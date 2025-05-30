"""
db_loader.py
--------------
负责从配置文件或环境变量中加载 SurrealDB 配置信息，并实例化数据库驱动。
"""

import os
from dotenv import load_dotenv
from surrealdb.surreal_driver import SurrealDriver
load_dotenv()
def load_db():
    # 从环境变量中读取配置（也可改为从 config.yaml 加载）
    endpoint = os.getenv("SURREALDB_ENDPOINT", "http://localhost:8001")
    namespace = os.getenv("SURREALDB_NAMESPACE", "prizm")
    database = os.getenv("SURREALDB_DATABASE", "core")
    user = os.getenv("SURREALDB_USER", "root")
    password = os.getenv("SURREALDB_PASSWORD", "secret")

    db = SurrealDriver(
        endpoint=endpoint,
        namespace=namespace,
        database=database,
        user=user,
        password=password
    )
    return db

