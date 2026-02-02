import axios, { AxiosError } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8080';
export const PROJECT_ID = import.meta.env.VITE_PROJECT_ID || 'test-project';

// Function to get current project from localStorage
export const getCurrentProject = () => {
  return localStorage.getItem('gcp-stimulator-project') || 'demo-project';
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
    // console.log(`[${config.method?.toUpperCase()}] ${config.url}`);
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
