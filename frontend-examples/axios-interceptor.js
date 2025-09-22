/**
 * Axios Interceptor for Automatic Token Refresh
 * Handles automatic token refresh on 401 responses
 */

import axios from 'axios';

// Token Manager (import from token-manager.js)
const tokenManager = window.tokenManager || new TokenManager();

// Create axios instance
const apiClient = axios.create({
    baseURL: 'http://localhost:8000/api/v1',
    timeout: 10000,
});

// Request interceptor - Add token to requests
apiClient.interceptors.request.use(
    (config) => {
        const token = tokenManager.accessToken;
        if (token && !tokenManager.isAccessTokenExpired()) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response interceptor - Handle token refresh on 401
apiClient.interceptors.response.use(
    (response) => {
        return response;
    },
    async (error) => {
        const originalRequest = error.config;

        // If error is 401 and we haven't already tried to refresh
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;

            try {
                // Try to refresh token
                await tokenManager.refreshAccessToken();
                
                // Retry original request with new token
                originalRequest.headers.Authorization = `Bearer ${tokenManager.accessToken}`;
                return apiClient(originalRequest);
            } catch (refreshError) {
                // Refresh failed, redirect to login
                tokenManager.clearTokens();
                window.location.href = '/login';
                return Promise.reject(refreshError);
            }
        }

        return Promise.reject(error);
    }
);

// API methods with automatic token refresh
export const authAPI = {
    // Login
    login: async (credentials) => {
        const response = await axios.post('/auth/token', credentials);
        const data = response.data;
        
        if (data.status === 200) {
            tokenManager.setTokens(data.data.access_token, data.data.refresh_token);
        }
        
        return data;
    },

    // Logout
    logout: async () => {
        try {
            await apiClient.post('/auth/logout');
        } catch (error) {
            console.warn('Logout API call failed:', error);
        } finally {
            tokenManager.clearTokens();
        }
    },

    // Get user profile
    getProfile: () => apiClient.get('/auth/me'),

    // Refresh token manually
    refreshToken: () => tokenManager.refreshAccessToken(),

    // Get valid access token
    getValidToken: () => tokenManager.getValidAccessToken(),
};

// Case management API
export const caseAPI = {
    getCases: () => apiClient.get('/cases'),
    getCase: (id) => apiClient.get(`/cases/${id}`),
    createCase: (caseData) => apiClient.post('/cases', caseData),
    updateCase: (id, caseData) => apiClient.put(`/cases/${id}`, caseData),
    deleteCase: (id) => apiClient.delete(`/cases/${id}`),
};

// Evidence management API
export const evidenceAPI = {
    getEvidence: (caseId) => apiClient.get(`/evidence?case_id=${caseId}`),
    uploadEvidence: (formData) => apiClient.post('/evidence/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    }),
    getEvidenceItem: (id) => apiClient.get(`/evidence/${id}`),
    updateEvidence: (id, data) => apiClient.put(`/evidence/${id}`, data),
    deleteEvidence: (id) => apiClient.delete(`/evidence/${id}`),
};

// Analysis API
export const analysisAPI = {
    getAnalyses: (caseId) => apiClient.get(`/analyses?case_id=${caseId}`),
    startAnalysis: (analysisData) => apiClient.post('/analyses', analysisData),
    getAnalysis: (id) => apiClient.get(`/analyses/${id}`),
    getAnalysisResults: (id) => apiClient.get(`/analyses/${id}/results`),
};

export default apiClient;

// Example usage:
/*
import { authAPI, caseAPI } from './axios-interceptor';

// Login (tokens automatically stored)
await authAPI.login({ username: 'admin', password: 'admin123' });

// Make API calls (automatic token refresh on 401)
const cases = await caseAPI.getCases();
const profile = await authAPI.getProfile();

// Logout (tokens automatically cleared)
await authAPI.logout();
*/
