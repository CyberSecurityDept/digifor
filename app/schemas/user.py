from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
import uuid


class UserBase(BaseModel):
    """Base user schema"""
    username: str
    email: EmailStr
    full_name: str
    role: str = "investigator"
    department: Optional[str] = None
    is_active: bool = True




class UserInDB(UserBase):
    """Schema for user in database"""
    id: uuid.UUID
    is_superuser: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class User(UserInDB):
    """Schema for user response"""
    pass




class Token(BaseModel):
    """Schema for authentication token"""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Schema for token data"""
    username: Optional[str] = None


class LoginSuccessData(BaseModel):
    """Schema for login success data"""
    access_token: str
    token_type: str


class LoginSuccessResponse(BaseModel):
    """Schema for login success response"""
    status: int
    messages: str
    data: LoginSuccessData


class LoginErrorResponse(BaseModel):
    """Schema for login error response"""
    status: str
    messages: str


class LoginRequest(BaseModel):
    """Schema for login request with JSON body"""
    username: str
    password: str


class UserProfileData(BaseModel):
    """Schema for user profile data in response"""
    id: uuid.UUID
    username: str
    email: str
    full_name: str
    role: str
    department: Optional[str] = None
    is_active: bool
    is_superuser: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserProfileResponse(BaseModel):
    """Schema for user profile response"""
    status: int
    message: str
    data: UserProfileData


class UserRegistration(BaseModel):
    """Schema for user registration"""
    username: str
    email: EmailStr
    full_name: str
    password: str
    department: Optional[str] = None
    role: str = "investigator"


class UserRegistrationResponse(BaseModel):
    """Schema for user registration response"""
    status: int
    message: str
    data: UserProfileData


class PasswordChange(BaseModel):
    """Schema for password change"""
    current_password: str
    new_password: str


class PasswordReset(BaseModel):
    """Schema for password reset request"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation"""
    token: str
    new_password: str


class SessionInfo(BaseModel):
    """Schema for session information"""
    user_id: uuid.UUID
    username: str
    role: str
    login_time: datetime
    last_activity: datetime
    expires_at: datetime
    is_active: bool


class SessionResponse(BaseModel):
    """Schema for session response"""
    status: int
    message: str
    data: SessionInfo


class RefreshTokenData(BaseModel):
    """Schema for refresh token data"""
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


class RefreshTokenResponse(BaseModel):
    """Schema for refresh token response"""
    status: int
    message: str
    data: RefreshTokenData


class TokenPair(BaseModel):
    """Schema for token pair (access + refresh)"""
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request"""
    refresh_token: str
