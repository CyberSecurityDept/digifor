from pydantic import BaseModel, EmailStr, ConfigDict, Field
from datetime import datetime

# ROLE
class RoleBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    description: str | None = Field(None, max_length=255)

class RoleOut(RoleBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class UserBase(BaseModel):
    email: EmailStr
    fullname:str
    is_active: bool = True

class UserCreate(BaseModel):
    email: EmailStr
    fullname: str
    password: str = Field(..., min_length=8, max_length=128)
    tag:str
    role_id: int | None = None

class UserOut(UserBase):
    id: int
    role: RoleOut | None = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class LoginRequest(BaseModel):
    email: str = Field(..., example="admin@gmail.com")
    password: str = Field(..., example="admin.admin")

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshRequest(BaseModel):
    refresh_token: str
