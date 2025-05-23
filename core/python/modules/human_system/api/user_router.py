from fastapi import APIRouter
from core.python.modules.human_system.schemas.user_schema import UserCreate, UserResponse
from core.python.modules.human_system.interfaces.user_interface import create_user_interface

router = APIRouter()

@router.post("/user/create", response_model=UserResponse)
def create_user_endpoint(user: UserCreate):
    return create_user_interface(user)

