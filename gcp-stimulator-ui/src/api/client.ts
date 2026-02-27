import axios, { AxiosError } from 'axios';

const browserHost =
  typeof window !== 'undefined' && window.location?.hostname
    ? window.location.hostname
    : '127.0.0.1';

const isLocalHost = (host: string) => host === 'localhost' || host === '127.0.0.1';

const resolveApiBaseUrl = () => {
  const configured = import.meta.env.VITE_API_BASE_URL?.trim();
  if (configured) {
    try {
      const parsed = new URL(configured);
      if (!isLocalHost(browserHost) && isLocalHost(parsed.hostname)) {
        parsed.hostname = browserHost;
      }
      return parsed.toString().replace(/\/$/, '');
    } catch {
      return configured.replace(/\/$/, '');
    }
  }

  // Default to relative proxy path for both local dev and containerized deployments.
  return '/api';
};

const API_BASE_URL = resolveApiBaseUrl();
export const PROJECT_ID = import.meta.env.VITE_PROJECT_ID || 'demo-project';

// Function to get current project from localStorage
export const getCurrentProject = () => {
  return localStorage.getItem('gcp-stimulator-project') || PROJECT_ID;
};

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Normalize to relative paths so baseURL prefixes (e.g. /api) are honored.
    if (typeof config.url === 'string' && config.url.startsWith('/')) {
      config.url = config.url.slice(1);
    }
    console.log(`[${config.method?.toUpperCase()}] ${API_BASE_URL}/${config.url} (baseURL: ${config.baseURL})`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ error: { message: string } }>) => {
    const { config } = error;
    const method = config?.method?.toUpperCase();
    const url = config?.url;

    const errorMessage = 
      error.response?.data?.error?.message || 
      error.message || 
      'An unexpected error occurred';
    
    console.error(`[${method}] ${url} - API Error:`, errorMessage, error.response);
    
    return Promise.reject(error);
  }
);

export default apiClient;
