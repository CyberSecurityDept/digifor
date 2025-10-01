# Frontend API Endpoints Summary

## Overview
This document provides a quick reference for all API endpoints that will be consumed by the frontend application.

## Authentication API (`/api/v1/auth`)

### **Login Management**
- ✅ `POST /token` - Login dengan username/password
- ✅ `POST /oauth2/token` - OAuth2 compatible login  
- ✅ `POST /refresh` - Refresh access token
- ✅ `POST /auto-refresh` - Auto refresh tokens

### **User Profile Management**
- ✅ `GET /me` - Get current user profile

### **User Registration Management**
- ✅ `POST /register` - Register new user

### **Password Management**
- ✅ `POST /change-password` - Change user password
- ✅ `POST /request-password-reset` - Request password reset
- ✅ `POST /reset-password` - Reset password

### **Session Management**
- ✅ `GET /token-status` - Check token status
- ✅ `GET /session` - Get session information
- ✅ `POST /logout-all` - Logout from all sessions

## Case Management API (`/api/v1/cases`)

### **Case List Management**
- ✅ `GET /overview` - Get dashboard statistics for case management cards
- ✅ `GET /get-all-cases/` - Retrieve paginated list of cases with filtering options
- ✅ `GET /search` - Search cases with advanced filters
- ✅ `GET /filter-options` - Get available filter options for case list
- ✅ `GET /form-options` - Get dropdown options for case creation form

### **Case Detail Management**
- ✅ `POST /create-cases/` - Create new case
- ✅ `GET /case-by-id` - Get case by ID
- ✅ `GET /{case_id}/detail` - Get comprehensive case details
- ✅ `PUT /update-case/{case_id}` - Update case information
- ✅ `DELETE /delete-case/` - Delete case
- ✅ `GET /{case_id}/stats` - Get case statistics
- ✅ `GET /{case_id}/export/pdf` - Export case to PDF

### **Case Person of Interest Management**
- ✅ `POST /{case_id}/persons` - Add person of interest to case
- ✅ `GET /{case_id}/persons` - Get all persons of interest for a case
- ✅ `PUT /{case_id}/persons/{person_id}` - Update person of interest
- ✅ `DELETE /{case_id}/persons/{person_id}` - Remove person of interest

### **Case Evidence Management**
- ✅ `POST /{case_id}/persons/{person_id}/evidence/{evidence_id}` - Associate evidence with person

### **Case Log & Notes Management**
- ✅ `GET /{case_id}/activities` - Get case activities/log
- ✅ `GET /{case_id}/activities/recent` - Get recent case activities
- ✅ `GET /{case_id}/status-history` - Get case status history
- ✅ `POST /{case_id}/notes` - Add note to case
- ✅ `GET /{case_id}/notes` - Get case notes
- ✅ `DELETE /{case_id}/notes/{note_index}` - Delete case note
- ✅ `POST /{case_id}/close` - Close case
- ✅ `POST /{case_id}/reopen` - Reopen case
- ✅ `POST /{case_id}/change-status` - Change case status

## Total Endpoints for Frontend

### **Authentication API: 12 endpoints**
- 4 Login Management endpoints
- 1 User Profile Management endpoint
- 1 User Registration Management endpoint
- 3 Password Management endpoints
- 3 Session Management endpoints

### **Case Management API: 24 endpoints**
- 5 Case List Management endpoints
- 7 Case Detail Management endpoints
- 4 Case Person of Interest Management endpoints
- 1 Case Evidence Management endpoint
- 7 Case Log & Notes Management endpoints

### **Total: 36 endpoints** yang akan dikonsumsi oleh frontend

## Documentation Files

### **Complete Documentation**
- `docs/AUTHENTICATION_API_DOCUMENTATION.md` - Complete Authentication API documentation
- `docs/CASE_MANAGEMENT_API_DOCUMENTATION.md` - Complete Case Management API documentation

### **Quick Reference**
- `docs/FRONTEND_ENDPOINTS_SUMMARY.md` - This file (Quick reference for all frontend endpoints)

## Frontend Implementation Notes

### **Authentication Flow**
1. Login → Get tokens → Store tokens → Use for API calls
2. Token refresh → Update stored tokens
3. Logout → Clear tokens → Redirect to login

### **Case Management Flow**
1. Get case list → Display cases → Select case → Get case detail
2. Create case → Add persons → Add notes → Manage case status
3. Search/filter cases → Update case → Export case

### **Error Handling**
- 401 Unauthorized → Redirect to login
- 404 Not Found → Show not found message
- 400 Bad Request → Show validation errors
- 422 Unprocessable Entity → Show field-specific errors
- 500 Server Error → Show generic error message

### **Security Considerations**
- All endpoints require Bearer token authentication
- Store tokens securely (httpOnly cookies recommended)
- Implement automatic token refresh
- Handle token expiration gracefully
- Use HTTPS in production
