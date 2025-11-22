from pydantic import BaseModel, EmailStr, Field, model_validator
from typing import List
from datetime import datetime

class UserCreate(BaseModel):
    fullname: str = Field(..., min_length=1)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)
    tag: str = Field(..., description="User tag: Admin, Investigator, or Ahli Forensic")
    
    @model_validator(mode='after')
    def passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError('Password and confirm password do not match')
        return self

class UserUpdate(BaseModel):
    fullname: str = Field(..., min_length=1)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)
    tag: str = Field(..., description="User tag: Admin, Investigator, or Ahli Forensic")
    
    @model_validator(mode='after')
    def passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError('Password and confirm password do not match')
        return self

class UserResponse(BaseModel):
    id: int
    email: str
    fullname: str
    tag: str
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class UserListResponse(BaseModel):
    status: int
    message: str
    data: List[UserResponse]
    total: int
    page: int
    size: int

