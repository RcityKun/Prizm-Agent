# core/surrealdb/surreal_driver.py

from __future__ import annotations

"""core.surrealdb.surreal_driver
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
高层 *Driver* —— 在不违背官方 SDK 的前提下，为彩虹城提供：

1. **单一重试** 逻辑（指数退避，可配置）。
2. **DDL / Schema 指令**：`define_table` 与 `inject_schema_from_yaml`。
3. **最小 CRUD**：`select`, `insert`, `update`, `delete`（便于上层快速调用）。

此为收官之作，融合了系统建制思想，遵循道法自然、万法归宗。
"""

import asyncio
import logging
from collections.abc import Mapping, Sequence
from typing import Any, Dict, Set

from .surreal_core_client import SurrealCoreClient, SurrealCoreClientError

__all__ = [
    "SurrealDriverError",
    "SurrealDriver",
]

logger = logging.getLogger("core.surrealdb.driver")


class SurrealDriverError(RuntimeError):
    """Driver 层异常。"""


class SurrealDriver:
    """面向业务的高层封装，遵循大道至简、上善若水、温润如玉的设计哲学。"""

    # “立规矩，成方圆”：预定义合法的 SurrealDB 类型集合，是为“玉石之盾”
    _VALID_SURREAL_TYPES: Set[str] = {
        "any", "string", "number", "int", "float", "bool", "datetime", 
        "duration", "decimal", "object", "array", "record", "geometry",
        # 也可以加入自定义的 record 类型，如 "record<user>"
    }

    def __init__(
        self,
        *,
        endpoint: str,
        namespace: str,
        database: str,
        user: str,
        password: str,
        max_retries: int = 3,
        backoff_base: float = 1.0,
    ) -> None:
        """初始化 Driver 实例。"""
        self._client = SurrealCoreClient(
            endpoint=endpoint,
            namespace=namespace,
            database=database,
            username=user,
            password=password,
        )
        self._max_retries = max_retries
        self._backoff_base = max(0.1, backoff_base)

    # ------------------------------------------------------------------
    # Context helpers: 管理连接生命周期，如水之来去，自然而然
    # ------------------------------------------------------------------
    async def __aenter__(self) -> "SurrealDriver":
        await self._client.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self._client.close()
        return False

    # ------------------------------------------------------------------
    # Query with single retry layer: 遇阻则退，再试则进，坚韧如水
    # ------------------------------------------------------------------
    async def query(self, sql: str, params: Dict[str, Any] | None = None) -> Any:
        """
        执行任意 SurrealQL，带可配置重试。
        支持参数化查询以防止 SQL 注入。
        """
        for attempt in range(1, self._max_retries + 1):
            try:
                return await self._client.query(sql, params)
            except SurrealCoreClientError as exc:
                if "Parse error" in str(exc):
                    logger.error("❌ 查询因语法错误而失败，无需重试: %s", exc)
                    raise SurrealDriverError(f"Query failed with a syntax error: {exc}") from exc

                if attempt >= self._max_retries:
                    logger.error("❌ 查询在 %s 次尝试后最终失败: %s", attempt, exc)
                    raise SurrealDriverError(f"Query failed after {attempt} attempts: {exc}") from exc

                wait_time = self._backoff_base * 2 ** (attempt - 1)
                logger.warning(
                    "⚠️ 查询失败，将在 %.2f 秒后进行第 %s/%s 次重试...",
                    wait_time,
                    attempt,
                    self._max_retries,
                )
                await asyncio.sleep(wait_time)
        return None  # Should be unreachable

    # ------------------------------------------------------------------
    # Minimal CRUD helpers: 简明扼要，直达本质 (包含最终微调)
    # ------------------------------------------------------------------
    async def select(self, table: str, *, limit: int | None = None) -> Any:
        sql = f"SELECT * FROM {table};"
        return await self.query(sql)

    async def insert(self, target: str, data: Mapping[str, Any]) -> Any:
        """
        智能插入/创建方法，是为“顺势而为”。
        - 如果 target 包含 ':', 则视为 Record ID (如 "user:1"), 使用 CREATE 语句。
        - 如果 target 不包含 ':', 则视为 Table Name (如 "user"), 使用 INSERT INTO 语句。
        """
        if ":" in target:
            # 目标是指定ID的记录 -> 使用 CREATE
            sql = f"CREATE {target} CONTENT $data;"
        else:
            # 目标是表 -> 使用 INSERT INTO, 让数据库生成ID
            sql = f"INSERT INTO {target} CONTENT $data;"
            
        return await self.query(sql, {"data": data})

    async def update(self, table: str, data: Mapping[str, Any]) -> Any:
        sql = f"UPDATE {table} CONTENT $data;"
        return await self.query(sql, {"data": data})

    async def delete(self, table: str) -> Any:
        return await self.query(f"DELETE FROM {table};")

    # ------------------------------------------------------------------
    # DDL helpers: 万法归宗，神韵合一
    # ------------------------------------------------------------------
    async def _define_permissions(
        self, table: str, permissions: Mapping[str, str] | None
    ) -> None:
        """私有辅助方法：以幂等方式定义权限 (职责分离，大道至简)。"""
        for action, clause in (permissions or {}).items():
            action_upper = action.upper()
            logger.debug("为表 %s 定义权限: FOR %s", table, action_upper)
            perm_sql = f"DEFINE PERMISSIONS FOR {action_upper} ON {table} WHERE {clause};"
            try:
                await self.query(perm_sql)
            except SurrealDriverError as exc:
                if "already exists" in str(exc).lower():
                    logger.debug("权限 FOR %s ON %s 已存在，跳过。", action_upper, table)
                else:
                    logger.error("❌ 定义权限时发生意外错误: %s", exc)
                    raise

    async def define_table(
        self,
        table: str,
        *,
        fields: Sequence[Dict[str, str]] | None = None,
        permissions: Mapping[str, str] | None = None,
    ) -> None:
        """
        以幂等方式定义表、字段和权限，兼容 SurrealDB v2.x 语法。
        """
        # 1. TABLE: “以不变应万变”，发送最基础的指令
        logger.debug("定义表: %s", table)
        try:
            await self.query(f"DEFINE TABLE {table};")
        except SurrealDriverError as exc:
            if "already exists" in str(exc).lower():
                logger.debug("表 %s 已存在，此为常态，顺势跳过。", table)
            else:
                logger.error("❌ 定义表 %s 时发生未知错误: %s", table, exc)
                raise

        # 2. FIELDS: “固本清源”，统一采用 try/except 模式
        for field_def in fields or []:
            field_name = field_def.get("name")
            field_type = field_def.get("data_type")

            if not field_name or not field_type:
                logger.warning("⚠️ 在表 %s 的定义中发现不完整的字段，已跳过: %s", table, field_def)
                continue
            
            # “玉石之盾”：在入口处验证类型合法性
            if field_type not in self._VALID_SURREAL_TYPES:
                logger.warning("⚠️ 字段 %s.%s 类型 '%s' 非法，已跳过。", table, field_name, field_type)
                continue

            logger.debug("为表 %s 定义字段: %s", table, field_name)
            field_sql = f"DEFINE FIELD `{field_name}` ON TABLE {table} TYPE {field_type};"
            try:
                await self.query(field_sql)
            except SurrealDriverError as exc:
                if "already exists" in str(exc).lower():
                    logger.debug("字段 %s.%s 已存在，跳过。", table, field_name)
                else:
                    logger.error("❌ 定义字段 %s.%s 时发生未知错误: %s", table, field_name, exc)
                    raise
        
        # 3. PERMISSIONS: “分治之术”，调用独立方法处理
        await self._define_permissions(table, permissions)

    # ------------------------------------------------------------------
    # YAML injection: 统合综效，将 schema 定义注入数据库
    # ------------------------------------------------------------------
    async def inject_schema_from_yaml(self, schema: Mapping[str, Any]) -> None:
        """从解析后的 YAML 数据中，注入一个完整的表定义。"""
        table_name = schema.get("table")
        if not table_name:
            raise SurrealDriverError("Schema 定义缺失 'table' 键，无法注入。")
        
        # “秋毫之察”与“远见之光”：记录版本信息，为未来演化奠基
        schema_version = schema.get("version", "未指定")
        logger.debug("准备注入 Schema: %s, 版本: %s", table_name, schema_version)

        # TODO: (道法自然) 此处可扩展版本比对逻辑。
        # 例如，从数据库某次元数据表读取当前版本，
        # 只有当 schema_version 高于当前版本时，才执行注入。
        # `if schema_version > current_db_version:`

        await self.define_table(
            table=table_name,
            fields=schema.get("fields"),
            permissions=schema.get("permissions"),
        )
        logger.info("✅ Schema v%s 注入成功: %s", schema_version, table_name)