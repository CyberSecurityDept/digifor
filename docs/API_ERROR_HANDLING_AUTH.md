# API Error Handling Documentation - Authentication

## Overview

This document describes the comprehensive error handling implemented for the Authentication API endpoints, including:
- `/api/v1/auth/login` - User login
- `/api/v1/auth/refresh` - Refresh access token
- `/api/v1/auth/logout` - User logout
- `/api/v1/auth/me` - Get current user profile

All error responses follow a consistent format and provide user-friendly messages without exposing technical details.

### Important Note: Server Down vs Application Errors

**Server Down (ECONNREFUSED) - FRONTEND/CLIENT SIDE:**
When the server/service is completely down or unreachable, you will see connection errors like:
- `Error: connect ECONNREFUSED <host>:<port>`
- `Could not send request`
- Network timeout errors

**These errors occur at the network/client level BEFORE the request reaches the server.** 
- ❌ **Backend error handling CANNOT handle these errors** (request never reaches the server)
- ✅ **Frontend/Client MUST handle these errors** (happens before request is sent)

**Error Handling Responsibility:**
- **Frontend/Client:** Handles network errors (ECONNREFUSED, timeout, network failures)
- **Backend:** Handles application errors (validation, database, token generation) - only when request reaches server

**Application Errors - BACKEND SIDE:**
The error handling documented below applies when the server is running but encounters errors during request processing (database connection issues, validation errors, etc.). These are handled by the backend and return proper HTTP status codes.

**To test application-level error handling:**
- Keep the server running
- Stop only the database service (to test database connection errors - backend returns 503)
- Send invalid data (to test validation errors - backend returns 400)

## Error Response Format

All error responses follow this standard format:

```json
{
  "status": <HTTP_STATUS_CODE>,
  "message": "<USER_FRIENDLY_MESSAGE>",
  "data": null
}
```

## Endpoint: POST `/api/v1/auth/login`

### Request Headers

| Header | Required | Description |
|--------|----------|-------------|
| `Content-Type` | Yes | Must be `application/json` |

### Request Body

```json
{
  "email": "string",
  "password": "string"
}
```

### Success Response (200 OK)

```json
{
  "status": 200,
  "message": "Login successful",
  "data": {
    "user": {
      "id": 1,
      "email": "admin@gmail.com",
      "fullname": "Admin User",
      "tag": "Admin",
      "role": "admin"
    },
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "token_string_here"
  }
}
```

---

## Error Responses

### 1. Validation Errors (400 Bad Request)

#### 1.1 Email Required

**Status Code:** `400`

**Response:**
```json
{
  "status": 400,
  "message": "Email is required",
  "data": null
}
```

**Triggered When:**
- Email field is missing or empty
- Email field contains only whitespace

---

#### 1.2 SQL Injection Detected in Email

**Status Code:** `400`

**Response:**
```json
{
  "status": 400,
  "message": "Invalid characters detected in email. Please remove any SQL injection attempts or malicious code.",
  "data": null
}
```

**Triggered When:**
- Email contains SQL injection patterns
- Email contains XSS patterns
- Email contains other malicious code patterns

---

#### 1.3 Invalid Email Format

**Status Code:** `400`

**Response:**
```json
{
  "status": 400,
  "message": "Invalid email format",
  "data": null
}
```

**Triggered When:**
- Email does not contain `@` symbol
- Email does not contain a valid domain (no `.` after `@`)
- Email format is invalid

---

#### 1.4 Password Required

**Status Code:** `400`

**Response:**
```json
{
  "status": 400,
  "message": "Password is required",
  "data": null
}
```

**Triggered When:**
- Password field is missing or empty
- Password field contains only whitespace

---

#### 1.5 SQL Injection Detected in Password

**Status Code:** `400`

**Response:**
```json
{
  "status": 400,
  "message": "Invalid characters detected in password. Please remove any SQL injection attempts or malicious code.",
  "data": null
}
```

**Triggered When:**
- Password contains SQL injection patterns
- Password contains XSS patterns
- Password contains other malicious code patterns

---

#### 1.6 Password Too Short

**Status Code:** `400`

**Response:**
```json
{
  "status": 400,
  "message": "Password must be at least 8 characters long",
  "data": null
}
```

**Triggered When:**
- Password length is less than 8 characters

---

#### 1.7 Password Too Long

**Status Code:** `400`

**Response:**
```json
{
  "status": 400,
  "message": "Password must not exceed 128 characters",
  "data": null
}
```

**Triggered When:**
- Password length exceeds 128 characters

---

### 2. Authentication Errors (401 Unauthorized)

#### 2.1 Invalid Credentials

**Status Code:** `401`

**Response:**
```json
{
  "status": 401,
  "message": "Invalid credentials",
  "data": null
}
```

**Triggered When:**
- User with provided email does not exist
- User account is inactive (`is_active = False`)
- Password does not match the stored hash

**Note:** For security reasons, the same generic message is returned for all authentication failures to prevent user enumeration attacks.

---

### 3. Server Errors (500 Internal Server Error)

#### 3.1 Database Error

**Status Code:** `500`

**Response:**
```json
{
  "status": 500,
  "message": "An error occurred while processing your request. Please try again later.",
  "data": null
}
```

**Triggered When:**
- SQLAlchemy error occurs (excluding connection errors)
- Database query fails
- Database transaction fails

**Internal Logging:**
- Full error details are logged server-side with `logger.error()`
- Stack trace is captured for debugging

---

#### 3.2 Token Creation Error

**Status Code:** `500`

**Response:**
```json
{
  "status": 500,
  "message": "An error occurred while generating authentication token. Please try again later.",
  "data": null
}
```

**Triggered When:**
- JWT token creation fails
- Token encoding error occurs
- Any exception during access token generation

**Internal Logging:**
- Full error details are logged server-side with `logger.error()`
- Stack trace is captured for debugging

---

#### 3.3 Unexpected Error

**Status Code:** `500`

**Response:**
```json
{
  "status": 500,
  "message": "An unexpected error occurred. Please try again later.",
  "data": null
}
```

**Triggered When:**
- Any unhandled exception occurs
- Unexpected error during login process

**Internal Logging:**
- Full error details are logged server-side with `logger.error()`
- Stack trace is captured for debugging
- Database rollback is attempted

---

### 4. Service Unavailable Errors (503 Service Unavailable)

#### 4.1 Database Connection Error

**Status Code:** `503`

**Response:**
```json
{
  "status": 503,
  "message": "Service temporarily unavailable. Please try again later.",
  "data": null
}
```

**Triggered When:**
- Database connection is refused (ECONNREFUSED)
- Database connection timeout
- Database connection lost
- `OperationalError` or `DisconnectionError` from SQLAlchemy
- `psycopg2.OperationalError` or `psycopg2.InterfaceError` (if psycopg2 is available)

**Common Scenarios:**
- Database server is down
- Database server is unreachable
- Network connectivity issues
- Database connection pool exhausted
- Database server is restarting

**Internal Logging:**
- Full error details are logged server-side with `logger.error()`
- Stack trace is captured for debugging
- Database rollback is performed

---

## Error Handling Flow

### 1. Input Validation
```
Request → Email Validation → Password Validation → Security Checks
```

### 2. Database Operations
```
User Lookup → Error Handling → User Verification → Password Verification
```

### 3. Token Generation
```
Access Token Creation → Error Handling → Refresh Token Creation → Error Handling
```

### 4. Response
```
Success Response OR Error Response (with appropriate status code)
```

---

## Error Handling Implementation Details

### Database Error Detection

The system detects database connection errors through multiple mechanisms:

1. **SQLAlchemy Errors:**
   - `OperationalError`: Database connection issues
   - `DisconnectionError`: Connection lost
   - `SQLAlchemyError`: General database errors

2. **psycopg2 Errors (if available):**
   - `psycopg2.OperationalError`: PostgreSQL connection errors
   - `psycopg2.InterfaceError`: PostgreSQL interface errors

3. **Error Chain Inspection:**
   - Checks exception `__cause__` attribute for nested psycopg2 errors

### Security Features

1. **SQL Injection Prevention:**
   - All inputs are validated using `validate_sql_injection_patterns()`
   - Inputs are sanitized using `sanitize_input()`

2. **Error Message Security:**
   - No technical details exposed to users
   - Generic error messages prevent information leakage
   - Full error details logged server-side only

3. **Database Rollback:**
   - All database errors trigger rollback
   - Prevents partial state updates

---

## Frontend/Client Error Handling

### Handling Network Errors (ECONNREFUSED, Timeout, etc.)

**Important:** These errors occur BEFORE the request reaches the server, so they must be handled in the frontend/client code.

```javascript
async function login(email, password) {
  try {
    const response = await fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        email: email,
        password: password
      })
    });

    // Check if response was received
    if (!response.ok) {
      // Try to parse error response from backend
      try {
        const errorData = await response.json();
        return {
          success: false,
          status: errorData.status,
          message: errorData.message
        };
      } catch (e) {
        // Response is not JSON (shouldn't happen, but handle it)
        return {
          success: false,
          status: response.status,
          message: 'An error occurred. Please try again.'
        };
      }
    }

    // Success - parse response
    const data = await response.json();
    return {
      success: true,
      data: data
    };

  } catch (error) {
    // Network errors (ECONNREFUSED, timeout, etc.)
    // These occur BEFORE request reaches server
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      // Network error - server is down or unreachable
      return {
        success: false,
        status: 'NETWORK_ERROR',
        message: 'Cannot connect to server. Please check if the server is running and try again.'
      };
    }
    
    if (error.name === 'AbortError') {
      // Request timeout
      return {
        success: false,
        status: 'TIMEOUT',
        message: 'Request timed out. Please check your connection and try again.'
      };
    }

    // Other errors
    return {
      success: false,
      status: 'UNKNOWN_ERROR',
      message: 'An unexpected error occurred. Please try again.'
    };
  }
}
```

### Complete Example with All Error Types

```javascript
async function handleLogin(email, password) {
  try {
    const response = await fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ email, password }),
      // Add timeout
      signal: AbortSignal.timeout(10000) // 10 seconds
    });

    const data = await response.json();

    if (response.ok && data.status === 200) {
      // Success
      localStorage.setItem('access_token', data.data.access_token);
      localStorage.setItem('refresh_token', data.data.refresh_token);
      return { success: true, message: 'Login successful' };
    } else {
      // Backend returned error (400, 401, 500, 503)
      return handleBackendError(data);
    }
  } catch (error) {
    // Network/Client-side errors
    return handleNetworkError(error);
  }
}

function handleBackendError(data) {
  switch (data.status) {
    case 400:
      return { 
        success: false, 
        message: data.message || 'Invalid input. Please check your email and password.',
        type: 'VALIDATION_ERROR'
      };
    case 401:
      return { 
        success: false, 
        message: 'Invalid credentials. Please check your email and password.',
        type: 'AUTH_ERROR'
      };
    case 500:
      return { 
        success: false, 
        message: 'Server error. Please try again later.',
        type: 'SERVER_ERROR'
      };
    case 503:
      return { 
        success: false, 
        message: 'Service temporarily unavailable. Please try again in a moment.',
        type: 'SERVICE_UNAVAILABLE'
      };
    default:
      return { 
        success: false, 
        message: data.message || 'An error occurred. Please try again.',
        type: 'UNKNOWN_ERROR'
      };
  }
}

function handleNetworkError(error) {
  if (error.name === 'TypeError' && error.message.includes('fetch')) {
    // ECONNREFUSED, network unreachable, etc.
    return {
      success: false,
      message: 'Cannot connect to server. Please check if the server is running.',
      type: 'NETWORK_ERROR'
    };
  }
  
  if (error.name === 'AbortError' || error.name === 'TimeoutError') {
    return {
      success: false,
      message: 'Request timed out. Please check your connection.',
      type: 'TIMEOUT_ERROR'
    };
  }

  return {
    success: false,
    message: 'Network error. Please check your connection and try again.',
    type: 'NETWORK_ERROR'
  };
}
```

---

## Best Practices for Client Implementation

### 1. Error Handling (Backend Errors - When Server is Running)

```javascript
try {
  const response = await fetch('/api/v1/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      email: 'user@example.com',
      password: 'password123'
    })
  });

  const data = await response.json();

  if (response.ok && data.status === 200) {
    // Success - store tokens
    localStorage.setItem('access_token', data.data.access_token);
    localStorage.setItem('refresh_token', data.data.refresh_token);
  } else {
    // Handle error based on status code
    switch (data.status) {
      case 400:
        // Validation error - show field-specific message
        console.error('Validation error:', data.message);
        break;
      case 401:
        // Authentication error - show login failed message
        console.error('Authentication failed:', data.message);
        break;
      case 500:
        // Server error - show generic error message
        console.error('Server error:', data.message);
        break;
      case 503:
        // Service unavailable - show retry message
        console.error('Service unavailable:', data.message);
        // Implement retry logic
        break;
      default:
        console.error('Unknown error:', data.message);
    }
  }
} catch (error) {
  // Network error or other exception
  console.error('Request failed:', error);
}
```

### 2. Retry Logic for 503 Errors

```javascript
async function loginWithRetry(email, password, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email, password })
      });

      const data = await response.json();

      if (response.ok && data.status === 200) {
        return data;
      } else if (data.status === 503 && i < maxRetries - 1) {
        // Wait before retry (exponential backoff)
        await new Promise(resolve => setTimeout(resolve, Math.pow(2, i) * 1000));
        continue;
      } else {
        throw new Error(data.message);
      }
    } catch (error) {
      if (i === maxRetries - 1) {
        throw error;
      }
      await new Promise(resolve => setTimeout(resolve, Math.pow(2, i) * 1000));
    }
  }
}
```

### 3. User Feedback

- **400 Errors:** Show field-specific validation messages
- **401 Errors:** Show generic "Invalid credentials" message
- **500 Errors:** Show "Something went wrong. Please try again."
- **503 Errors:** Show "Service temporarily unavailable. Please try again in a moment."

---

## Status Code Summary

| Status Code | Description | When to Use |
|-------------|-------------|-------------|
| 200 | Success | Login successful |
| 400 | Bad Request | Validation errors, invalid input format |
| 401 | Unauthorized | Invalid credentials, inactive account |
| 500 | Internal Server Error | Server-side errors, token generation failures |
| 503 | Service Unavailable | Database connection errors, service downtime |

---

## Endpoint: POST `/api/v1/auth/refresh`

### Request Headers

| Header | Required | Description |
|--------|----------|-------------|
| `Content-Type` | Yes | Must be `application/json` |

### Request Body

```json
{
  "refresh_token": "string"
}
```

### Success Response (200 OK)

```json
{
  "status": 200,
  "message": "Token refreshed successfully",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "new_token_string_here"
  }
}
```

---

### Error Responses for Refresh Endpoint

#### 1. Refresh Token Required

**Status Code:** `400`

**Response:**
```json
{
  "status": 400,
  "message": "Refresh token is required",
  "data": null
}
```

**Triggered When:**
- Refresh token field is missing or empty
- Refresh token field contains only whitespace

---

#### 2. SQL Injection Detected in Refresh Token

**Status Code:** `400`

**Response:**
```json
{
  "status": 400,
  "message": "Invalid characters detected in refresh token. Please remove any SQL injection attempts or malicious code.",
  "data": null
}
```

**Triggered When:**
- Refresh token contains SQL injection patterns
- Refresh token contains XSS patterns
- Refresh token contains other malicious code patterns

---

#### 3. Invalid Refresh Token Format

**Status Code:** `400`

**Response:**
```json
{
  "status": 400,
  "message": "Invalid refresh token format",
  "data": null
}
```

**Triggered When:**
- Refresh token length is less than 20 characters
- Refresh token length exceeds 1000 characters

---

#### 4. Invalid or Expired Refresh Token

**Status Code:** `401`

**Response:**
```json
{
  "status": 401,
  "message": "Invalid or expired refresh token",
  "data": null
}
```

**Triggered When:**
- Refresh token does not exist in database
- Refresh token has been revoked
- Refresh token has expired
- Refresh token is associated with a non-existent user

---

#### 5. Database Connection Error

**Status Code:** `503`

**Response:**
```json
{
  "status": 503,
  "message": "Service temporarily unavailable. Please try again later.",
  "data": null
}
```

**Triggered When:**
- Database connection is refused during token validation
- Database connection timeout during token operations
- Database connection lost during token revocation or creation
- `OperationalError` or `DisconnectionError` from SQLAlchemy
- `psycopg2.OperationalError` or `psycopg2.InterfaceError` (if psycopg2 is available)

**Internal Logging:**
- Full error details are logged server-side with `logger.error()`
- Stack trace is captured for debugging
- Database rollback is performed

---

#### 6. Database Error

**Status Code:** `500`

**Response:**
```json
{
  "status": 500,
  "message": "An error occurred while processing your request. Please try again later.",
  "data": null
}
```

**Triggered When:**
- SQLAlchemy error occurs during token operations (excluding connection errors)
- Database query fails during token validation, revocation, or creation
- Database transaction fails

**Internal Logging:**
- Full error details are logged server-side with `logger.error()`
- Stack trace is captured for debugging
- Database rollback is performed

---

#### 7. Token Creation Error

**Status Code:** `500`

**Response:**
```json
{
  "status": 500,
  "message": "An error occurred while generating authentication token. Please try again later.",
  "data": null
}
```

**Triggered When:**
- JWT token creation fails
- Token encoding error occurs
- Any exception during access token generation

**Internal Logging:**
- Full error details are logged server-side with `logger.error()`
- Stack trace is captured for debugging

---

#### 8. Unexpected Error

**Status Code:** `500`

**Response:**
```json
{
  "status": 500,
  "message": "An unexpected error occurred. Please try again later.",
  "data": null
}
```

**Triggered When:**
- Any unhandled exception occurs during token refresh process

**Internal Logging:**
- Full error details are logged server-side with `logger.error()`
- Stack trace is captured for debugging
- Database rollback is attempted

---

## Endpoint: POST `/api/v1/auth/logout`

### Request Headers

| Header | Required | Description |
|--------|----------|-------------|
| `Authorization` | Yes | Must be `Bearer <access_token>` |
| `Content-Type` | No | Optional, can be `application/json` |

### Success Response (200 OK)

```json
{
  "status": 200,
  "message": "Logout successful. Access token revoked.",
  "data": null
}
```

---

### Error Responses for Logout Endpoint

#### 1. Unauthorized - Missing or Invalid Token

**Status Code:** `401`

**Response:**
```json
{
  "status": 401,
  "message": "Not authenticated",
  "data": null
}
```

**Triggered When:**
- Authorization header is missing
- Authorization header does not start with "Bearer "
- Access token is invalid
- Access token has expired
- Access token is blacklisted

**Note:** This error is handled by the `get_current_user` dependency, not directly in the logout endpoint.

---

#### 2. Logout Failed

**Status Code:** `500`

**Response:**
```json
{
  "status": 500,
  "message": "Failed to logout user",
  "data": null
}
```

**Triggered When:**
- Database error occurs during token revocation
- Database error occurs during refresh token revocation
- Any unexpected exception during logout process

**Internal Logging:**
- Full error details are logged server-side with `logger.error()`
- Stack trace is captured for debugging
- Database rollback is performed

---

## Endpoint: GET `/api/v1/auth/me`

### Request Headers

| Header | Required | Description |
|--------|----------|-------------|
| `Authorization` | Yes | Must be `Bearer <access_token>` |

### Success Response (200 OK)

```json
{
  "status": 200,
  "message": "User profile retrieved successfully",
  "data": {
    "id": 1,
    "email": "admin@gmail.com",
    "fullname": "Admin User",
    "tag": "Admin",
    "role": "admin",
    "password": ""
  }
}
```

---

### Error Responses for Get Me Endpoint

#### 1. Unauthorized - Missing or Invalid Token

**Status Code:** `401`

**Response:**
```json
{
  "status": 401,
  "message": "Not authenticated",
  "data": null
}
```

**Triggered When:**
- Authorization header is missing
- Authorization header does not start with "Bearer "
- Access token is invalid
- Access token has expired
- Access token is blacklisted

**Note:** This error is handled by the `get_current_user` dependency, not directly in the get_me endpoint.

---

#### 2. Missing User Data

**Status Code:** `500`

**Response:**
```json
{
  "status": 500,
  "message": "Failed to retrieve user profile - missing user data",
  "data": null
}
```

**Triggered When:**
- User object is missing required attributes (AttributeError)
- User data is incomplete or corrupted

**Internal Logging:**
- Full error details are logged server-side with `logger.error()`
- Stack trace is captured for debugging
- Specific attribute that is missing is logged

---

#### 3. Failed to Retrieve User Profile

**Status Code:** `500`

**Response:**
```json
{
  "status": 500,
  "message": "Failed to retrieve user profile",
  "data": null
}
```

**Triggered When:**
- Any unexpected exception occurs during profile retrieval
- Database error (if any database operations are performed)
- Any other unhandled error

**Internal Logging:**
- Full error details are logged server-side with `logger.error()`
- Stack trace is captured for debugging

---

## Testing Error Scenarios

### 1. Test Validation Errors

```bash
# Missing email
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"password": "password123"}'

# Invalid email format
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "invalid-email", "password": "password123"}'

# Password too short
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "short"}'
```

### 2. Test Authentication Errors

```bash
# Invalid credentials
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "nonexistent@example.com", "password": "wrongpassword"}'
```

### 3. Test Database Connection Errors

To test database connection errors, you can:
- Stop the database server
- Block database port in firewall
- Use incorrect database connection string

---

### 4. Test Refresh Token Errors

```bash
# Missing refresh token
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{}'

# Invalid refresh token format (too short)
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "short"}'

# Invalid or expired refresh token
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "invalid_token_here"}'
```

### 5. Test Logout Errors

```bash
# Missing authorization header
curl -X POST http://localhost:8000/api/v1/auth/logout

# Invalid token
curl -X POST http://localhost:8000/api/v1/auth/logout \
  -H "Authorization: Bearer invalid_token"
```

### 6. Test Get Me Errors

```bash
# Missing authorization header
curl -X GET http://localhost:8000/api/v1/auth/me

# Invalid token
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer invalid_token"

# Expired token
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer expired_token_here"
```

---

## Changelog

### Version 1.1.0 (Current)
- Added comprehensive error handling for login endpoint
- Added error handling documentation for refresh token endpoint
- Added error handling documentation for logout endpoint
- Added error handling documentation for get user profile endpoint
- Implemented database connection error detection
- Added SQL injection and XSS pattern validation
- Added token creation error handling
- Implemented proper database rollback on errors
- Added server-side logging for all errors
- Standardized error response format

### Version 1.0.0
- Initial release with login endpoint error handling

---

## Troubleshooting

### Server Connection Errors (ECONNREFUSED)

**Symptom:** `Error: connect ECONNREFUSED <host>:<port>` or "Could not send request"

**Cause:** The server/service is not running or unreachable.

**Why Error Handling Doesn't Appear:**
When the server is completely down, the error occurs at the **network/client level** before the request reaches the FastAPI application. The error handling documented in this file only works when:
- ✅ The server is running and accessible
- ✅ The request successfully reaches the FastAPI application
- ✅ Errors occur within the application (validation, database, token generation, etc.)

**Solution:**
1. Verify the server is running:
   ```bash
   # Check if service is running
   systemctl status digifor  # or your service name
   
   # Or check if process is running
   ps aux | grep uvicorn
   ```

2. Start the server:
   ```bash
   # Using systemd
   sudo systemctl start digifor
   
   # Or manually
   source venv/bin/activate
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. Verify network connectivity:
   ```bash
   # Test if port is accessible
   telnet <host> <port>
   # or
   curl http://<host>:<port>/health
   ```

**Note:** These connection errors occur at the network level and cannot be handled by application-level error handling. The error responses documented in this file only apply when the server is running and the request reaches the application.

### Application-Level Errors

If you're seeing application-level errors (400, 401, 500, 503) but the server is running, refer to the specific error sections above for troubleshooting steps.

**To test application-level error handling:**
- Keep the server running
- Stop only the database service (to test database connection errors - will return 503)
- Send invalid data (to test validation errors - will return 400)
- Use invalid credentials (to test authentication errors - will return 401)

---

## Support

For issues or questions regarding error handling:
- **Server Connection Issues:** Check if the server process is running and accessible
- **Application Errors:** Check server logs for detailed error information
- **Database Errors:** Verify database connectivity and configuration
- **Validation Errors:** Review input validation requirements
- **Persistent 503 Errors:** Contact system administrator for service availability issues

