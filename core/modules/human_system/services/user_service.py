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
