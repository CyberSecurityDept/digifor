from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
import uuid


class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    role: str = "investigator"
    department: Optional[str] = None
    is_active: bool = True




class UserInDB(UserBase):
    id: uuid.UUID
    is_superuser: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class User(UserInDB):
    pass




class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class LoginSuccessData(BaseModel):
    access_token: str
    token_type: str


class LoginSuccessResponse(BaseModel):
    status: int
    messages: str
    data: LoginSuccessData


class LoginErrorResponse(BaseModel):
    status: str
    messages: str


class LoginRequest(BaseModel):
    username: str
    password: str


class UserProfileData(BaseModel):
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
    status: int
    message: str
    data: UserProfileData


class UserRegistration(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    password: str
    department: Optional[str] = None
    role: str = "investigator"


class UserRegistrationResponse(BaseModel):
    status: int
    message: str
    data: UserProfileData


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


class PasswordReset(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str


class SessionInfo(BaseModel):
    user_id: uuid.UUID
    username: str
    role: str
    login_time: datetime
    last_activity: datetime
    expires_at: datetime
    is_active: bool


class SessionResponse(BaseModel):
    status: int
    message: str
    data: SessionInfo


class RefreshTokenData(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


class RefreshTokenResponse(BaseModel):
    status: int
    message: str
    data: RefreshTokenData


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


class RefreshTokenRequest(BaseModel):
    refresh_token: str
