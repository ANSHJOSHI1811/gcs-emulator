import axios from 'axios';
import { toast } from 'react-toastify';

const apiClient = axios.create({
  baseURL: (import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:8080',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    const projectId = localStorage.getItem('selectedProject');
    if (projectId && config.params) {
      config.params.project = projectId;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.error?.message || error.message || 'An error occurred';
    
    if (error.response?.status === 401) {
      toast.error('Unauthorized. Please check your credentials.');
    } else if (error.response?.status === 404) {
      toast.error('Resource not found.');
    } else if (error.response?.status >= 500) {
      toast.error('Server error. Please try again later.');
    } else if (!error.config?.skipErrorToast) {
      toast.error(message);
    }
    
    return Promise.reject(error);
  }
);

export default apiClient;
