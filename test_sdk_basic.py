import asyncio
from surrealdb import AsyncSurreal

async def test_connect():
    print("🔌 开始异步连接测试")
    
    try:
        # 1. 创建异步客户端（不会立即连接）
        db = AsyncSurreal(url="ws://127.0.0.1:8001/rpc")
        
        # 2. 建立连接（关键步骤）
        await db.connect()
        print("✅ 成功连接到 SurrealDB")

        # 3. 可选：登录认证（如果启用认证）
        # await db.signin({"user": "root", "pass": "root"})
        # print("🔐 已登录")

        # 4. 可选：切换命名空间/数据库
        # await db.use("test", "test")
        # print("🧱 已切换到 test/test")

    except Exception as e:
        print(f"❌ 连接失败: {str(e)}")
    
    finally:
        # 5. 安全关闭连接
        await db.close()
        print("🔌 连接已关闭")

# 运行异步测试
asyncio.run(test_connect())