# Auto Refresh Token Guide

## Overview

Sistem auto refresh token memungkinkan aplikasi untuk secara otomatis memperbarui access token sebelum expired, memberikan pengalaman pengguna yang seamless tanpa interupsi login.

## Features

### 1. Automatic Token Refresh
- **Threshold**: Token akan di-refresh 5 menit sebelum expired
- **Seamless**: User tidak perlu login ulang
- **Security**: Token rotation untuk keamanan maksimal

### 2. Token Rotation
- Refresh token lama di-revoke setelah digunakan
- Refresh token baru diberikan setiap refresh
- Mencegah token reuse attacks

### 3. Multiple Storage Options
- **Header**: `X-Refresh-Token`
- **Cookie**: `refresh_token`
- **Request Body**: Untuk POST requests

## API Endpoints

### 1. Login (Mendapatkan Token Pair)
```http
POST /api/v1/auth/token
Content-Type: application/json

{
    "username": "admin",
    "password": "password"
}
```

**Response:**
```json
{
    "status": 200,
    "message": "Login Successfully",
    "data": {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer",
        "expires_in": 1800
    }
}
```

### 2. Manual Refresh Token
```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### 3. Auto Refresh Token
```http
POST /api/v1/auth/auto-refresh
Content-Type: application/json

{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### 4. Token Status Check
```http
GET /api/v1/auth/token-status
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```json
{
    "status": 200,
    "message": "Token status retrieved successfully",
    "data": {
        "valid": true,
        "needs_refresh": false,
        "time_until_expiry": 1200,
        "expires_at": "2024-01-01T12:00:00Z",
        "username": "admin",
        "role": "admin"
    }
}
```

## Frontend Implementation

### 1. JavaScript/TypeScript Example

```javascript
class TokenManager {
    constructor() {
        this.accessToken = localStorage.getItem('access_token');
        this.refreshToken = localStorage.getItem('refresh_token');
        this.baseURL = 'http://localhost:8000';
    }

    // Login dan simpan tokens
    async login(username, password) {
        const response = await fetch(`${this.baseURL}/api/v1/auth/token`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password })
        });

        if (response.ok) {
            const data = await response.json();
            this.accessToken = data.data.access_token;
            this.refreshToken = data.data.refresh_token;
            
            localStorage.setItem('access_token', this.accessToken);
            localStorage.setItem('refresh_token', this.refreshToken);
            
            return data;
        }
        throw new Error('Login failed');
    }

    // Request dengan auto refresh
    async request(url, options = {}) {
        const headers = {
            'Authorization': `Bearer ${this.accessToken}`,
            'X-Refresh-Token': this.refreshToken,
            ...options.headers
        };

        const response = await fetch(url, {
            ...options,
            headers
        });

        // Check jika token di-refresh
        if (response.headers.get('X-Token-Refreshed') === 'true') {
            const newAccessToken = response.headers.get('X-New-Access-Token');
            const newRefreshToken = response.headers.get('X-New-Refresh-Token');
            
            if (newAccessToken && newRefreshToken) {
                this.accessToken = newAccessToken;
                this.refreshToken = newRefreshToken;
                
                localStorage.setItem('access_token', this.accessToken);
                localStorage.setItem('refresh_token', this.refreshToken);
                
                console.log('Tokens refreshed automatically');
            }
        }

        return response;
    }

    // Manual refresh
    async refreshTokens() {
        if (!this.refreshToken) {
            throw new Error('No refresh token available');
        }

        const response = await fetch(`${this.baseURL}/api/v1/auth/auto-refresh`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ refresh_token: this.refreshToken })
        });

        if (response.ok) {
            const data = await response.json();
            this.accessToken = data.data.access_token;
            this.refreshToken = data.data.refresh_token;
            
            localStorage.setItem('access_token', this.accessToken);
            localStorage.setItem('refresh_token', this.refreshToken);
            
            return data;
        }
        throw new Error('Token refresh failed');
    }

    // Logout
    logout() {
        this.accessToken = null;
        this.refreshToken = null;
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
    }
}

// Usage
const tokenManager = new TokenManager();

// Login
await tokenManager.login('admin', 'password');

// Make authenticated requests
const response = await tokenManager.request('/api/v1/cases');
```

### 2. Axios Interceptor Example

```javascript
import axios from 'axios';

const api = axios.create({
    baseURL: 'http://localhost:8000',
});

// Request interceptor
api.interceptors.request.use(
    (config) => {
        const accessToken = localStorage.getItem('access_token');
        const refreshToken = localStorage.getItem('refresh_token');
        
        if (accessToken) {
            config.headers.Authorization = `Bearer ${accessToken}`;
        }
        
        if (refreshToken) {
            config.headers['X-Refresh-Token'] = refreshToken;
        }
        
        return config;
    },
    (error) => Promise.reject(error)
);

// Response interceptor
api.interceptors.response.use(
    (response) => {
        // Check jika token di-refresh
        if (response.headers['x-token-refreshed'] === 'true') {
            const newAccessToken = response.headers['x-new-access-token'];
            const newRefreshToken = response.headers['x-new-refresh-token'];
            
            if (newAccessToken && newRefreshToken) {
                localStorage.setItem('access_token', newAccessToken);
                localStorage.setItem('refresh_token', newRefreshToken);
                console.log('Tokens refreshed automatically');
            }
        }
        
        return response;
    },
    async (error) => {
        if (error.response?.status === 401) {
            // Token expired, try to refresh
            const refreshToken = localStorage.getItem('refresh_token');
            
            if (refreshToken) {
                try {
                    const response = await axios.post('/api/v1/auth/auto-refresh', {
                        refresh_token: refreshToken
                    });
                    
                    const { access_token, refresh_token } = response.data.data;
                    localStorage.setItem('access_token', access_token);
                    localStorage.setItem('refresh_token', refresh_token);
                    
                    // Retry original request
                    error.config.headers.Authorization = `Bearer ${access_token}`;
                    return axios.request(error.config);
                } catch (refreshError) {
                    // Refresh failed, redirect to login
                    localStorage.removeItem('access_token');
                    localStorage.removeItem('refresh_token');
                    window.location.href = '/login';
                }
            }
        }
        
        return Promise.reject(error);
    }
);
```

## Security Features

### 1. Token Rotation
- Setiap refresh token hanya bisa digunakan sekali
- Token lama di-revoke setelah digunakan
- Mencegah replay attacks

### 2. Automatic Cleanup
- Expired tokens di-cleanup otomatis
- Session management yang aman
- Memory efficient

### 3. Secure Storage
- Refresh token bisa disimpan di httpOnly cookies
- Header-based refresh token support
- Multiple storage options

## Configuration

### Environment Variables
```env
# Token expiration times (in minutes)
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Auto refresh threshold (in seconds)
AUTO_REFRESH_THRESHOLD=300
```

### Middleware Configuration
```python
# In main.py
app.add_middleware(
    AutoRefreshTokenMiddleware,
    auto_refresh_threshold=300  # 5 minutes before expiry
)
```

## Best Practices

### 1. Frontend
- Simpan refresh token di httpOnly cookie jika mungkin
- Implementasi retry logic untuk failed requests
- Handle token refresh errors gracefully
- Monitor token expiration times

### 2. Backend
- Gunakan token rotation untuk keamanan
- Implementasi rate limiting untuk refresh endpoints
- Log semua token refresh activities
- Monitor suspicious refresh patterns

### 3. Security
- Jangan log sensitive token data
- Implementasi proper CORS settings
- Gunakan HTTPS di production
- Monitor dan alert untuk unusual activities

## Troubleshooting

### Common Issues

1. **Token refresh failed**
   - Check refresh token validity
   - Verify user is still active
   - Check database connection

2. **Auto refresh not working**
   - Verify middleware is properly configured
   - Check token threshold settings
   - Ensure refresh token is available in request

3. **CORS issues**
   - Configure CORS to allow custom headers
   - Add `X-Refresh-Token` to allowed headers

### Debug Mode
```python
# Enable debug logging
import logging
logging.getLogger('app.middleware.auto_refresh').setLevel(logging.DEBUG)
```

## Monitoring

### Metrics to Track
- Token refresh success rate
- Average time between refreshes
- Failed refresh attempts
- User session durations

### Logs to Monitor
- Token refresh activities
- Failed authentication attempts
- Suspicious refresh patterns
- User login/logout events
