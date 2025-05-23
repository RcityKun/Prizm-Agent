import os

# 获取当前脚本所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 获取项目根目录（假设脚本在 scripts/generate 下）
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))

# 构造目标目录路径
base_path = os.path.join(project_root, "core", "python", "modules", "human_system")
service_path = os.path.join(base_path, "services", "user_service.py")
router_path = os.path.join(base_path, "api", "user_router.py")

# 用户服务代码
user_service_code = '''\
from surrealdb.surreal_driver import SurrealDriver
from surrealdb.query_builder import QueryBuilder
from surrealdb.surreal_utils import generate_id, current_timestamp

class UserService:
    def __init__(self, db: SurrealDriver):
        self.db = db

    async def create_user(self, user_data: dict):
        user_id = generate_id()
        user_data["id"] = user_id
        user_data["created_at"] = current_timestamp()
        query = f"CREATE user CONTENT {{user_data}}"
        return await self.db.query(query)

    async def get_user_by_id(self, user_id: str):
        query = f"SELECT * FROM user WHERE id = '{{user_id}}'"
        return await self.db.query(query)

    async def list_users(self):
        query = QueryBuilder("user").build_select()
        return await self.db.query(query)
'''

# 路由代码
user_router_code = '''\
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
'''

# 创建目录并写入文件
os.makedirs(os.path.dirname(service_path), exist_ok=True)
os.makedirs(os.path.dirname(router_path), exist_ok=True)

with open(service_path, "w", encoding="utf-8") as f:
    f.write(user_service_code)

with open(router_path, "w", encoding="utf-8") as f:
    f.write(user_router_code)

print("✅ 已成功生成 user_service.py 与 user_router.py 文件！")
