# core/python/main.py
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "core", "python")))

from fastapi import FastAPI
from modules.human_system.api.user_router import router as user_router
from modules.human_system.services.user_service import UserService
from config.db_loader import load_db

# 创建 FastAPI 实例
app = FastAPI()

# 初始化数据库
db = load_db()
print("✅ FastAPI 成功加载 SurrealDB")

# 手动注入服务依赖
user_service = UserService(db=db)
user_router.user_service = user_service  # 手动注入依赖

# 挂载路由
app.include_router(user_router, prefix="/api")

@app.get("/")
def read_root():
    return {"msg": "PrizmAgent FastAPI is running"}
