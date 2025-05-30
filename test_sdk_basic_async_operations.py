import asyncio, logging
from surrealdb import AsyncSurreal

logging.basicConfig(level=logging.INFO)

async def main():
    async with AsyncSurreal("ws://127.0.0.1:8001/rpc") as db:
        await db.signin({"username": "root", "password": "root"})  # 关键: 字段名
        await db.use("prizm", "core")

        # Create
        print(await db.create("person", {
            "user": "me",
            "password": "safe",
            "tags": ["python"],
        }))

        # Read
        print(await db.select("person"))

        # Update
        print(await db.update("person", {"tags": ["awesome"]}))

        # Delete
        print(await db.delete("person"))

asyncio.run(main())
