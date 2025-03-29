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
        
        # 使用索引而不是循環器來實現順序輪詢
        if isinstance(self.paid_key, list) and self.paid_key:
            self.paid_key_index = 0
            self.paid_key_lock = asyncio.Lock()
            # 同時追蹤付費鍵的失敗次數
            self.paid_key_failure_counts: Dict[str, int] = {key: 0 for key in self.paid_key}
            # 添加付費鍵的調用次數計數器
            self.paid_key_usage_counts: Dict[str, int] = {key: 0 for key in self.paid_key}
        else:
            # 兼容原來的字符串類型
            self.paid_key_index = -1
            self.paid_key_lock = None
            self.paid_key_failure_counts = {}
<<<<<<< HEAD
            self.paid_key_usage_counts = {}
            if isinstance(self.paid_key, str) and self.paid_key:
                self.paid_key_usage_counts[self.paid_key] = 0
=======
        
        # 為了確保同一個請求使用同一個密鑰，使用字典記錄已分配的密鑰
        self.request_key_map = {}
>>>>>>> e037c4c27fccf4abbe91c3a32b3af5094eade273

    async def get_paid_key(self, request_id=None) -> str:
        """
        獲取一個付費 API 密鑰，按照順序從列表中取出
        
        Args:
            request_id: 可選的請求 ID，用於確保同一請求獲取相同的密鑰
        """
<<<<<<< HEAD
        selected_key = ""
        # 如果付費鍵是列表並且有設置輪詢器，則使用輪詢方式獲取
        if self.paid_key_cycle is not None:
            async with self.paid_key_cycle_lock:
                selected_key = next(self.paid_key_cycle)
=======
        # 如果提供了請求 ID 且已經為該請求分配了密鑰，則返回之前分配的密鑰
        if request_id and request_id in self.request_key_map:
            key = self.request_key_map[request_id]
            logger.info(f"使用已分配的付費密鑰: {key} (請求ID: {request_id})")
            return key
        
        # 如果付費鍵是列表並且不為空
        if isinstance(self.paid_key, list) and self.paid_key:
            async with self.paid_key_lock:
                # 如果列表只有一個元素，直接返回
                if len(self.paid_key) == 1:
                    key = self.paid_key[0]
                    if request_id:
                        self.request_key_map[request_id] = key
                    return key
                
                # 獲取當前索引對應的密鑰
                key = self.paid_key[self.paid_key_index]
                # 更新索引，到達列表尾部時重置為0
                self.paid_key_index = (self.paid_key_index + 1) % len(self.paid_key)
                
                # 如果提供了請求 ID，則記錄該請求使用的密鑰
                if request_id:
                    self.request_key_map[request_id] = key
                    
                logger.info(f"使用付費密鑰: {key}，下一個索引位置: {self.paid_key_index}")
                return key
>>>>>>> e037c4c27fccf4abbe91c3a32b3af5094eade273
        # 兼容原來的字符串類型
        elif isinstance(self.paid_key, str):
            selected_key = self.paid_key
        # 如果付費鍵是空列表，返回空字符串
        else:
            return ""
            
<<<<<<< HEAD
        return selected_key

    async def increment_paid_key_usage(self, key: str) -> None:
        """
        增加特定付費密鑰的使用計數
        """
        if not key:
            return
            
        async with self.failure_count_lock:  # 重用現有的鎖以避免競爭條件
            if key in self.paid_key_usage_counts:
                self.paid_key_usage_counts[key] += 1
            else:
                # 如果是第一次使用這個密鑰，初始化計數器
                self.paid_key_usage_counts[key] = 1
                
        logger.info(f"Paid key {key} usage count: {self.paid_key_usage_counts.get(key, 0)}")

    async def get_paid_keys_usage(self) -> Dict[str, int]:
        """
        獲取所有付費密鑰的使用統計
        """
        async with self.failure_count_lock:
            # 返回一個副本以避免並發修改問題
            return dict(self.paid_key_usage_counts)
=======
    def release_paid_key(self, request_id):
        """釋放與請求相關聯的付費密鑰"""
        if request_id in self.request_key_map:
            del self.request_key_map[request_id]
            logger.info(f"釋放請求 {request_id} 的付費密鑰")
>>>>>>> e037c4c27fccf4abbe91c3a32b3af5094eade273

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
