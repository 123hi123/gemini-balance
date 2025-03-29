#!/usr/bin/env python3
import asyncio
import sys
import os
from typing import Dict, List, Any
from unittest.mock import AsyncMock, patch, MagicMock

# 添加專案根目錄到Python路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class MockLogger:
    """模擬記錄器"""
    def info(self, message):
        print(f"[INFO] {message}")
    
    def warning(self, message):
        print(f"[WARNING] {message}")
    
    def error(self, message):
        print(f"[ERROR] {message}")

class MockSettings:
    """模擬設置對象"""
    def __init__(self):
        self.API_KEYS = ["api-key-1", "api-key-2"]
        self.PAID_KEY = ["paid-key-1", "paid-key-2", "paid-key-3"]
        self.MAX_FAILURES = 3
        self.CREATE_IMAGE_MODEL = "imagen-3.0-generate-002"

class MockKeyManager:
    """模擬修改後的KeyManager類"""
    def __init__(self):
        settings = MockSettings()
        self.api_keys = settings.API_KEYS
        self.key_cycle_lock = asyncio.Lock()
        self.failure_count_lock = asyncio.Lock()
        self.key_failure_counts = {key: 0 for key in self.api_keys}
        self.MAX_FAILURES = settings.MAX_FAILURES
        self.paid_key = settings.PAID_KEY
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

class MockImageRequest:
    """模擬圖像生成請求"""
    def __init__(self, prompt="測試圖像", size="1024x1024"):
        self.prompt = prompt
        self.size = size
        self.n = 1
        self.response_format = "url"

class MockImageService:
    """模擬圖像服務類"""
    def __init__(self):
        self.key_manager = MockKeyManager()
        self.settings = MockSettings()
        self.logger = MockLogger()
    
    async def get_paid_key(self) -> str:
        """獲取付費密鑰"""
        return await self.key_manager.get_paid_key()
    
    async def generate_images(self, request: MockImageRequest):
        """模擬生成圖像，並使用付費密鑰"""
        try:
            # 獲取付費密鑰
            paid_key = await self.get_paid_key()
            
            self.logger.info(f"使用密鑰 '{paid_key}' 生成圖像: '{request.prompt}'")
            
            # 模擬API響應
            return {
                "created": 1234567890,
                "data": [{"url": f"https://example.com/image_{request.prompt}_{paid_key}.jpg"}],
                "used_key": paid_key
            }
        except Exception as e:
            self.logger.error(f"生成圖像失敗: {str(e)}")
            raise

async def test_image_service_sequential_keys():
    """測試圖像服務使用順序輪詢的付費密鑰"""
    print("開始測試圖像服務順序輪詢付費密鑰功能...")
    
    # 初始化圖像服務
    image_service = MockImageService()
    
    # 獲取付費密鑰列表以進行驗證
    paid_keys = image_service.key_manager.paid_key
    print(f"付費密鑰列表: {paid_keys}")
    
    # 模擬多次圖像生成請求
    print("\n模擬多次圖像生成請求:")
    results = []
    
    for i in range(1, 10):  # 生成9張圖像
        prompt = f"測試圖像_{i}"
        request = MockImageRequest(prompt=prompt)
        
        response = await image_service.generate_images(request)
        used_key = response.get("used_key")
        results.append(used_key)
        
        print(f"  #{i}: 生成圖像 '{prompt}' 使用密鑰: {used_key}")
    
    # 驗證是否按照順序輪詢使用密鑰
    print("\n驗證密鑰使用順序:")
    expected_sequence = []
    for i in range(len(results)):
        expected_key = paid_keys[i % len(paid_keys)]
        expected_sequence.append(expected_key)
        
        if results[i] != expected_key:
            print(f"  ❌ 第 {i+1} 次請求密鑰不匹配: 期望 {expected_key}, 實際 {results[i]}")
    
    if results == expected_sequence:
        print("  ✅ 測試通過: 圖像生成服務正確地按順序使用付費密鑰")
    else:
        print("  ❌ 測試失敗: 密鑰使用順序不符合預期")
        print(f"  期望順序: {expected_sequence}")
        print(f"  實際順序: {results}")
    
    # 測試連續使用同一個密鑰
    print("\n測試連續使用同一個密鑰:")
    
    # 修改密鑰列表為單個密鑰
    image_service.key_manager.paid_key = [paid_keys[0]]
    
    # 重置索引
    async with image_service.key_manager.paid_key_lock:
        image_service.key_manager.paid_key_index = 0
    
    # 連續生成三張圖像
    single_key_results = []
    for i in range(1, 4):
        prompt = f"單密鑰測試_{i}"
        request = MockImageRequest(prompt=prompt)
        
        response = await image_service.generate_images(request)
        used_key = response.get("used_key")
        single_key_results.append(used_key)
        
        print(f"  #{i}: 生成圖像 '{prompt}' 使用密鑰: {used_key}")
    
    # 驗證所有請求都使用了同一個密鑰
    if all(key == paid_keys[0] for key in single_key_results):
        print("  ✅ 測試通過: 單密鑰模式下所有請求都使用了同一個密鑰")
    else:
        print("  ❌ 測試失敗: 單密鑰模式下使用了不同的密鑰")
    
    print("\n所有測試完成!")

async def main():
    await test_image_service_sequential_keys()

if __name__ == "__main__":
    asyncio.run(main()) 