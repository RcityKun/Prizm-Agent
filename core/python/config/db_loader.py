"""
db_loader.py
--------------
负责从配置文件或环境变量中加载 SurrealDB 配置信息，并实例化数据库驱动。
"""

import os
from surrealdb.surreal_driver import SurrealDriver

def load_db():
    # 从环境变量中读取配置（也可改为从 config.yaml 加载）
    endpoint = os.getenv("SURREALDB_ENDPOINT", "http://localhost:8000/rpc")
    namespace = os.getenv("SURREALDB_NAMESPACE", "test_namespace")
    database = os.getenv("SURREALDB_DATABASE", "test_db")
    user = os.getenv("SURREALDB_USER", "root")
    password = os.getenv("SURREALDB_PASSWORD", "root")

    db = SurrealDriver(
        endpoint=endpoint,
        namespace=namespace,
        database=database,
        user=user,
        password=password
    )
    return db
