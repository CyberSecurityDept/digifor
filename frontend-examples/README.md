# 🔄 Automatic Token Refresh Implementation

Implementasi automatic token refresh untuk berbagai frontend framework.

## 📋 Overview

Sistem ini menyediakan:
- ✅ **Automatic Token Refresh** - Refresh token otomatis sebelum expired
- ✅ **Error Handling** - Graceful handling untuk expired tokens
- ✅ **Multiple Framework Support** - React, Vue.js, Vanilla JS
- ✅ **Security** - Token rotation dan secure storage
- ✅ **User Experience** - Seamless authentication tanpa interupsi

## 🚀 Quick Start

### 1. Include Token Manager
```html
<script src="token-manager.js"></script>
```

### 2. Basic Usage
```javascript
// Login
await tokenManager.login('admin', 'admin123');

// Make authenticated requests (automatic refresh)
const response = await tokenManager.authenticatedRequest('/api/v1/auth/me');
const userData = await response.json();
```

## 📚 Framework Implementations

### 🔷 Vanilla JavaScript
**File:** `token-manager.js`

```javascript
// Initialize
const tokenManager = new TokenManager();

// Login
await tokenManager.login('username', 'password');

// Authenticated requests
const response = await tokenManager.authenticatedRequest('/api/v1/cases');
```

### ⚛️ React
**File:** `useAuth.js`

```jsx
import { useAuth } from './useAuth';

function App() {
    const { user, loading, login, logout, isAuthenticated } = useAuth();

    const handleLogin = async (credentials) => {
        try {
            await login(credentials.username, credentials.password);
        } catch (error) {
            console.error('Login failed:', error);
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
```

### 🟢 Vue.js
**File:** `vue-auth-plugin.js`

```javascript
// main.js
import { createApp } from 'vue';
import AuthPlugin from './vue-auth-plugin.js';

const app = createApp(App);
app.use(AuthPlugin);
app.mount('#app');
```

```vue
<!-- Component.vue -->
<template>
  <div>
    <div v-if="auth.loading">Loading...</div>
    <div v-else-if="isAuthenticated">
      <h1>Welcome, {{ auth.user?.full_name }}!</h1>
      <button @click="logout">Logout</button>
    </div>
    <div v-else>
      <LoginForm @login="login" />
    </div>
  </div>
</template>

<script>
import { useAuth } from './vue-auth-plugin.js';

export default {
  setup() {
    const { auth, isAuthenticated, login, logout } = useAuth();
    return { auth, isAuthenticated, login, logout };
  }
};
</script>
```

### 🔷 Axios Interceptor
**File:** `axios-interceptor.js`

```javascript
import { authAPI, caseAPI } from './axios-interceptor';

// Login
await authAPI.login({ username: 'admin', password: 'admin123' });

// API calls with automatic refresh
const cases = await caseAPI.getCases();
const profile = await authAPI.getProfile();
```

## ⚙️ Configuration

### Token Expiration Settings
```javascript
// Access token: 30 minutes
// Refresh token: 7 days
// Auto-refresh: 5 minutes before expiry
```

### Custom Base URL
```javascript
const tokenManager = new TokenManager();
tokenManager.baseURL = 'https://your-api.com/api/v1/auth';
```

## 🛡️ Security Features

### 1. Token Rotation
- Refresh token di-rotate setiap kali digunakan
- Old refresh token di-revoke untuk keamanan

### 2. Automatic Cleanup
- Expired tokens otomatis dibersihkan
- LocalStorage dibersihkan saat logout

### 3. Error Handling
- Graceful fallback untuk expired tokens
- Automatic redirect ke login page

## 📊 API Reference

### TokenManager Methods

| Method | Description | Parameters |
|--------|-------------|------------|
| `login(username, password)` | Login dan simpan tokens | `username: string, password: string` |
| `logout()` | Logout dan clear tokens | - |
| `getValidAccessToken()` | Get valid access token (refresh if needed) | - |
| `refreshAccessToken()` | Manual refresh token | - |
| `authenticatedRequest(url, options)` | Make authenticated request | `url: string, options: object` |

### React Hook Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `login(credentials)` | Login user | `Promise<AuthResult>` |
| `logout()` | Logout user | `Promise<void>` |
| `refreshToken()` | Manual refresh | `Promise<void>` |
| `fetchUserProfile()` | Get user profile | `Promise<void>` |

## 🔧 Advanced Usage

### Custom Error Handling
```javascript
tokenManager.authenticatedRequest('/api/v1/cases')
    .then(response => response.json())
    .then(data => console.log(data))
    .catch(error => {
        if (error.message.includes('Both tokens expired')) {
            // Redirect to login
            window.location.href = '/login';
        } else {
            // Handle other errors
            console.error('API Error:', error);
        }
    });
```

### Manual Token Refresh
```javascript
// Check if token needs refresh
if (tokenManager.isAccessTokenExpired()) {
    await tokenManager.refreshAccessToken();
}
```

### Custom Storage
```javascript
class CustomTokenManager extends TokenManager {
    setTokens(accessToken, refreshToken) {
        // Custom storage logic
        sessionStorage.setItem('access_token', accessToken);
        sessionStorage.setItem('refresh_token', refreshToken);
    }
}
```

## 🐛 Troubleshooting

### Common Issues

1. **"Refresh token not found"**
   - Solution: Login ulang untuk mendapatkan refresh token baru

2. **"Both tokens expired"**
   - Solution: User harus login ulang

3. **CORS Issues**
   - Solution: Pastikan backend mengizinkan origin frontend

4. **Token not refreshing automatically**
   - Solution: Pastikan interval check berjalan (60 detik)

### Debug Mode
```javascript
// Enable debug logging
tokenManager.debug = true;
```

## 📈 Performance

- **Memory Usage:** Minimal (hanya menyimpan 2 tokens)
- **Network Calls:** Hanya saat refresh diperlukan
- **CPU Usage:** Minimal (check setiap 60 detik)
- **Storage:** 2 items di localStorage

## 🔄 Migration Guide

### From Manual Token Management
```javascript
// Before
const token = localStorage.getItem('token');
if (isTokenExpired(token)) {
    // Manual refresh logic
}

// After
const token = await tokenManager.getValidAccessToken();
// Automatic refresh handled
```

## 📝 Best Practices

1. **Always use `authenticatedRequest()`** untuk API calls
2. **Handle errors gracefully** dengan try-catch
3. **Clear tokens on logout** untuk keamanan
4. **Use HTTPS** untuk production
5. **Implement proper loading states** untuk UX

## 🚀 Production Deployment

1. **Update baseURL** untuk production API
2. **Configure CORS** di backend
3. **Set up proper error monitoring**
4. **Test token refresh flow** thoroughly
5. **Implement proper logging**

---

**Note:** Pastikan backend API sudah mengimplementasikan refresh token endpoint sesuai dengan dokumentasi API.
