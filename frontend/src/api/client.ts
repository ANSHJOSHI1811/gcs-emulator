import axios, { AxiosError } from 'axios';
import toast from 'react-hot-toast';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8080';

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
    const errorMessage = 
      error.response?.data?.error?.message || 
      error.message || 
      'An unexpected error occurred';
    
    console.error('API Error:', errorMessage);
    
    return Promise.reject(error);
  }
);

export default apiClient;
