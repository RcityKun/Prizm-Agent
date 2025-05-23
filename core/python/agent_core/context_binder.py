"""
上下文聚合器 - 管理和绑定各模块的上下文信息
"""
from typing import Any, Dict, Optional

class ContextBinder:
    def __init__(self):
        self._context_store: Dict[str, Any] = {}
        self._active_context: Optional[str] = None

    def bind_context(self, context_id: str, context_data: Dict[str, Any]) -> None:
        """绑定新的上下文数据"""
        self._context_store[context_id] = context_data
        self._active_context = context_id

    def get_active_context(self) -> Optional[Dict[str, Any]]:
        """获取当前活动的上下文"""
        if self._active_context:
            return self._context_store.get(self._active_context)
        return None

    def merge_contexts(self, context_ids: list[str]) -> Dict[str, Any]:
        """合并多个上下文"""
        merged = {}
        for ctx_id in context_ids:
            if ctx_id in self._context_store:
                merged.update(self._context_store[ctx_id])
        return merged

    def clear_context(self, context_id: str) -> None:
        """清除指定的上下文"""
        if context_id in self._context_store:
            del self._context_store[context_id]
            if self._active_context == context_id:
                self._active_context = None
