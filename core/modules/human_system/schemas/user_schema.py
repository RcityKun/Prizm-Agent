from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    username: str
    nickname: Optional[str]
    gender: Optional[str]
    age: Optional[int]
    region: Optional[str]
    phone: Optional[str]

class UserResponse(BaseModel):
    id: int
    username: str
    nickname: Optional[str]
    status: str

    class Config:
        orm_mode = True
