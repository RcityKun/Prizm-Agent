from sqlalchemy import Column, Integer, String
from core.python.database.schema.base import Base  # 引用统一Base类路径

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False, unique=True)
    nickname = Column(String)
    avatar = Column(String)
    gender = Column(String)
    age = Column(Integer)
    region = Column(String)
    phone = Column(String)
    signature = Column(String)

    race = Column(String)
    religion = Column(String)
    profession = Column(String)
    industry = Column(String)
    hobbies = Column(String)  # 存储格式后续决定：JSON or 逗号分隔
    qr_code = Column(String)
    status = Column(String, default="active")  # active / frozen / banned

