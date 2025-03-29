#!/usr/bin/env python3
import asyncio
import sys
import os
from typing import Dict, List, Any

# 添加專案根目錄到Python路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class MockLogger:
    """模擬記錄器"""
    def info(self, message):
        print(f"[INFO] {message}")
    
    def warning(self, message):
        print(f"[WARNING] {message}")

class MockKeyManager:
    """模擬修改後的KeyManager類"""
    def __init__(self, api_keys: list, paid_keys: list):
        self.api_keys = api_keys
        self.key_cycle_lock = asyncio.Lock()
        self.failure_count_lock = asyncio.Lock()
        self.key_failure_counts = {key: 0 for key in api_keys}
        self.MAX_FAILURES = 3
        self.paid_key = paid_keys
        self.logger = MockLogger()
        
        # 使用索引而不是循環器來實現順序輪詢
        if isinstance(self.paid_key, list) and self.paid_key:
            self.paid_key_index = 0
            self.paid_key_lock = asyncio.Lock()
            self.paid_key_failure_counts = {key: 0 for key in self.paid_key}
        else:
            self.paid_key_index = -1
            self.paid_key_lock = None
            self.paid_key_failure_counts = {}

    async def get_paid_key(self) -> str:
        """獲取一個付費 API 密鑰，按照順序從列表中取出"""
        # 如果付費鍵是列表並且不為空
        if isinstance(self.paid_key, list) and self.paid_key:
            async with self.paid_key_lock:
                # 獲取當前索引對應的密鑰
                key = self.paid_key[self.paid_key_index]
                # 更新索引，到達列表尾部時重置為0
                self.paid_key_index = (self.paid_key_index + 1) % len(self.paid_key)
                self.logger.info(f"使用付費密鑰: {key}，下一個索引位置: {self.paid_key_index}")
                return key
        # 兼容原來的字符串類型
        elif isinstance(self.paid_key, str):
            return self.paid_key
        # 如果付費鍵是空列表，返回空字符串
        else:
            return ""

class MockImageService:
    """模擬圖像服務類"""
    def __init__(self, key_manager):
        self.key_manager = key_manager
    
    async def get_paid_key(self) -> str:
        """獲取付費密鑰"""
        return await self.key_manager.get_paid_key()

async def test_sequential_paid_key_rotation():
    """測試順序輪詢付費密鑰功能"""
    print("開始測試順序輪詢付費密鑰功能...")
    
    # 創建測試用的API鍵和付費密鑰列表
    api_keys = ["api-key-1", "api-key-2"]
    paid_keys = ["paid-key-1", "paid-key-2", "paid-key-3"]
    
    print(f"API密鑰: {api_keys}")
    print(f"付費密鑰: {paid_keys}")
    
    # 初始化KeyManager
    key_manager = MockKeyManager(api_keys, paid_keys)
    
    # 測試順序輪詢
    print("\n1. 測試KeyManager順序輪詢:")
    km_results = []
    
    # 調用多次，觀察多於一輪的輪詢
    total_calls = len(paid_keys) * 3
    for i in range(total_calls):
        key = await key_manager.get_paid_key()
        km_results.append(key)
        print(f"  第 {i+1} 次獲取: {key}")
    
    # 驗證是否按照順序輪詢
    is_sequential = True
    for i in range(total_calls):
        expected_key = paid_keys[i % len(paid_keys)]
        if km_results[i] != expected_key:
            is_sequential = False
            print(f"  ❌ 第 {i+1} 次輪詢失敗: 期望 {expected_key}, 實際 {km_results[i]}")
            break
    
    if is_sequential:
        print("  ✅ 順序輪詢測試通過: 密鑰按照正確順序輪詢")
    else:
        print("  ❌ 順序輪詢測試失敗")
    
    # 測試通過圖像服務獲取密鑰
    print("\n2. 測試通過ImageService獲取付費密鑰:")
    image_service = MockImageService(key_manager)
    is_results = []
    
    for i in range(len(paid_keys) * 2):
        key = await image_service.get_paid_key()
        is_results.append(key)
        print(f"  第 {i+1} 次獲取: {key}")
    
    # 驗證是否按照順序輪詢
    is_service_sequential = True
    for i in range(len(paid_keys) * 2):
        expected_key = paid_keys[i % len(paid_keys)]
        if is_results[i] != expected_key:
            is_service_sequential = False
            print(f"  ❌ 第 {i+1} 次輪詢失敗: 期望 {expected_key}, 實際 {is_results[i]}")
            break
    
    if is_service_sequential:
        print("  ✅ 服務順序輪詢測試通過: 密鑰按照正確順序輪詢")
    else:
        print("  ❌ 服務順序輪詢測試失敗")
    
    # 測試索引重置
    print("\n3. 測試索引重置:")
    
    # 手動設置索引
    async with key_manager.paid_key_lock:
        key_manager.paid_key_index = len(paid_keys) - 1
        print(f"  手動設置索引為 {key_manager.paid_key_index}，對應密鑰 {paid_keys[key_manager.paid_key_index]}")
    
    # 獲取密鑰，應該獲取最後一個密鑰
    key = await key_manager.get_paid_key()
    print(f"  獲取密鑰: {key}，期望: {paid_keys[len(paid_keys)-1]}")
    
    # 再次獲取密鑰，應該回到第一個密鑰
    key = await key_manager.get_paid_key()
    print(f"  獲取密鑰: {key}，期望: {paid_keys[0]} (索引重置)")
    
    if key == paid_keys[0]:
        print("  ✅ 索引重置測試通過: 索引正確重置為0")
    else:
        print(f"  ❌ 索引重置測試失敗: 期望 {paid_keys[0]}, 實際 {key}")
    
    print("\n所有測試完成!")

async def main():
    await test_sequential_paid_key_rotation()

if __name__ == "__main__":
    asyncio.run(main()) 