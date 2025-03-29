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
    """模擬修改後的KeyManager類，支持請求ID功能"""
    def __init__(self, paid_keys: list):
        self.paid_key = paid_keys
        self.paid_key_index = 0
        self.paid_key_lock = asyncio.Lock()
        self.request_key_map = {}
        self.logger = MockLogger()
    
    async def get_paid_key(self, request_id=None) -> str:
        """獲取一個付費 API 密鑰，按照順序從列表中取出，支持請求ID"""
        # 如果提供了請求 ID 且已經為該請求分配了密鑰，則返回之前分配的密鑰
        if request_id and request_id in self.request_key_map:
            key = self.request_key_map[request_id]
            self.logger.info(f"使用已分配的付費密鑰: {key} (請求ID: {request_id})")
            return key
        
        # 按順序獲取密鑰
        async with self.paid_key_lock:
            key = self.paid_key[self.paid_key_index]
            self.paid_key_index = (self.paid_key_index + 1) % len(self.paid_key)
            
            # 如果提供了請求 ID，則記錄該請求使用的密鑰
            if request_id:
                self.request_key_map[request_id] = key
                
            self.logger.info(f"使用付費密鑰: {key}，下一個索引位置: {self.paid_key_index}")
            return key
    
    def release_paid_key(self, request_id):
        """釋放與請求相關聯的付費密鑰"""
        if request_id in self.request_key_map:
            deleted_key = self.request_key_map[request_id]
            del self.request_key_map[request_id]
            self.logger.info(f"釋放請求 {request_id} 的付費密鑰: {deleted_key}")

class MockImageService:
    """模擬圖像服務類"""
    def __init__(self, key_manager):
        self.key_manager = key_manager
        self.logger = MockLogger()
    
    async def process_request(self, prompt, request_id=None):
        """處理圖像生成請求"""
        # 獲取付費密鑰
        key = await self.key_manager.get_paid_key(request_id)
        self.logger.info(f"使用密鑰 '{key}' 處理請求: '{prompt}'")
        
        # 模擬API處理過程中的第二次密鑰獲取（這是問題所在）
        key2 = await self.key_manager.get_paid_key(request_id)
        self.logger.info(f"再次獲取密鑰: '{key2}' 處理請求: '{prompt}'")
        
        # 釋放請求密鑰
        self.key_manager.release_paid_key(request_id)
        
        return {"success": True, "used_key": key, "second_key": key2}

async def test_request_id_key_management():
    """測試請求ID管理密鑰功能"""
    print("\n開始測試請求ID管理密鑰功能...")
    
    # 創建測試用的付費密鑰列表
    paid_keys = ["key-1", "key-2", "key-3"]
    print(f"付費密鑰列表: {paid_keys}")
    
    # 初始化密鑰管理器和圖像服務
    key_manager = MockKeyManager(paid_keys)
    image_service = MockImageService(key_manager)
    
    # 測試不使用請求ID（舊方式）
    print("\n1. 測試不使用請求ID時的行為:")
    
    # 模擬處理三個請求
    for i in range(1, 4):
        prompt = f"測試圖像_{i}"
        response = await image_service.process_request(prompt)
        
        if response["used_key"] != response["second_key"]:
            print(f"  ❌ 請求 #{i}: 兩次獲取了不同的密鑰: {response['used_key']} != {response['second_key']}")
        else:
            print(f"  ✅ 請求 #{i}: 兩次獲取了相同的密鑰: {response['used_key']} = {response['second_key']}")
    
    # 重置索引
    key_manager.paid_key_index = 0
    print("\n已重置索引為0")
    
    # 測試使用請求ID
    print("\n2. 測試使用請求ID時的行為:")
    
    # 模擬處理三個請求，每個請求都有唯一ID
    for i in range(1, 4):
        prompt = f"帶ID測試圖像_{i}"
        request_id = f"test_request_{i}"
        response = await image_service.process_request(prompt, request_id)
        
        if response["used_key"] == response["second_key"]:
            print(f"  ✅ 請求 #{i} (ID:{request_id}): 兩次獲取了相同的密鑰: {response['used_key']}")
        else:
            print(f"  ❌ 請求 #{i} (ID:{request_id}): 兩次獲取了不同的密鑰: {response['used_key']} != {response['second_key']}")
    
    print("\n測試完成!")

if __name__ == "__main__":
    asyncio.run(test_request_id_key_management()) 