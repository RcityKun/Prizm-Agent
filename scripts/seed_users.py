# scripts/seed_users.py

import asyncio
import logging
from datetime import datetime
from core.surrealdb.surreal_driver import SurrealDriver

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def seed_users():
    # ... (driver 初始化代码不变) ...
    driver = SurrealDriver(
        endpoint="ws://127.0.0.1:8000",
        namespace="prizm",
        database="core",
        user="root",
        password="root",
    )

    async with driver:
        user_data = {
            "username": "admin",
            "email": "admin@example.com",
            # 返璞归真：直接使用原生的 datetime 对象
            "created_at": datetime.utcnow(), 
            "age": 99
        }

        try:
            # 使用我们智能的 insert 方法，并传入指定ID
            result = await driver.insert("user:admin001", user_data)
            logger.info("✅ 插入成功，结果: %s", result)
        except Exception as e:
            logger.error("❌ 插入失败: %s", e, exc_info=True)

if __name__ == "__main__":
    asyncio.run(seed_users())