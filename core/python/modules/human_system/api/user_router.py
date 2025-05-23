from fastapi import APIRouter, HTTPException
from modules.human_system.services.user_service import UserService

router = APIRouter()
user_service = UserService(db=None)  # TODO: 实际注入 db 实例

@router.post("/users/")
async def create_user(user_data: dict):
    return await user_service.create_user(user_data)

@router.get("/users/{user_id}")
async def get_user(user_id: str):
    result = await user_service.get_user_by_id(user_id)
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    return result

@router.get("/users/")
async def list_users():
    return await user_service.list_users()
