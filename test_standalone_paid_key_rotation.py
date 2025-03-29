#!/usr/bin/env python3
import asyncio
import sys
import os
from itertools import cycle
from typing import Dict, List, Any

class MockSettings:
    """模擬設置對象"""
    def __init__(self):
        self.API_KEYS = ["mock-api-key-1", "mock-api-key-2"]
        self.PAID_KEY = ["mock-paid-key-1", "mock-paid-key-2", "mock-paid-key-3"]

class MockKeyManager:
    """模擬KeyManager類"""
    def __init__(self, api_keys: list):
        self.api_keys = api_keys
        self.key_cycle = cycle(api_keys)
        self.key_cycle_lock = asyncio.Lock()
        self.paid_key = MockSettings().PAID_KEY
        
        # 初始化付費密鑰循環器
        if isinstance(self.paid_key, list) and self.paid_key:
            self.paid_key_cycle = cycle(self.paid_key)
            self.paid_key_cycle_lock = asyncio.Lock()

    async def get_paid_key(self) -> str:
        """獲取一個付費密鑰"""
        if isinstance(self.paid_key, list) and self.paid_key:
            async with self.paid_key_cycle_lock:
                return next(self.paid_key_cycle)
        elif isinstance(self.paid_key, str):
            return self.paid_key
        else:
            return ""

class MockImageService:
    """模擬圖像服務類"""
    def __init__(self, key_manager: MockKeyManager):
        self.key_manager = key_manager
    
    async def get_paid_key(self) -> str:
        """獲取付費密鑰"""
        return await self.key_manager.get_paid_key()

async def test_standalone_paid_key_rotation():
    """測試付費密鑰輪詢功能的獨立測試"""
    print("開始測試付費密鑰輪詢功能（獨立版本）...")
    
    # 創建模擬的API密鑰和付費密鑰
    mock_settings = MockSettings()
    api_keys = mock_settings.API_KEYS
    paid_keys = mock_settings.PAID_KEY
    
    print(f"模擬的API密鑰: {api_keys}")
    print(f"模擬的付費密鑰: {paid_keys}")
    
    # 初始化模擬的KeyManager
    key_manager = MockKeyManager(api_keys)
    
    # 測試KeyManager的get_paid_key方法
    print("\n測試KeyManager的get_paid_key方法:")
    km_results = []
    
    for i in range(len(paid_keys) * 2):  # 調用多次以觀察輪詢效果
        key = await key_manager.get_paid_key()
        km_results.append(key)
        print(f"第 {i+1} 次獲取: {key}")
    
    # 初始化模擬的圖像服務
    image_service = MockImageService(key_manager)
    
    # 測試圖像服務的get_paid_key方法
    print("\n測試ImageService的get_paid_key方法:")
    is_results = []
    
    for i in range(len(paid_keys) * 2):
        key = await image_service.get_paid_key()
        is_results.append(key)
        print(f"第 {i+1} 次獲取: {key}")
    
    # 驗證KeyManager輪詢結果
    is_km_rotating = True
    for i in range(len(paid_keys)):
        if km_results[i] != km_results[i + len(paid_keys)]:
            is_km_rotating = False
            break
    
    if is_km_rotating:
        print("\n✅ 測試通過: KeyManager正確輪詢付費密鑰")
    else:
        print("\n❌ 測試失敗: KeyManager未按預期輪詢付費密鑰")
    
    # 驗證ImageService輪詢結果
    is_is_rotating = True
    for i in range(len(paid_keys)):
        if is_results[i] != is_results[i + len(paid_keys)]:
            is_is_rotating = False
            break
    
    if is_is_rotating:
        print("✅ 測試通過: ImageService正確輪詢付費密鑰")
    else:
        print("❌ 測試失敗: ImageService未按預期輪詢付費密鑰")
    
    # 驗證兩者是否一致
    if km_results == is_results:
        print("✅ 測試通過: KeyManager和ImageService獲取的密鑰序列一致")
    else:
        print("❌ 測試失敗: KeyManager和ImageService獲取的密鑰序列不一致")

async def main():
    await test_standalone_paid_key_rotation()

if __name__ == "__main__":
    asyncio.run(main()) 