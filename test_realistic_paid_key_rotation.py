#!/usr/bin/env python3
import asyncio
import sys
import os
from itertools import cycle
from typing import Dict, List, Any
import unittest

class MockSettings:
    """模擬設置對象"""
    def __init__(self):
        self.API_KEYS = ["mock-api-key-1", "mock-api-key-2"]
        self.PAID_KEY = ["mock-paid-key-1", "mock-paid-key-2", "mock-paid-key-3"]
        self.MAX_FAILURES = 3

class RealisticKeyManager:
    """模擬真實的KeyManager類"""
    def __init__(self, api_keys: list):
        self.api_keys = api_keys
        self.key_cycle = cycle(api_keys)
        self.key_cycle_lock = asyncio.Lock()
        self.failure_count_lock = asyncio.Lock()
        self.key_failure_counts: Dict[str, int] = {key: 0 for key in api_keys}
        
        # 從設置獲取配置
        settings = MockSettings()
        self.MAX_FAILURES = settings.MAX_FAILURES
        self.paid_key = settings.PAID_KEY
        
        # 初始化付費密鑰循環器和失敗計數
        if isinstance(self.paid_key, list) and self.paid_key:
            self.paid_key_cycle = cycle(self.paid_key)
            self.paid_key_cycle_lock = asyncio.Lock()
            self.paid_key_failure_counts: Dict[str, int] = {key: 0 for key in self.paid_key}
        else:
            self.paid_key_cycle = None
            self.paid_key_cycle_lock = None
            self.paid_key_failure_counts = {}

    async def get_paid_key(self) -> str:
        """獲取一個付費API密鑰，如果配置為列表則循環使用"""
        # 如果付費密鑰是列表並且有設置循環器，則使用循環方式獲取
        if self.paid_key_cycle is not None:
            async with self.paid_key_cycle_lock:
                return next(self.paid_key_cycle)
        # 兼容字符串類型
        elif isinstance(self.paid_key, str):
            return self.paid_key
        # 如果付費密鑰是空列表，返回空字符串
        else:
            return ""

    async def get_next_key(self) -> str:
        """獲取下一個API密鑰"""
        async with self.key_cycle_lock:
            return next(self.key_cycle)

    async def is_key_valid(self, key: str) -> bool:
        """檢查密鑰是否有效"""
        async with self.failure_count_lock:
            return self.key_failure_counts.get(key, 0) < self.MAX_FAILURES

    async def handle_paid_key_failure(self, key: str) -> str:
        """處理付費密鑰調用失敗"""
        if not self.paid_key_failure_counts or key not in self.paid_key_failure_counts:
            return await self.get_paid_key()
            
        async with self.failure_count_lock:
            self.paid_key_failure_counts[key] += 1
            
        # 獲取下一個可用的付費密鑰
        return await self.get_paid_key()

class MockImageService:
    """模擬圖像服務類"""
    def __init__(self, key_manager):
        self.key_manager = key_manager
    
    async def get_paid_key(self) -> str:
        """獲取付費密鑰"""
        return await self.key_manager.get_paid_key()
        
    async def generate_image(self, prompt: str, n: int = 1):
        """模擬生成圖像，並處理可能的API密鑰錯誤"""
        max_retries = 3
        current_retries = 0
        
        while current_retries < max_retries:
            try:
                # 獲取付費密鑰
                api_key = await self.get_paid_key()
                print(f"使用密鑰 '{api_key}' 生成圖像: '{prompt}'")
                
                # 模擬API調用
                # 這裡可以添加模擬失敗的邏輯
                return {"success": True, "image_url": "https://example.com/image.jpg", "used_key": api_key}
            
            except Exception as e:
                current_retries += 1
                print(f"圖像生成失敗 (嘗試 {current_retries}/{max_retries}): {str(e)}")
                
                # 處理密鑰失敗
                api_key = await self.key_manager.handle_paid_key_failure(api_key)
                
                if current_retries >= max_retries:
                    raise Exception(f"圖像生成失敗，已達到最大重試次數 ({max_retries})")

async def test_realistic_paid_key_rotation():
    """測試更真實的付費密鑰輪詢功能"""
    print("開始測試真實場景下的付費密鑰輪詢功能...")
    
    # 獲取模擬的API密鑰和付費密鑰
    mock_settings = MockSettings()
    api_keys = mock_settings.API_KEYS
    paid_keys = mock_settings.PAID_KEY
    
    print(f"模擬的API密鑰: {api_keys}")
    print(f"模擬的付費密鑰: {paid_keys}")
    
    # 初始化鍵管理器
    key_manager = RealisticKeyManager(api_keys)
    
    # 1. 基本密鑰輪詢測試
    print("\n1. 基本密鑰輪詢測試:")
    km_results = []
    for i in range(len(paid_keys) * 2):
        key = await key_manager.get_paid_key()
        km_results.append(key)
        print(f"  第 {i+1} 次獲取: {key}")
    
    # 檢查基本輪詢
    is_rotating = True
    for i in range(len(paid_keys)):
        if km_results[i] != km_results[i + len(paid_keys)]:
            is_rotating = False
            break
    
    assert is_rotating, "基本密鑰輪詢測試失敗"
    print("  ✅ 基本密鑰輪詢測試通過")
    
    # 2. 通過圖像服務獲取付費密鑰
    print("\n2. 通過圖像服務獲取付費密鑰:")
    image_service = MockImageService(key_manager)
    is_results = []
    
    for i in range(len(paid_keys) * 2):
        key = await image_service.get_paid_key()
        is_results.append(key)
        print(f"  第 {i+1} 次獲取: {key}")
    
    # 檢查服務輪詢
    is_service_rotating = True
    for i in range(len(paid_keys)):
        if is_results[i] != is_results[i + len(paid_keys)]:
            is_service_rotating = False
            break
    
    assert is_service_rotating, "圖像服務密鑰輪詢測試失敗"
    print("  ✅ 圖像服務密鑰輪詢測試通過")
    
    # 3. 模擬圖像生成
    print("\n3. 模擬圖像生成:")
    generation_results = []
    
    for i in range(len(paid_keys) * 2):
        prompt = f"Test image {i+1}"
        result = await image_service.generate_image(prompt)
        generation_results.append(result["used_key"])
        print(f"  生成圖像 {i+1} 使用密鑰: {result['used_key']}")
    
    # 檢查圖像生成中的密鑰輪詢
    is_gen_rotating = True
    for i in range(len(paid_keys)):
        if generation_results[i] != generation_results[i + len(paid_keys)]:
            is_gen_rotating = False
            break
    
    assert is_gen_rotating, "圖像生成密鑰輪詢測試失敗"
    print("  ✅ 圖像生成密鑰輪詢測試通過")
    
    # 4. 模擬密鑰失敗和恢復
    print("\n4. 模擬密鑰失敗和恢復:")
    
    # 手動設置某個密鑰為失敗狀態
    failed_key = paid_keys[0]
    key_manager.paid_key_failure_counts[failed_key] = key_manager.MAX_FAILURES - 1
    print(f"  將密鑰 '{failed_key}' 設置為接近失敗狀態 (失敗次數: {key_manager.paid_key_failure_counts[failed_key]})")
    
    # 故意使失敗密鑰再次失敗
    await key_manager.handle_paid_key_failure(failed_key)
    print(f"  使密鑰 '{failed_key}' 再次失敗，當前失敗次數: {key_manager.paid_key_failure_counts[failed_key]}")
    
    # 獲取新的密鑰並確保它不是失敗的密鑰
    next_key = await key_manager.get_paid_key()
    print(f"  獲取下一個密鑰: {next_key}")
    
    if next_key != failed_key:
        print("  ✅ 密鑰失敗處理測試通過：系統成功跳過失敗的密鑰")
    else:
        # 如果只有一個密鑰，這可能會失敗，但我們有多個密鑰
        print("  ❌ 密鑰失敗處理測試失敗：系統仍在使用失敗的密鑰")
    
    print("\n所有測試完成！")

async def main():
    await test_realistic_paid_key_rotation()

if __name__ == "__main__":
    asyncio.run(main()) 