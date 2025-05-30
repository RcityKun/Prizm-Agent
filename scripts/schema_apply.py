from __future__ import annotations

"""scripts.schema_apply
~~~~~~~~~~~~~~~~~~~~~~~
CLI 入口：一键 *加载 → 校验 → 注入* YAML schema 到 SurrealDB。

> 设计原则：
> 1. **零硬编码** – 一切连接参数来自环境变量或 CLI 参数。
> 2. **零副作用** – 不修改 `sys.path`；以包导入保证可测试性。
> 3. **零阻塞** – 全链路 async / await。
"""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import List

from dotenv import load_dotenv

# ----------------------------------------------------------------------
# Early logging (可由 CLI --log-level 覆盖) -----------------------------
# ----------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("scripts.schema_apply")

# ----------------------------------------------------------------------
# 自动添加项目根路径 --------------------------------------------------
# ----------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# ----------------------------------------------------------------------
# Import internal libs --------------------------------------------------
# ----------------------------------------------------------------------
try:
    from core.surrealdb.surreal_driver import SurrealDriver
    from core.surrealdb.schema_loader import load_schemas
    from core.surrealdb.schema_model import TableSchema
except ModuleNotFoundError as exc:
    logger.critical("❌ Unable to import core package: %s", exc)
    sys.exit(1)

# ----------------------------------------------------------------------
# CLI -------------------------------------------------------------------
# ----------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:  # noqa: D401
    parser = argparse.ArgumentParser(description="Apply YAML schemas to SurrealDB")
    parser.add_argument(
        "--schemas-root",
        type=Path,
        default=None,
        help="Root directory containing YAML schemas (default: core/surrealdb/schemas)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    )
    return parser.parse_args()

# ----------------------------------------------------------------------
# Main ------------------------------------------------------------------
# ----------------------------------------------------------------------
async def _apply_schemas(schemas: List[TableSchema], driver: SurrealDriver) -> None:
    success, failed = 0, 0
    for schema in schemas:
        try:
            await driver.inject_schema_from_yaml(schema.model_dump())
            logger.info("✅ Injected table: %s", schema.table)
            success += 1
        except Exception as exc:  # pragma: no cover – 粗粒度捕获即可
            logger.error("❌ Inject failed for %s: %s", schema.table, exc)
            failed += 1
    logger.info("🎉 Applied schemas – success=%s failed=%s", success, failed)
    if success == 0:
        raise SystemExit(1)

def main() -> None:  # noqa: D401
    args = _parse_args()
    logging.getLogger().setLevel(args.log_level)

    # 1. .env -----------------------------------------------------------
    load_dotenv()

    # 2. Config from env -----------------------------------------------
    endpoint = os.getenv("SURREALDB_ENDPOINT", "ws://localhost:8000/rpc")
    namespace = os.getenv("SURREALDB_NAMESPACE", "test_namespace")
    database = os.getenv("SURREALDB_DATABASE", "test_db")
    user = os.getenv("SURREALDB_USER", "root")
    password = os.getenv("SURREALDB_PASSWORD", "root")

    if logging.getLogger().isEnabledFor(logging.DEBUG):
        logger.debug("Endpoint=%s ns=%s db=%s user=%s", endpoint, namespace, database, user)

    # 3. Run async workflow -------------------------------------------
    async def _workflow() -> None:
        async with SurrealDriver(
            endpoint=endpoint,
            namespace=namespace,
            database=database,
            user=user,
            password=password,
        ) as driver:
            schemas = await load_schemas(args.schemas_root)
            if not schemas:
                logger.warning("No schema found – nothing to do")
                return
            await _apply_schemas(schemas, driver)

    asyncio.run(_workflow())

if __name__ == "__main__":
    main()
