import asyncio
from itertools import cycle
from typing import Dict, List

from app.config.config import settings
from app.log.logger import get_key_manager_logger

logger = get_key_manager_logger()


class KeyManager:
    def __init__(self, api_keys: list):
        self.api_keys = api_keys
        self.key_cycle = cycle(api_keys)
        self.key_cycle_lock = asyncio.Lock()
        self.failure_count_lock = asyncio.Lock()
        self.key_failure_counts: Dict[str, int] = {key: 0 for key in api_keys}
        self.MAX_FAILURES = settings.MAX_FAILURES
        self.paid_key = settings.PAID_KEY
        # 如果付費鍵是列表且不為空，創建付費鍵的輪詢器
        if isinstance(self.paid_key, list) and self.paid_key:
            self.paid_key_cycle = cycle(self.paid_key)
            self.paid_key_cycle_lock = asyncio.Lock()
            # 同時追蹤付費鍵的失敗次數
            self.paid_key_failure_counts: Dict[str, int] = {key: 0 for key in self.paid_key}
        else:
            # 兼容原來的字符串類型
            self.paid_key_cycle = None
            self.paid_key_cycle_lock = None
            self.paid_key_failure_counts = {}

    async def get_paid_key(self) -> str:
        """
        獲取一個付費 API 密鑰，如果配置為列表則循環使用
        """
        # 如果付費鍵是列表並且有設置輪詢器，則使用輪詢方式獲取
        if self.paid_key_cycle is not None:
            async with self.paid_key_cycle_lock:
                return next(self.paid_key_cycle)
        # 兼容原來的字符串類型
        elif isinstance(self.paid_key, str):
            return self.paid_key
        # 如果付費鍵是空列表，返回空字符串
        else:
            return ""

    async def get_next_key(self) -> str:
        """获取下一个API key"""
        async with self.key_cycle_lock:
            return next(self.key_cycle)

    async def is_key_valid(self, key: str) -> bool:
        """检查key是否有效"""
        async with self.failure_count_lock:
            return self.key_failure_counts[key] < self.MAX_FAILURES

    async def reset_failure_counts(self):
        """重置所有key的失败计数"""
        async with self.failure_count_lock:
            for key in self.key_failure_counts:
                self.key_failure_counts[key] = 0

    async def get_next_working_key(self) -> str:
        """获取下一可用的API key"""
        initial_key = await self.get_next_key()
        current_key = initial_key

        while True:
            if await self.is_key_valid(current_key):
                return current_key

            current_key = await self.get_next_key()
            if current_key == initial_key:
                # await self.reset_failure_counts() 取消重置
                return current_key

    async def handle_api_failure(self, api_key: str) -> str:
        """处理API调用失败"""
        async with self.failure_count_lock:
            self.key_failure_counts[api_key] += 1
            if self.key_failure_counts[api_key] >= self.MAX_FAILURES:
                logger.warning(
                    f"API key {api_key} has failed {self.MAX_FAILURES} times"
                )

        return await self.get_next_working_key()

    def get_fail_count(self, key: str) -> int:
        """获取指定密钥的失败次数"""
        return self.key_failure_counts.get(key, 0)

    async def get_keys_by_status(self) -> dict:
        """获取分类后的API key列表，包括失败次数"""
        valid_keys = {}
        invalid_keys = {}

        async with self.failure_count_lock:
            for key in self.api_keys:
                fail_count = self.key_failure_counts[key]
                if fail_count < self.MAX_FAILURES:
                    valid_keys[key] = fail_count
                else:
                    invalid_keys[key] = fail_count

        return {"valid_keys": valid_keys, "invalid_keys": invalid_keys}


_singleton_instance = None
_singleton_lock = asyncio.Lock()


async def get_key_manager_instance(api_keys: list = None) -> KeyManager:
    """
    获取 KeyManager 单例实例。

    如果尚未创建实例，将使用提供的 api_keys 初始化 KeyManager。
    如果已创建实例，则忽略 api_keys 参数，返回现有单例。
    """
    global _singleton_instance

    async with _singleton_lock:
        if _singleton_instance is None:
            if api_keys is None:
                raise ValueError("API keys are required to initialize the KeyManager")
            _singleton_instance = KeyManager(api_keys)
        return _singleton_instance
