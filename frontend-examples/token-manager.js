/**
 * Automatic Token Refresh Manager
 * Handles automatic token refresh when access token expires
 */

class TokenManager {
    constructor() {
        this.accessToken = localStorage.getItem('access_token');
        this.refreshToken = localStorage.getItem('refresh_token');
        this.refreshPromise = null;
        this.baseURL = 'http://localhost:8000/api/v1/auth';
    }

    /**
     * Set tokens in localStorage and memory
     */
    setTokens(accessToken, refreshToken) {
        this.accessToken = accessToken;
        this.refreshToken = refreshToken;
        localStorage.setItem('access_token', accessToken);
        localStorage.setItem('refresh_token', refreshToken);
    }

    /**
     * Clear all tokens
     */
    clearTokens() {
        this.accessToken = null;
        this.refreshToken = null;
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
    }

    /**
     * Check if access token is expired
     */
    isAccessTokenExpired() {
        if (!this.accessToken) return true;
        
        try {
            const payload = JSON.parse(atob(this.accessToken.split('.')[1]));
            const now = Math.floor(Date.now() / 1000);
            return payload.exp < now;
        } catch (error) {
            return true;
        }
    }

    /**
     * Check if refresh token is expired
     */
    isRefreshTokenExpired() {
        if (!this.refreshToken) return true;
        
        try {
            const payload = JSON.parse(atob(this.refreshToken.split('.')[1]));
            const now = Math.floor(Date.now() / 1000);
            return payload.exp < now;
        } catch (error) {
            return true;
        }
    }

    /**
     * Refresh access token using refresh token
     */
    async refreshAccessToken() {
        // Prevent multiple simultaneous refresh calls
        if (this.refreshPromise) {
            return this.refreshPromise;
        }

        if (!this.refreshToken || this.isRefreshTokenExpired()) {
            this.clearTokens();
            throw new Error('Refresh token expired or not available');
        }

        this.refreshPromise = this._performRefresh();

        try {
            const result = await this.refreshPromise;
            return result;
        } finally {
            this.refreshPromise = null;
        }
    }

    /**
     * Perform the actual refresh API call
     */
    async _performRefresh() {
        try {
            const response = await fetch(`${this.baseURL}/refresh`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    refresh_token: this.refreshToken
                })
            });

            if (!response.ok) {
                throw new Error(`Refresh failed: ${response.status}`);
            }

            const data = await response.json();
            
            if (data.status === 200) {
                this.setTokens(data.data.access_token, data.data.refresh_token);
                return data.data;
            } else {
                throw new Error(data.message || 'Refresh failed');
            }
        } catch (error) {
            this.clearTokens();
            throw error;
        }
    }

    /**
     * Get valid access token (refresh if needed)
     */
    async getValidAccessToken() {
        if (!this.accessToken || this.isAccessTokenExpired()) {
            if (this.isRefreshTokenExpired()) {
                throw new Error('Both tokens expired. Please login again.');
            }
            
            await this.refreshAccessToken();
        }
        
        return this.accessToken;
    }

    /**
     * Make authenticated API request with automatic token refresh
     */
    async authenticatedRequest(url, options = {}) {
        try {
            const token = await this.getValidAccessToken();
            
            const requestOptions = {
                ...options,
                headers: {
                    ...options.headers,
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                }
            };

            const response = await fetch(url, requestOptions);
            
            // If still unauthorized after refresh, clear tokens
            if (response.status === 401) {
                this.clearTokens();
                throw new Error('Authentication failed. Please login again.');
            }

            return response;
        } catch (error) {
            if (error.message.includes('Both tokens expired')) {
                this.clearTokens();
                // Redirect to login page
                window.location.href = '/login';
            }
            throw error;
        }
    }

    /**
     * Login and store tokens
     */
    async login(username, password) {
        try {
            const response = await fetch(`${this.baseURL}/token`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ username, password })
            });

            const data = await response.json();
            
            if (data.status === 200) {
                this.setTokens(data.data.access_token, data.data.refresh_token);
                return data;
            } else {
                throw new Error(data.message || 'Login failed');
            }
        } catch (error) {
            throw error;
        }
    }

    /**
     * Logout and clear tokens
     */
    async logout() {
        try {
            if (this.accessToken) {
                await fetch(`${this.baseURL}/logout`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${this.accessToken}`,
                    }
                });
            }
        } catch (error) {
            console.warn('Logout API call failed:', error);
        } finally {
            this.clearTokens();
        }
    }
}

// Global instance
window.tokenManager = new TokenManager();

// Example usage:
/*
// Login
await tokenManager.login('admin', 'admin123');

// Make authenticated request (automatic refresh)
const response = await tokenManager.authenticatedRequest('/api/v1/auth/me');
const userData = await response.json();

// Manual refresh if needed
await tokenManager.refreshAccessToken();

// Logout
await tokenManager.logout();
*/
