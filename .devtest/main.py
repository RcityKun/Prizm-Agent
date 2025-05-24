import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "core", "python")))
from fastapi import FastAPI
from modules.human_system.api.user_router import router as user_router
from config.db_loader import load_db
from modules.human_system.services.user_service import UserService

app = FastAPI()

# 加载数据库实例
db = load_db()

# 实例化服务并注入依赖（简化方式）
user_service = UserService(db=db)
user_router.user_service = user_service  # 手动注入

# 挂载用户路由
app.include_router(user_router, prefix="/api")

@app.get("/")
def read_root():
    return {"msg": "PrizmAgent FastAPI is running"}
