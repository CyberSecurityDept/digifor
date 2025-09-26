/**
 * Auto Refresh Token Implementation
 * Contoh implementasi frontend untuk auto refresh token
 */

class AutoRefreshTokenManager {
    constructor(baseURL = 'http://localhost:8000') {
        this.baseURL = baseURL;
        this.accessToken = localStorage.getItem('access_token');
        this.refreshToken = localStorage.getItem('refresh_token');
        this.isRefreshing = false;
        this.failedQueue = [];
    }

    /**
     * Login dan dapatkan token pair
     */
    async login(username, password) {
        try {
            const response = await fetch(`${this.baseURL}/api/v1/auth/token`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ username, password })
            });

            if (!response.ok) {
                throw new Error(`Login failed: ${response.status}`);
            }

            const data = await response.json();
            
            if (data.status === 200) {
                this.accessToken = data.data.access_token;
                this.refreshToken = data.data.refresh_token;
                
                localStorage.setItem('access_token', this.accessToken);
                localStorage.setItem('refresh_token', this.refreshToken);
                
                console.log('✅ Login successful, tokens saved');
                return data;
            } else {
                throw new Error(data.message || 'Login failed');
            }
        } catch (error) {
            console.error('❌ Login error:', error);
            throw error;
        }
    }

    /**
     * Manual refresh token
     */
    async refreshTokens() {
        if (!this.refreshToken) {
            throw new Error('No refresh token available');
        }

        try {
            const response = await fetch(`${this.baseURL}/api/v1/auth/auto-refresh`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ refresh_token: this.refreshToken })
            });

            if (!response.ok) {
                throw new Error(`Refresh failed: ${response.status}`);
            }

            const data = await response.json();
            
            if (data.status === 200) {
                this.accessToken = data.data.access_token;
                this.refreshToken = data.data.refresh_token;
                
                localStorage.setItem('access_token', this.accessToken);
                localStorage.setItem('refresh_token', this.refreshToken);
                
                console.log('✅ Tokens refreshed successfully');
                return data;
            } else {
                throw new Error(data.message || 'Token refresh failed');
            }
        } catch (error) {
            console.error('❌ Token refresh error:', error);
            // Clear invalid tokens
            this.logout();
            throw error;
        }
    }

    /**
     * Check token status
     */
    async checkTokenStatus() {
        if (!this.accessToken) {
            return { valid: false, reason: 'no_token' };
        }

        try {
            const response = await fetch(`${this.baseURL}/api/v1/auth/token-status`, {
                headers: {
                    'Authorization': `Bearer ${this.accessToken}`
                }
            });

            if (!response.ok) {
                return { valid: false, reason: 'invalid_token' };
            }

            const data = await response.json();
            return data.data;
        } catch (error) {
            console.error('❌ Token status check error:', error);
            return { valid: false, reason: 'check_failed' };
        }
    }

    /**
     * Make authenticated request dengan auto refresh
     */
    async request(url, options = {}) {
        // Add authentication headers
        const headers = {
            'Authorization': `Bearer ${this.accessToken}`,
            'X-Refresh-Token': this.refreshToken,
            'Content-Type': 'application/json',
            ...options.headers
        };

        try {
            const response = await fetch(url, {
                ...options,
                headers
            });

            // Check jika token di-refresh otomatis
            if (response.headers.get('X-Token-Refreshed') === 'true') {
                const newAccessToken = response.headers.get('X-New-Access-Token');
                const newRefreshToken = response.headers.get('X-New-Refresh-Token');
                
                if (newAccessToken && newRefreshToken) {
                    this.accessToken = newAccessToken;
                    this.refreshToken = newRefreshToken;
                    
                    localStorage.setItem('access_token', this.accessToken);
                    localStorage.setItem('refresh_token', this.refreshToken);
                    
                    console.log('🔄 Tokens refreshed automatically by server');
                }
            }

            return response;
        } catch (error) {
            console.error('❌ Request error:', error);
            throw error;
        }
    }

    /**
     * Get user profile
     */
    async getUserProfile() {
        try {
            const response = await this.request(`${this.baseURL}/api/v1/auth/me`);
            
            if (!response.ok) {
                throw new Error(`Profile fetch failed: ${response.status}`);
            }

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('❌ Get profile error:', error);
            throw error;
        }
    }

    /**
     * Logout dan clear tokens
     */
    async logout() {
        try {
            if (this.accessToken) {
                await this.request(`${this.baseURL}/api/v1/auth/logout`, {
                    method: 'POST'
                });
            }
        } catch (error) {
            console.warn('⚠️ Logout request failed:', error);
        } finally {
            this.accessToken = null;
            this.refreshToken = null;
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            console.log('✅ Logged out successfully');
        }
    }

    /**
     * Check if user is authenticated
     */
    isAuthenticated() {
        return !!(this.accessToken && this.refreshToken);
    }

    /**
     * Get token info
     */
    getTokenInfo() {
        return {
            hasAccessToken: !!this.accessToken,
            hasRefreshToken: !!this.refreshToken,
            isAuthenticated: this.isAuthenticated()
        };
    }
}

// Usage Examples
async function exampleUsage() {
    const tokenManager = new AutoRefreshTokenManager();

    try {
        // 1. Login
        console.log('🔐 Logging in...');
        await tokenManager.login('admin', 'password');
        
        // 2. Check token status
        console.log('📊 Checking token status...');
        const status = await tokenManager.checkTokenStatus();
        console.log('Token status:', status);
        
        // 3. Get user profile
        console.log('👤 Getting user profile...');
        const profile = await tokenManager.getUserProfile();
        console.log('User profile:', profile);
        
        // 4. Make other authenticated requests
        console.log('📋 Making authenticated requests...');
        const response = await tokenManager.request('/api/v1/cases');
        console.log('Cases response:', response.status);
        
        // 5. Manual refresh (optional)
        console.log('🔄 Manual token refresh...');
        await tokenManager.refreshTokens();
        
        // 6. Check token info
        console.log('ℹ️ Token info:', tokenManager.getTokenInfo());
        
    } catch (error) {
        console.error('❌ Example error:', error);
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AutoRefreshTokenManager;
}

// Auto-run example if in browser
if (typeof window !== 'undefined') {
    console.log('🚀 Auto Refresh Token Manager loaded!');
    console.log('📖 Usage: const tokenManager = new AutoRefreshTokenManager();');
    console.log('🔐 Login: await tokenManager.login(username, password);');
    console.log('📡 Request: await tokenManager.request(url, options);');
}
