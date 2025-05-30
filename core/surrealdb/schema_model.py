# core/surrealdb/schema_model.py

from __future__ import annotations

"""
定义 SurrealDB 表结构的 Pydantic 数据模型。

用途：
- 校验 schema 文件格式
- 类型提示与 IDE 补全
- 支撑后续自动注入、权限生成等逻辑
"""

from typing import List, Literal, Optional, Union
from pydantic import BaseModel, Field, ConfigDict


class FieldPermission(BaseModel):
    """字段级权限声明"""
    select: Optional[str] = None
    create: Optional[str] = None
    update: Optional[str] = None


class TablePermissions(BaseModel):
    """表级权限声明"""
    select: Optional[str] = None
    create: Optional[str] = None
    update: Optional[str] = None
    delete: Optional[str] = None


class TableField(BaseModel):
    """字段定义"""
    name: str
    kind: Literal["field"]
    data_type: str = Field(..., alias="type")     # 注意：YAML中写的是 type，需要 alias
    default: Optional[str] = None
    assert_: Optional[str] = Field(None, alias="assert")
    permissions: Optional[FieldPermission] = None

    model_config = ConfigDict(populate_by_name=True)


class TableSchema(BaseModel):
    """完整的 SurrealDB 表结构定义"""
    table: str
    drop: Optional[bool] = False
    define: Optional[bool] = True
    permissions: Optional[TablePermissions] = None
    fields: List[TableField]
