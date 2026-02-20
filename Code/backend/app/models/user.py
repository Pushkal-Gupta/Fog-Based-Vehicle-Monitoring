from pydantic import BaseModel, EmailStr, Field


class UserModel(BaseModel):
    uid: str = Field(...)
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=100)
    created_at: int