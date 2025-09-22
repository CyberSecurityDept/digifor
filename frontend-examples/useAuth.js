/**
 * React Hook for Authentication with Automatic Token Refresh
 * useAuth.js - React Hook implementation
 */

import { useState, useEffect, useCallback } from 'react';

// Token Manager (import from token-manager.js)
const tokenManager = window.tokenManager || new TokenManager();

export const useAuth = () => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Check if user is authenticated
    const isAuthenticated = useCallback(() => {
        return !!(tokenManager.accessToken && !tokenManager.isAccessTokenExpired());
    }, []);

    // Login function
    const login = useCallback(async (username, password) => {
        try {
            setLoading(true);
            setError(null);
            
            const result = await tokenManager.login(username, password);
            
            // Fetch user profile after login
            await fetchUserProfile();
            
            return result;
        } catch (err) {
            setError(err.message);
            throw err;
        } finally {
            setLoading(false);
        }
    }, []);

    // Logout function
    const logout = useCallback(async () => {
        try {
            setLoading(true);
            await tokenManager.logout();
        } catch (err) {
            console.warn('Logout error:', err);
        } finally {
            setUser(null);
            setLoading(false);
        }
    }, []);

    // Fetch user profile
    const fetchUserProfile = useCallback(async () => {
        try {
            const response = await tokenManager.authenticatedRequest('/api/v1/auth/me');
            const data = await response.json();
            
            if (data.status === 200) {
                setUser(data.data);
            } else {
                throw new Error(data.message || 'Failed to fetch user profile');
            }
        } catch (err) {
            setError(err.message);
            setUser(null);
            throw err;
        }
    }, []);

    // Refresh token function
    const refreshToken = useCallback(async () => {
        try {
            setLoading(true);
            await tokenManager.refreshAccessToken();
            await fetchUserProfile();
        } catch (err) {
            setError(err.message);
            setUser(null);
            throw err;
        } finally {
            setLoading(false);
        }
    }, [fetchUserProfile]);

    // Initialize auth state
    useEffect(() => {
        const initializeAuth = async () => {
            try {
                setLoading(true);
                
                if (isAuthenticated()) {
                    await fetchUserProfile();
                } else if (tokenManager.refreshToken && !tokenManager.isRefreshTokenExpired()) {
                    // Try to refresh token
                    await refreshToken();
                } else {
                    // No valid tokens
                    setUser(null);
                }
            } catch (err) {
                setError(err.message);
                setUser(null);
            } finally {
                setLoading(false);
            }
        };

        initializeAuth();
    }, [isAuthenticated, fetchUserProfile, refreshToken]);

    // Auto-refresh token before expiration
    useEffect(() => {
        if (!isAuthenticated() || !tokenManager.accessToken) return;

        const checkTokenExpiry = () => {
            try {
                const payload = JSON.parse(atob(tokenManager.accessToken.split('.')[1]));
                const now = Math.floor(Date.now() / 1000);
                const timeUntilExpiry = payload.exp - now;
                
                // Refresh token 5 minutes before expiry
                if (timeUntilExpiry < 300 && timeUntilExpiry > 0) {
                    refreshToken().catch(console.error);
                }
            } catch (error) {
                console.warn('Token expiry check failed:', error);
            }
        };

        // Check every minute
        const interval = setInterval(checkTokenExpiry, 60000);
        
        return () => clearInterval(interval);
    }, [isAuthenticated, refreshToken]);

    return {
        user,
        loading,
        error,
        isAuthenticated: isAuthenticated(),
        login,
        logout,
        refreshToken,
        fetchUserProfile
    };
};

// Higher-order component for protected routes
export const withAuth = (WrappedComponent) => {
    return function AuthenticatedComponent(props) {
        const { isAuthenticated, loading } = useAuth();

        if (loading) {
            return <div>Loading...</div>;
        }

        if (!isAuthenticated) {
            return <div>Please login to access this page</div>;
        }

        return <WrappedComponent {...props} />;
    };
};

// Example usage in React component:
/*
import { useAuth } from './useAuth';

function App() {
    const { user, loading, error, login, logout, isAuthenticated } = useAuth();

    const handleLogin = async (username, password) => {
        try {
            await login(username, password);
        } catch (err) {
            console.error('Login failed:', err);
        }
    };

    if (loading) return <div>Loading...</div>;

    return (
        <div>
            {isAuthenticated ? (
                <div>
                    <h1>Welcome, {user?.full_name}!</h1>
                    <button onClick={logout}>Logout</button>
                </div>
            ) : (
                <LoginForm onLogin={handleLogin} />
            )}
        </div>
    );
}
*/
