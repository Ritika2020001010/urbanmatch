from typing import List, Optional
from pydantic import BaseModel, EmailStr, validator

class UserBase(BaseModel):
    name: str
    age: int
    gender: str
    email: str  # We'll validate this manually
    city: str
    interests: str  # Comma-separated interests

    @validator('email')
    def validate_email(cls, v):
        if '@' not in v or '.' not in v:
            raise ValueError('Invalid email format')
        return v

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    email: Optional[str] = None
    city: Optional[str] = None
    interests: Optional[str] = None

    @validator('email')
    def validate_email(cls, v):
        if v is not None and ('@' not in v or '.' not in v):
            raise ValueError('Invalid email format')
        return v

class User(UserBase):
    id: int
    is_active: bool

    class Config:
        orm_mode = True