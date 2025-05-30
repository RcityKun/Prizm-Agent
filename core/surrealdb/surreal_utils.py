# 工具函数集合
import uuid
from datetime import datetime

def generate_id():
    """生成唯一的 UUID 字符串"""
    return str(uuid.uuid4())

def current_timestamp():
    """返回当前 UTC 时间戳（ISO 格式）"""
    return datetime.utcnow().isoformat() + 'Z'
