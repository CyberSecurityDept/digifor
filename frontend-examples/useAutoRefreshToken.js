/**
 * React Hook untuk Auto Refresh Token
 * Custom hook untuk menangani auto refresh token di React/Next.js
 */

import { useState, useEffect, useCallback, useRef } from 'react';

const useAutoRefreshToken = (baseURL = 'http://localhost:8000') => {
    const [accessToken, setAccessToken] = useState(null);
    const [refreshToken, setRefreshToken] = useState(null);
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    
    const isRefreshing = useRef(false);
    const failedQueue = useRef([]);

    // Initialize tokens from localStorage
    useEffect(() => {
        const storedAccessToken = localStorage.getItem('access_token');
        const storedRefreshToken = localStorage.getItem('refresh_token');
        
        if (storedAccessToken && storedRefreshToken) {
            setAccessToken(storedAccessToken);
            setRefreshToken(storedRefreshToken);
            setIsAuthenticated(true);
        }
    }, []);

    // Save tokens to localStorage when they change
    useEffect(() => {
        if (accessToken && refreshToken) {
            localStorage.setItem('access_token', accessToken);
            localStorage.setItem('refresh_token', refreshToken);
        } else {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
        }
    }, [accessToken, refreshToken]);

    // Login function
    const login = useCallback(async (username, password) => {
        setIsLoading(true);
        setError(null);

        try {
            const response = await fetch(`${baseURL}/api/v1/auth/token`, {
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
                setAccessToken(data.data.access_token);
                setRefreshToken(data.data.refresh_token);
                setIsAuthenticated(true);
                return data;
            } else {
                throw new Error(data.message || 'Login failed');
            }
        } catch (err) {
            setError(err.message);
            throw err;
        } finally {
            setIsLoading(false);
        }
    }, [baseURL]);

    // Refresh tokens function
    const refreshTokens = useCallback(async () => {
        if (!refreshToken || isRefreshing.current) {
            return false;
        }

        isRefreshing.current = true;

        try {
            const response = await fetch(`${baseURL}/api/v1/auth/auto-refresh`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ refresh_token: refreshToken })
            });

            if (!response.ok) {
                throw new Error(`Refresh failed: ${response.status}`);
            }

            const data = await response.json();
            
            if (data.status === 200) {
                setAccessToken(data.data.access_token);
                setRefreshToken(data.data.refresh_token);
                
                // Process failed queue
                failedQueue.current.forEach(({ resolve }) => resolve());
                failedQueue.current = [];
                
                return true;
            } else {
                throw new Error(data.message || 'Token refresh failed');
            }
        } catch (err) {
            // Process failed queue with error
            failedQueue.current.forEach(({ reject }) => reject(err));
            failedQueue.current = [];
            
            // Clear tokens on refresh failure
            logout();
            throw err;
        } finally {
            isRefreshing.current = false;
        }
    }, [refreshToken, baseURL]);

    // Logout function
    const logout = useCallback(async () => {
        try {
            if (accessToken) {
                await fetch(`${baseURL}/api/v1/auth/logout`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${accessToken}`
                    }
                });
            }
        } catch (err) {
            console.warn('Logout request failed:', err);
        } finally {
            setAccessToken(null);
            setRefreshToken(null);
            setIsAuthenticated(false);
            setError(null);
        }
    }, [accessToken, baseURL]);

    // Authenticated request function
    const request = useCallback(async (url, options = {}) => {
        if (!accessToken) {
            throw new Error('No access token available');
        }

        const headers = {
            'Authorization': `Bearer ${accessToken}`,
            'X-Refresh-Token': refreshToken,
            'Content-Type': 'application/json',
            ...options.headers
        };

        try {
            const response = await fetch(url, {
                ...options,
                headers
            });

            // Check if token was refreshed automatically
            if (response.headers.get('X-Token-Refreshed') === 'true') {
                const newAccessToken = response.headers.get('X-New-Access-Token');
                const newRefreshToken = response.headers.get('X-New-Refresh-Token');
                
                if (newAccessToken && newRefreshToken) {
                    setAccessToken(newAccessToken);
                    setRefreshToken(newRefreshToken);
                    console.log('🔄 Tokens refreshed automatically by server');
                }
            }

            return response;
        } catch (err) {
            // If request fails with 401, try to refresh token
            if (err.response?.status === 401 && refreshToken) {
                if (isRefreshing.current) {
                    // If already refreshing, queue this request
                    return new Promise((resolve, reject) => {
                        failedQueue.current.push({ resolve, reject });
                    }).then(() => request(url, options));
                } else {
                    // Try to refresh token
                    try {
                        await refreshTokens();
                        // Retry original request
                        return request(url, options);
                    } catch (refreshErr) {
                        throw refreshErr;
                    }
                }
            }
            throw err;
        }
    }, [accessToken, refreshToken, refreshTokens]);

    // Get user profile
    const getUserProfile = useCallback(async () => {
        const response = await request(`${baseURL}/api/v1/auth/me`);
        
        if (!response.ok) {
            throw new Error(`Profile fetch failed: ${response.status}`);
        }

        return response.json();
    }, [request, baseURL]);

    // Check token status
    const checkTokenStatus = useCallback(async () => {
        if (!accessToken) {
            return { valid: false, reason: 'no_token' };
        }

        try {
            const response = await request(`${baseURL}/api/v1/auth/token-status`);
            
            if (!response.ok) {
                return { valid: false, reason: 'invalid_token' };
            }

            const data = await response.json();
            return data.data;
        } catch (err) {
            return { valid: false, reason: 'check_failed' };
        }
    }, [accessToken, request, baseURL]);

    return {
        // State
        accessToken,
        refreshToken,
        isAuthenticated,
        isLoading,
        error,
        
        // Actions
        login,
        logout,
        refreshTokens,
        request,
        getUserProfile,
        checkTokenStatus,
        
        // Utilities
        clearError: () => setError(null)
    };
};

export default useAutoRefreshToken;

// Example usage in React component
export const ExampleComponent = () => {
    const {
        isAuthenticated,
        isLoading,
        error,
        login,
        logout,
        request,
        getUserProfile,
        checkTokenStatus
    } = useAutoRefreshToken();

    const handleLogin = async () => {
        try {
            await login('admin', 'password');
            console.log('Login successful!');
        } catch (err) {
            console.error('Login failed:', err);
        }
    };

    const handleGetProfile = async () => {
        try {
            const profile = await getUserProfile();
            console.log('User profile:', profile);
        } catch (err) {
            console.error('Get profile failed:', err);
        }
    };

    const handleCheckStatus = async () => {
        try {
            const status = await checkTokenStatus();
            console.log('Token status:', status);
        } catch (err) {
            console.error('Check status failed:', err);
        }
    };

    const handleLogout = async () => {
        try {
            await logout();
            console.log('Logout successful!');
        } catch (err) {
            console.error('Logout failed:', err);
        }
    };

    if (isLoading) {
        return <div>Loading...</div>;
    }

    return (
        <div>
            <h1>Auto Refresh Token Example</h1>
            
            {error && (
                <div style={{ color: 'red' }}>
                    Error: {error}
                </div>
            )}
            
            {!isAuthenticated ? (
                <div>
                    <h2>Login</h2>
                    <button onClick={handleLogin}>
                        Login as Admin
                    </button>
                </div>
            ) : (
                <div>
                    <h2>Authenticated</h2>
                    <p>You are logged in!</p>
                    
                    <button onClick={handleGetProfile}>
                        Get Profile
                    </button>
                    
                    <button onClick={handleCheckStatus}>
                        Check Token Status
                    </button>
                    
                    <button onClick={handleLogout}>
                        Logout
                    </button>
                </div>
            )}
        </div>
    );
};
