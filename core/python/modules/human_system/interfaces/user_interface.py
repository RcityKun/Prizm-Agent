from core.python.database.database_loader import get_db
from core.python.modules.human_system.schemas.user_schema import UserCreate
from core.python.modules.human_system.services.user_service import create_user

def create_user_interface(user_data: UserCreate):
    db = get_db()
    return create_user(user_data, db)
