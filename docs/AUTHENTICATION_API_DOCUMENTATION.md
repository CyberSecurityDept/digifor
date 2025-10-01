# Authentication API Documentation

## Overview
This document provides comprehensive API documentation for the Authentication system endpoints. The endpoints are organized by functionality to match the authentication system structure.

## Base URL
```
/api/v1/auth
```

## Frontend API Endpoints Summary

### **Endpoints yang akan digunakan Frontend:**

#### **1. Login Management (Essential untuk Frontend)**
- ✅ `POST /token` - Login dengan username/password
- ✅ `POST /oauth2/token` - OAuth2 compatible login  
- ✅ `POST /refresh` - Refresh access token
- ✅ `POST /auto-refresh` - Auto refresh tokens

#### **2. User Profile Management (Essential untuk Frontend)**
- ✅ `GET /me` - Get current user profile

#### **3. User Registration Management (Essential untuk Frontend)**
- ✅ `POST /register` - Register new user

#### **4. Password Management (Essential untuk Frontend)**
- ✅ `POST /change-password` - Change user password
- ✅ `POST /request-password-reset` - Request password reset
- ✅ `POST /reset-password` - Reset password

#### **5. Session Management (Essential untuk Frontend)**
- ✅ `GET /token-status` - Check token status
- ✅ `GET /session` - Get session information
- ✅ `POST /logout-all` - Logout from all sessions

---

## Authentication Endpoints

### 1. Authentication - Login Management

#### **POST** `/token`
**Description:** Login with username/password and get access + refresh tokens

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response (200 - Success):**
```json
{
  "status": 200,
  "message": "Login Successfully",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 3600
  }
}
```

**Response (401 - Invalid Credentials):**
```json
{
  "status": 401,
  "messages": "Invalid username or password"
}
```

**Response (500 - Server Error):**
```json
{
  "status": 500,
  "message": "Login failed: [error details]"
}
```

---

#### **POST** `/token-form`
**Description:** Login with OAuth2 form data (for Swagger UI compatibility)

**Request Body (Form Data):**
```
username: string
password: string
```

**Response (200 - Success):**
```json
{
  "status": 200,
  "messages": "Login Successfully",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  }
}
```

**Response (401 - Invalid Credentials):**
```json
{
  "status": 401,
  "messages": "Invalid username or password"
}
```

---

#### **POST** `/oauth2/token`
**Description:** OAuth2 compatible login endpoint

**Request Body (Form Data):**
```
username: string
password: string
```

**Response (200 - Success):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Response (401 - Invalid Credentials):**
```json
{
  "status": 401,
  "message": "Incorrect username or password"
}
```

---

#### **POST** `/refresh`
**Description:** Refresh access token using refresh token

**Request Body:**
```json
{
  "refresh_token": "string"
}
```

**Response (200 - Success):**
```json
{
  "status": 200,
  "message": "Tokens refreshed successfully",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 3600
  }
}
```

**Response (401 - Invalid Refresh Token):**
```json
{
  "status": 401,
  "message": "Invalid refresh token"
}
```

**Response (401 - Refresh Token Not Found):**
```json
{
  "status": 401,
  "message": "Refresh token not found"
}
```

**Response (401 - Refresh Token Expired):**
```json
{
  "status": 401,
  "message": "Refresh token has expired"
}
```

**Response (500 - Server Error):**
```json
{
  "status": 500,
  "message": "Token refresh failed: [error details]"
}
```

---

#### **POST** `/auto-refresh`
**Description:** Automatically refresh tokens using token manager

**Request Body:**
```json
{
  "refresh_token": "string"
}
```

**Response (200 - Success):**
```json
{
  "status": 200,
  "message": "Tokens refreshed automatically",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 3600
  }
}
```

**Response (401 - Auto Refresh Failed):**
```json
{
  "status": 401,
  "message": "Auto refresh failed",
  "error": "Token validation failed"
}
```

**Response (500 - Server Error):**
```json
{
  "status": 500,
  "message": "Auto refresh failed: [error details]"
}
```

---

### 2. Authentication - User Profile Management

#### **GET** `/me`
**Description:** Get current user profile information

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 - Success):**
```json
{
  "status": 200,
  "message": "User profile retrieved successfully",
  "data": {
    "id": "uuid",
    "username": "string",
    "email": "string",
    "full_name": "string",
    "role": "string",
    "department": "string",
    "is_active": true,
    "is_superuser": false,
    "last_login": "2025-10-01T02:18:02.207864+00:00",
    "created_at": "2025-10-01T02:18:02.207864+00:00",
    "updated_at": "2025-10-01T02:18:02.207864+00:00"
  }
}
```

**Response (401 - Unauthorized):**
```json
{
  "status": 401,
  "message": "Token not provided"
}
```

**Response (401 - Invalid Token):**
```json
{
  "status": 401,
  "message": "Invalid token"
}
```

**Response (401 - Session Not Found):**
```json
{
  "status": 401,
  "message": "Session not found"
}
```

**Response (401 - Session Expired):**
```json
{
  "status": 401,
  "message": "Session has expired"
}
```

**Response (400 - Inactive User):**
```json
{
  "status": 400,
  "message": "Inactive user"
}
```

**Response (500 - Server Error):**
```json
{
  "status": 500,
  "message": "Failed to retrieve user profile: [error details]"
}
```

---

### 3. Authentication - User Registration Management

#### **POST** `/register`
**Description:** Register a new user account

**Request Body:**
```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "full_name": "string",
  "role": "string",
  "department": "string"
}
```

**Response (201 - Success):**
```json
{
  "status": 201,
  "message": "User registered successfully",
  "data": {
    "id": "uuid",
    "username": "string",
    "email": "string",
    "full_name": "string",
    "role": "string",
    "department": "string",
    "is_active": true,
    "is_superuser": false,
    "last_login": null,
    "created_at": "2025-10-01T02:18:02.207864+00:00",
    "updated_at": "2025-10-01T02:18:02.207864+00:00"
  }
}
```

**Response (400 - Username Already Exists):**
```json
{
  "status": 400,
  "message": "Username already exists"
}
```

**Response (400 - Email Already Exists):**
```json
{
  "status": 400,
  "message": "Email already exists"
}
```

**Response (422 - Password Validation Failed):**
```json
{
  "status": 422,
  "message": "Password validation failed",
  "errors": [
    "Password must be at least 8 characters long",
    "Password must contain at least one uppercase letter",
    "Password must contain at least one lowercase letter",
    "Password must contain at least one number",
    "Password must contain at least one special character"
  ],
  "strength": "weak"
}
```

---

### 4. Authentication - Password Management

#### **POST** `/change-password`
**Description:** Change user password (requires current password)

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "current_password": "string",
  "new_password": "string"
}
```

**Response (200 - Success):**
```json
{
  "status": 200,
  "message": "Password changed successfully",
  "revoked_sessions": 3
}
```

**Response (400 - Incorrect Current Password):**
```json
{
  "status": 400,
  "message": "Current password is incorrect"
}
```

**Response (422 - Password Validation Failed):**
```json
{
  "status": 422,
  "message": "Password validation failed",
  "errors": [
    "Password must be at least 8 characters long",
    "Password must contain at least one uppercase letter"
  ],
  "strength": "medium"
}
```

**Response (401 - Unauthorized):**
```json
{
  "status": 401,
  "message": "Token not provided"
}
```

---

#### **POST** `/request-password-reset`
**Description:** Request password reset (sends reset token to email)

**Request Body:**
```json
{
  "email": "string"
}
```

**Response (200 - Success):**
```json
{
  "status": 200,
  "message": "If the email exists, a password reset link has been sent"
}
```

**Response (200 - Success with Token (Development)):**
```json
{
  "status": 200,
  "message": "Password reset link sent to email",
  "reset_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

---

#### **POST** `/reset-password`
**Description:** Reset password using reset token

**Request Body:**
```json
{
  "token": "string",
  "new_password": "string"
}
```

**Response (200 - Success):**
```json
{
  "status": 200,
  "message": "Password reset successfully",
  "revoked_sessions": 2
}
```

**Response (400 - Invalid Reset Token):**
```json
{
  "status": 400,
  "message": "Invalid or expired reset token"
}
```

**Response (404 - User Not Found):**
```json
{
  "status": 404,
  "message": "User not found"
}
```

**Response (422 - Password Validation Failed):**
```json
{
  "status": 422,
  "message": "Password validation failed",
  "errors": [
    "Password must be at least 8 characters long"
  ],
  "strength": "weak"
}
```

---

### 5. Authentication - Session Management

#### **GET** `/token-status`
**Description:** Get current token status and information

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 - Success):**
```json
{
  "status": 200,
  "message": "Token status retrieved successfully",
  "data": {
    "is_valid": true,
    "expires_at": "2025-10-01T03:18:02.207864+00:00",
    "time_remaining": 3600,
    "user_id": "uuid",
    "username": "string",
    "role": "string"
  }
}
```

---

#### **GET** `/session`
**Description:** Get current session information

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 - Success):**
```json
{
  "status": 200,
  "message": "Session information retrieved successfully",
  "data": {
    "user_id": "uuid",
    "username": "string",
    "role": "string",
    "login_time": "2025-10-01T02:18:02.207864+00:00",
    "last_activity": "2025-10-01T02:28:02.207864+00:00",
    "expires_at": "2025-10-01T03:18:02.207864+00:00",
    "is_active": true
  }
}
```

**Response (401 - Session Not Found):**
```json
{
  "status": 401,
  "message": "Session not found"
}
```

**Response (500 - Server Error):**
```json
{
  "status": 500,
  "message": "Failed to retrieve session info: [error details]"
}
```

---

#### **POST** `/logout-all`
**Description:** Logout from all sessions and revoke all tokens

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 - Success):**
```json
{
  "status": 200,
  "message": "Logged out from 3 sessions and 2 refresh tokens"
}
```

**Response (500 - Server Error):**
```json
{
  "status": 500,
  "message": "Failed to logout all sessions: [error details]"
}
```

---

#### **GET** `/sessions/cleanup`
**Description:** Clean up expired sessions and refresh tokens

**Response (200 - Success):**
```json
{
  "status": 200,
  "message": "Cleaned up 5 expired sessions and 3 expired refresh tokens",
  "active_sessions": 12,
  "active_refresh_tokens": 8
}
```

---

## Authentication Flow

### 1. **Login Flow**
```
1. POST /auth/token
   ↓
2. Receive access_token + refresh_token
   ↓
3. Use access_token for API calls
   ↓
4. When access_token expires, use refresh_token
```

### 2. **Token Refresh Flow**
```
1. POST /auth/refresh
   ↓
2. Receive new access_token + refresh_token
   ↓
3. Use new tokens for continued access
```

### 3. **Password Reset Flow**
```
1. POST /auth/request-password-reset
   ↓
2. Receive reset token (in development)
   ↓
3. POST /auth/reset-password
   ↓
4. Password reset successfully
```

### 4. **Session Management Flow**
```
1. GET /auth/session (check session info)
   ↓
2. GET /auth/token-status (check token status)
   ↓
3. POST /auth/logout-all (logout from all sessions)
```

## Security Features

### **Token Security**
- JWT access tokens with expiration
- Refresh token rotation for security
- Session-based token management
- Token status monitoring

### **Password Security**
- Password strength validation
- Secure password hashing (bcrypt)
- Password reset with email tokens
- Session revocation on password change

### **Session Security**
- Session tracking and monitoring
- Automatic cleanup of expired sessions
- Logout all sessions functionality
- Session information retrieval

## Error Handling

### **Common Error Responses**

#### **401 Unauthorized**
- Token not provided
- Invalid token
- Session not found
- Session inactive
- Session expired
- User not found

#### **400 Bad Request**
- Username already exists
- Email already exists
- Current password incorrect
- Inactive user

#### **404 Not Found**
- User not found

#### **422 Unprocessable Entity**
- Password validation failed
- Invalid request data

#### **500 Internal Server Error**
- Server errors
- Database errors
- Token generation errors

## Rate Limiting

### **Login Attempts**
- Maximum 5 failed attempts per minute per IP
- Account lockout after 10 failed attempts
- Progressive delay for repeated failures

### **Password Reset**
- Maximum 3 reset requests per hour per email
- Rate limiting to prevent abuse

## Best Practices

### **Token Management**
1. Store tokens securely (httpOnly cookies recommended)
2. Implement automatic token refresh
3. Handle token expiration gracefully
4. Use refresh tokens for long-term sessions

### **Password Security**
1. Use strong passwords (8+ characters, mixed case, numbers, symbols)
2. Change passwords regularly
3. Don't reuse passwords across services
4. Enable two-factor authentication when available

### **Session Management**
1. Logout from all sessions when changing passwords
2. Monitor active sessions regularly
3. Clean up expired sessions
4. Use secure connections (HTTPS)

## Testing

### **Test Credentials (Development)**
```
Username: admin
Password: admin123
```

### **Test Endpoints**
```bash
# Login
curl -X POST "http://localhost:8000/api/v1/auth/oauth2/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"

# Get Profile
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer <access_token>"

# Change Password
curl -X POST "http://localhost:8000/api/v1/auth/change-password" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"current_password":"admin123","new_password":"NewPassword123!"}'
```

## API Versioning

- Current Version: v1
- Base Path: `/api/v1/auth`
- Backward Compatibility: Maintained for v1 endpoints

## Frontend Integration Guide

### **Essential Frontend Endpoints**

#### **Authentication Flow**
```javascript
// 1. Login
POST /api/v1/auth/oauth2/token
// 2. Get User Profile  
GET /api/v1/auth/me
// 3. Refresh Token
POST /api/v1/auth/refresh
// 4. Logout
POST /api/v1/auth/logout-all
```

#### **User Management Flow**
```javascript
// 1. Register User
POST /api/v1/auth/register
// 2. Change Password
POST /api/v1/auth/change-password
// 3. Request Password Reset
POST /api/v1/auth/request-password-reset
// 4. Reset Password
POST /api/v1/auth/reset-password
```

#### **Session Management Flow**
```javascript
// 1. Check Token Status
GET /api/v1/auth/token-status
// 2. Get Session Info
GET /api/v1/auth/session
// 3. Auto Refresh
POST /api/v1/auth/auto-refresh
```

### **Frontend Implementation Examples**

#### **Login Implementation**
```javascript
async function login(username, password) {
  const response = await fetch('/api/v1/auth/oauth2/token', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: `username=${username}&password=${password}`
  });
  
  const data = await response.json();
  if (data.access_token) {
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    return data;
  }
  throw new Error(data.message || 'Login failed');
}
```

#### **Token Refresh Implementation**
```javascript
async function refreshToken() {
  const refreshToken = localStorage.getItem('refresh_token');
  const response = await fetch('/api/v1/auth/refresh', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ refresh_token: refreshToken })
  });
  
  const data = await response.json();
  if (data.data?.access_token) {
    localStorage.setItem('access_token', data.data.access_token);
    localStorage.setItem('refresh_token', data.data.refresh_token);
    return data.data;
  }
  throw new Error(data.message || 'Token refresh failed');
}
```

#### **Get User Profile**
```javascript
async function getUserProfile() {
  const token = localStorage.getItem('access_token');
  const response = await fetch('/api/v1/auth/me', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  if (!response.ok) {
    throw new Error('Failed to get user profile');
  }
  
  return await response.json();
}
```

#### **Change Password**
```javascript
async function changePassword(currentPassword, newPassword) {
  const token = localStorage.getItem('access_token');
  const response = await fetch('/api/v1/auth/change-password', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      current_password: currentPassword,
      new_password: newPassword
    })
  });
  
  return await response.json();
}
```

#### **Logout Implementation**
```javascript
async function logout() {
  const token = localStorage.getItem('access_token');
  try {
    await fetch('/api/v1/auth/logout-all', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
  } finally {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    // Redirect to login page
    window.location.href = '/login';
  }
}
```

### **Frontend Error Handling**

#### **Common Error Responses**
```javascript
// Handle authentication errors
function handleAuthError(error) {
  switch (error.status) {
    case 401:
      // Token expired or invalid
      refreshToken().catch(() => {
        logout();
      });
      break;
    case 400:
      // Bad request (validation errors)
      showError(error.message);
      break;
    case 422:
      // Validation failed
      showValidationErrors(error.errors);
      break;
    default:
      showError('An unexpected error occurred');
  }
}
```

### **Frontend Security Best Practices**

#### **Token Storage**
```javascript
// Secure token storage
const TokenManager = {
  setTokens(accessToken, refreshToken) {
    // Use httpOnly cookies in production
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
  },
  
  getAccessToken() {
    return localStorage.getItem('access_token');
  },
  
  getRefreshToken() {
    return localStorage.getItem('refresh_token');
  },
  
  clearTokens() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }
};
```

#### **Automatic Token Refresh**
```javascript
// Auto refresh token before expiration
function setupTokenRefresh() {
  setInterval(async () => {
    const token = TokenManager.getAccessToken();
    if (token) {
      try {
        const response = await fetch('/api/v1/auth/token-status', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await response.json();
        
        // If token expires in less than 5 minutes, refresh it
        if (data.data?.time_remaining < 300) {
          await refreshToken();
        }
      } catch (error) {
        console.error('Token refresh check failed:', error);
      }
    }
  }, 60000); // Check every minute
}
```

## Support

For technical support or questions about the Authentication API:
- Check the API documentation
- Review error responses for troubleshooting
- Contact the development team for assistance
