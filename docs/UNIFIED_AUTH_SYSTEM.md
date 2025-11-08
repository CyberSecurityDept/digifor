# Unified Authentication System

## Overview

Sistem autentikasi terpusat yang digunakan oleh **Analytics** dan **Case Management** applications. User login sekali, mendapatkan 1 token JWT, dan token yang sama dapat digunakan untuk mengakses kedua aplikasi.

## Architecture

```
┌─────────────────┐
│   User Login    │
│  (1x per user)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Auth Service   │
│  Generate JWT   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  JWT Token      │
│  (1 token)      │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌──────────────┐
│Analytics│ │Case Management│
│   App   │ │      App      │
└────────┘ └──────────────┘
```

## How It Works

### 1. Login Process

User melakukan login sekali melalui endpoint `/api/v1/auth/login`:

**Request:**
```json
POST /api/v1/auth/login
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "status": 200,
  "message": "Login successful",
  "data": {
    "user": {
      "id": 1,
      "email": "user@example.com",
      "fullname": "John Doe",
      "tag": "analyst",
      "role": "analyst"
    },
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

### 2. Token Verification

**AuthMiddleware** melakukan verifikasi otomatis untuk setiap request:
- ✅ Verifikasi signature token
- ✅ Cek token expiration
- ✅ Cek token blacklist
- ✅ Verifikasi user existence dan active status
- ✅ Menyimpan user di `request.state.user`

### 3. Role/Permission Checking

Setiap endpoint dapat menggunakan dependency injection untuk:
- ✅ Mengambil current user
- ✅ Mengecek role user
- ✅ Mengecek permission (jika diperlukan)

## Usage in Endpoints

### Basic Usage - Get Current User

```python
from fastapi import APIRouter, Depends
from app.api.deps import get_current_user, get_database
from app.auth.models import User
from sqlalchemy.orm import Session

router = APIRouter()

@router.get("/my-profile")
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Get current user profile.
    Works for both Analytics and Case Management.
    """
    return {
        "status": 200,
        "message": "Profile retrieved successfully",
        "data": {
            "id": current_user.id,
            "email": current_user.email,
            "fullname": current_user.fullname,
            "role": current_user.role,
            "tag": current_user.tag
        }
    }
```

### Require Specific Role

```python
from app.api.deps import require_role

@router.get("/admin-only")
async def admin_endpoint(
    current_user: User = Depends(require_role(["admin"]))
):
    """
    Endpoint hanya bisa diakses oleh admin.
    """
    return {"message": "Admin access granted"}
```

### Require Multiple Roles

```python
@router.get("/analyst-or-admin")
async def analyst_endpoint(
    current_user: User = Depends(require_role(["admin", "analyst"]))
):
    """
    Endpoint bisa diakses oleh admin atau analyst.
    """
    return {"message": "Access granted"}
```

### Require Admin

```python
from app.api.deps import require_admin

@router.delete("/delete-case/{case_id}")
async def delete_case(
    case_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_database)
):
    """
    Hanya admin yang bisa delete case.
    """
    # ... delete logic
    return {"message": "Case deleted"}
```

### Require Active User

```python
from app.api.deps import require_active_user

@router.get("/active-users-only")
async def active_user_endpoint(
    current_user: User = Depends(require_active_user)
):
    """
    Hanya user aktif yang bisa akses.
    """
    return {"message": "Active user access"}
```

### Combine Multiple Dependencies

```python
@router.post("/create-case")
async def create_case(
    case_data: CaseCreate,
    current_user: User = Depends(require_role(["admin", "investigator"])),
    db: Session = Depends(get_database)
):
    """
    Create case - hanya admin atau investigator yang bisa.
    """
    # ... create logic
    return {"message": "Case created"}
```

## Available Dependencies

### `get_current_user`
Mengambil current authenticated user dari request state.

```python
current_user: User = Depends(get_current_user)
```

### `require_role(allowed_roles: List[str])`
Mengecek apakah user memiliki role yang diizinkan.

```python
current_user: User = Depends(require_role(["admin", "analyst"]))
```

### `require_any_role(*allowed_roles: str)`
Mengecek apakah user memiliki salah satu dari role yang diizinkan.

```python
current_user: User = Depends(require_any_role("admin", "analyst"))
```

### `require_admin`
Mengecek apakah user adalah admin.

```python
current_user: User = Depends(require_admin)
```

### `require_active_user`
Mengecek apakah user account aktif.

```python
current_user: User = Depends(require_active_user)
```

## Token Structure

JWT token berisi:
```json
{
  "sub": "1",           // User ID
  "iat": 1234567890,    // Issued at
  "exp": 1234654290,    // Expiration
  "type": "access"      // Token type
}
```

**Note:** Role tidak disimpan di token, tetapi diambil dari database setelah token verification untuk memastikan role selalu up-to-date.

## Security Features

### 1. Token Verification
- ✅ Signature verification menggunakan `SECRET_KEY`
- ✅ Expiration check
- ✅ Token blacklist check

### 2. User Verification
- ✅ User existence check
- ✅ User active status check
- ✅ Role-based access control

### 3. Middleware Protection
- ✅ Automatic token verification untuk semua protected endpoints
- ✅ Public paths tidak memerlukan authentication
- ✅ Consistent error responses

## Error Responses

### 401 Unauthorized
```json
{
  "status": 401,
  "message": "Unauthorized",
  "data": null
}
```

**Causes:**
- Token tidak valid
- Token expired
- Token tidak ada di header
- User tidak ditemukan

### 403 Forbidden
```json
{
  "status": 403,
  "message": "Forbidden - Required role: admin",
  "data": null
}
```

**Causes:**
- User tidak memiliki role yang diperlukan
- User account tidak aktif

## Examples

### Example 1: Case Management Endpoint

```python
# app/api/v1/case_routes.py
from fastapi import APIRouter, Depends
from app.api.deps import get_current_user, get_database, require_role
from app.auth.models import User
from sqlalchemy.orm import Session

router = APIRouter(prefix="/cases", tags=["Case Management"])

@router.get("/get-all-cases")
async def get_cases(
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Get all cases - semua authenticated user bisa akses.
    """
    # ... implementation
    pass

@router.delete("/delete-case/{case_id}")
async def delete_case(
    case_id: int,
    current_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_database)
):
    """
    Delete case - hanya admin yang bisa.
    """
    # ... implementation
    pass
```

### Example 2: Analytics Endpoint

```python
# app/api/v1/analytics_device_routes.py
from fastapi import APIRouter, Depends
from app.api.deps import get_current_user, require_role
from app.auth.models import User

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/devices")
async def get_devices(
    current_user: User = Depends(require_role(["admin", "analyst"]))
):
    """
    Get devices - admin atau analyst bisa akses.
    """
    # ... implementation
    pass
```

## Migration Guide

### Before (Old Code)
```python
# ❌ Old way - tidak menggunakan unified auth
def get_current_user():
    return {"id": "system", "username": "system", "role": "admin"}
```

### After (New Code)
```python
# ✅ New way - menggunakan unified auth
from app.api.deps import get_current_user
from app.auth.models import User

@router.get("/endpoint")
async def my_endpoint(
    current_user: User = Depends(get_current_user)
):
    # current_user adalah User object dari database
    # Sudah terverifikasi oleh AuthMiddleware
    pass
```

## Best Practices

1. **Always use dependencies** - Jangan manual check token, gunakan dependency injection
2. **Use role-based access** - Gunakan `require_role()` untuk endpoint yang memerlukan role tertentu
3. **Combine dependencies** - Bisa combine multiple dependencies untuk complex access control
4. **Keep it simple** - AuthMiddleware sudah handle token verification, endpoint hanya perlu check role/permission

## Testing

### Test dengan Postman

1. **Login** untuk mendapatkan token:
```
POST /api/v1/auth/login
{
  "email": "user@example.com",
  "password": "password"
}
```

2. **Gunakan token** di semua request:
```
Authorization: Bearer YOUR_TOKEN_HERE
```

3. **Token yang sama** bisa digunakan untuk:
   - Analytics endpoints
   - Case Management endpoints

## FAQ

### Q: Apakah token bisa digunakan untuk kedua aplikasi?
**A:** Ya, token yang sama bisa digunakan untuk Analytics dan Case Management karena keduanya menggunakan AuthMiddleware yang sama.

### Q: Bagaimana cara mengecek role user?
**A:** Gunakan dependency `require_role(["admin"])` atau `require_admin` di endpoint.

### Q: Apakah perlu verifikasi token manual?
**A:** Tidak, AuthMiddleware sudah handle semua verifikasi. Endpoint hanya perlu check role/permission.

### Q: Bagaimana jika user role berubah?
**A:** Role diambil dari database setiap request, jadi perubahan role langsung berlaku tanpa perlu login ulang.

### Q: Apakah token expired?
**A:** Token akan expired sesuai `ACCESS_TOKEN_EXPIRE_MINUTES` di config. User perlu login ulang untuk mendapatkan token baru.

## Summary

✅ **1 Login** - User login sekali  
✅ **1 Token** - Generate 1 JWT token  
✅ **2 Apps** - Token bisa digunakan untuk Analytics & Case Management  
✅ **Auto Verification** - AuthMiddleware handle token verification  
✅ **Role Checking** - Dependency injection untuk role/permission checking  
✅ **No JSON Changes** - Struktur JSON response tetap sama  

