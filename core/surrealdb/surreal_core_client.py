# core/surrealdb/surreal_core_client.py

from __future__ import annotations

"""core.surrealdb.surreal_core_client
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
最底层 SurrealDB 连接封装，只负责两件事：

1. 与官方 **AsyncSurreal** SDK 完全同构的 *连接 / 鉴权 / 关闭* 生命周期。
2. 对 `query()` 做最薄一层错误包装，保持上层调用一致性。

遵循 *大道至简* ：不拼 SQL、不含重试、不做 DDL/DML 语义，
只保障一条稳定、可复用的 WebSocket 管线。
此为最终定版。
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

from surrealdb import AsyncSurreal

__all__ = [
    "SurrealCoreClientError",
    "SurrealCoreClient",
]

logger = logging.getLogger("core.surrealdb.core")


class SurrealCoreClientError(RuntimeError):
    """所有核心客户端层异常的基类——上层可捕获此类并做统一处理。"""


class SurrealCoreClient:  # pylint: disable=too-few-public-methods
    """與官方 SDK 一致的核心客户端。

    Parameters
    ----------
    endpoint: str
        SurrealDB WebSocket 端点，支持传入含/不含 ``/rpc`` 后缀，
        会自动校正为合法 WebSocket URL。
    namespace: str
    database: str
    username: str
    password: str
    """

    _RPC_SUFFIX = "/rpc"

    def __init__(
        self,
        *,
        endpoint: str,
        namespace: str,
        database: str,
        username: str,
        password: str,
    ) -> None:
        """初始化客户端，并规范化URL。"""
        endpoint = endpoint.rstrip("/")
        if not endpoint.endswith(self._RPC_SUFFIX):
            endpoint += self._RPC_SUFFIX
        # http -> ws 协议映射
        endpoint = endpoint.replace("http://", "ws://").replace("https://", "wss://")

        self._endpoint = endpoint
        self._namespace = namespace
        self._database = database
        self._username = username
        self._password = password

        self._db: Optional[AsyncSurreal] = None
        self._connect_lock = asyncio.Lock()
        self._last_success_ts = 0.0

    # ---------------------------------------------------------------------
    # Public context‑manager helpers
    # ---------------------------------------------------------------------
    async def __aenter__(self) -> "SurrealCoreClient":
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb):  # noqa: D401
        await self.close()
        return False  # Never swallow exceptions

    # ------------------------------------------------------------------
    # Core lifecycle
    # ------------------------------------------------------------------
    async def connect(self) -> None:
        """建立与数据库的连接，此操作是幂等的且协程安全。"""
        if self._db is not None:
            return  # Fast‑path：已连接

        async with self._connect_lock:
            if self._db is not None:  # 另一个协程已经连上
                return
            try:
                logger.info("🔌 正在连接 SurrealDB ⇒ %s", self._endpoint)
                db = AsyncSurreal(self._endpoint)

                # —— Auth & context ——
                await db.signin({"username": self._username, "password": self._password})
                await db.use(self._namespace, self._database)

                self._db = db
                self._last_success_ts = time.time()
                logger.info("✅ SurrealDB 已连接: ns=%s db=%s", self._namespace, self._database)
            except Exception as exc:  # pragma: no cover – 封装所有异常
                self._db = None
                raise SurrealCoreClientError(f"无法连接或鉴权 SurrealDB: {exc}") from exc

    async def close(self) -> None:
        """关闭 WebSocket 连接并重置状态。"""
        if self._db is not None:
            try:
                await self._db.close()
                logger.debug("🔒 SurrealDB 连接已关闭")
            finally:
                self._db = None

    # ------------------------------------------------------------------
    # Query wrapper (核心微调区域)
    # ------------------------------------------------------------------
    async def query(self, sql: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        执行 SurrealQL / SQL，并对返回错误做最薄、但最敏锐的包装。
        此方法已升级，可接收 `params` 字典以支持安全的参数化查询。
        """
        if not self._db:
            await self.connect()

        assert self._db is not None, "数据库未连接，这是一个不应发生的内部状态错误。"

        # 日志记录更加“温润”，能感知并显示参数
        if params:
            logger.debug("➡️  SQL: %s | PARAMS: %s", sql.strip(), params)
        else:
            logger.debug("➡️  SQL: %s", sql.strip())

        try:
            # 将 sql 和 params 一同传递给 SDK，实现参数化查询
            result = await self._db.query(sql, params)
        except Exception as exc:
            logger.error("❌ 查询在 SDK 层面失败: %s", exc)
            raise SurrealCoreClientError(f"查询执行失败: {exc}") from exc

        # 对 SurrealDB 返回结果的错误状态检查，此为玉之内核，亦需“秋毫之察”
        if isinstance(result, list):
            for item in result:
                # 检查1：官方标准的 status: "ERR" 错误
                if isinstance(item, dict) and item.get("status") == "ERR":
                    err_msg = item.get('result', '未知错误')
                    logger.error("❌ SurrealDB 返回“官话”错误状态: %s", err_msg)
                    raise SurrealCoreClientError(f"SurrealDB 错误: {err_msg}")
                
                # 检查2 (微调)：对数据验证类等纯文本“俚语”错误的检查
                if isinstance(item, str) and (
                    "error" in item.lower() 
                    or "found none for field" in item.lower()
                    or "problem with the database" in item.lower()
                ):
                    logger.error("❌ SurrealDB 返回纯文本错误信息: %s", item)
                    raise SurrealCoreClientError(f"SurrealDB 隐式错误: {item}")


        logger.debug("⬅️  Result: %s", result)
        return result

    # ------------------------------------------------------------------
    # Exposed property
    # ------------------------------------------------------------------
    @property
    def sdk(self) -> AsyncSurreal:
        """底层 SDK 直通，可做高级操作 (如 live 查询)。"""
        if self._db is None:
            raise SurrealCoreClientError("SDK尚未连接，无法访问")
        return self._db