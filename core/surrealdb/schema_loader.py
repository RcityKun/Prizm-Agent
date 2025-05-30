from __future__ import annotations

"""
core.surrealdb.schema_loader
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
异步读取 YAML schema 文件并解析为 TableSchema 实例。

功能目标：
- 遍历指定根目录（默认：core/surrealdb/schemas）下所有 `.yaml`/`.yml` 文件
- 跳过空文件或格式非法者
- 保证 alias 字段（如 type → data_type）在载入过程中正确映射
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import List, Optional

import yaml
from pydantic import ValidationError

from core.surrealdb.schema_model import TableSchema

logger = logging.getLogger("core.schema_loader")


async def load_schemas(root: Optional[Path] = None) -> List[TableSchema]:
    """从给定目录递归加载所有 schema YAML 文件"""
    schemas: List[TableSchema] = []

    root_dir = root or Path(__file__).parent / "schemas"
    root_dir = root_dir.resolve()
    logger.debug("🔍 正在搜索 schema 文件目录: %s", root_dir)

    if not root_dir.exists() or not root_dir.is_dir():
        logger.warning("⚠️ schema 根目录不存在: %s", root_dir)
        return []

    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if not filename.endswith((".yaml", ".yml")):
                continue

            path = Path(dirpath) / filename
            try:
                content = await asyncio.to_thread(path.read_text, encoding="utf-8")
                if not content.strip():
                    logger.warning("⚠️ 空文件跳过: %s", path.name)
                    continue

                raw = yaml.safe_load(content)
                if not isinstance(raw, dict):
                    logger.warning("⚠️ 非 dict YAML 跳过: %s", path.name)
                    continue

                # 自动推断表名（如 user.yaml → table: user）
                raw.setdefault("table", path.stem)

                # 校验字段结构：必须是 dict，必须包含 name，必须包含 type 或 data_type
                fields = raw.get("fields", [])
                valid_fields = []
                for i, field in enumerate(fields):
                    if not isinstance(field, dict):
                        logger.error("❌ 字段格式错误 (非 dict): %s\n  ➤ 文件: %s", field, path.name)
                        continue

                    if "name" not in field or ("type" not in field and "data_type" not in field):
                        logger.error(
                            "❌ 字段缺失 name 或 type:\n  ➤ 字段: %s\n  ➤ 文件: %s",
                            field,
                            path.name,
                        )
                        continue

                    valid_fields.append(field)

                raw["fields"] = valid_fields
                logger.debug("🔎 当前处理字段内容: %s", valid_fields)

                # 使用 Pydantic 校验并解析（支持 alias）
                schema = TableSchema.model_validate(raw, from_attributes=True)
                schemas.append(schema)

                logger.info("📄 成功载入 schema: %s", path.relative_to(root_dir))

            except ValidationError as ve:
                logger.error("❌ schema 校验失败 (%s): %s", path.name, ve)
            except Exception as e:
                logger.error("❌ schema 加载失败 (%s): %s", path.name, e)

    return schemas
