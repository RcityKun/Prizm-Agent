from core.python.modules.human_system.models.user import User
from core.python.database.database_loader import get_db
from sqlalchemy.orm import Session

def create_user(user_data, db: Session):
    user = User(**user_data.dict())
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

