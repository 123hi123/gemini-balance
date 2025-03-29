#!/usr/bin/env python3
import asyncio
import sys

# 將輸出重定向到文件
output_file = open("test_results.txt", "w", encoding="utf-8")

def log(message):
    """輸出到控制台和文件"""
    print(message)
    output_file.write(message + "\n")
    output_file.flush()  # 確保立即寫入文件

class KeyManager:
    """簡化版密鑰管理器，支持請求ID功能"""
    def __init__(self, paid_keys):
        self.paid_keys = paid_keys
        self.index = 0
        self.lock = asyncio.Lock()
        self.request_key_map = {}
    
    async def get_paid_key(self, request_id=None):
        """獲取付費密鑰，支持請求ID"""
        # 如果提供請求ID並且已分配密鑰，則返回已分配的密鑰
        if request_id and request_id in self.request_key_map:
            key = self.request_key_map[request_id]
            log(f"[使用已分配密鑰] {key}，請求ID: {request_id}")
            return key
        
        # 獲取新密鑰
        async with self.lock:
            key = self.paid_keys[self.index]
            self.index = (self.index + 1) % len(self.paid_keys)
            
            # 如果提供請求ID，記錄分配的密鑰
            if request_id:
                self.request_key_map[request_id] = key
            
            log(f"[分配新密鑰] {key}，下一個索引: {self.index}")
            return key
    
    def release_key(self, request_id):
        """釋放請求關聯的密鑰"""
        if request_id in self.request_key_map:
            key = self.request_key_map[request_id]
            del self.request_key_map[request_id]
            log(f"[釋放密鑰] {key}，請求ID: {request_id}")

async def test_without_request_id(key_manager):
    """測試不使用請求ID的情況"""
    log("\n===== 測試不使用請求ID =====")
    # 模擬多次獲取密鑰（同一請求中）
    keys = []
    for i in range(3):
        key = await key_manager.get_paid_key()
        keys.append(key)
    
    # 檢查是否每次都獲取了不同的密鑰
    if len(set(keys)) == len(keys):
        log(f"❌ 問題複現：獲取了 {len(keys)} 個不同的密鑰: {keys}")
    else:
        log(f"✓ 獲取了相同的密鑰: {keys}")

async def test_with_request_id(key_manager):
    """測試使用請求ID的情況"""
    log("\n===== 測試使用請求ID =====")
    
    # 創建3個不同的請求
    for req_id in ["request-1", "request-2", "request-3"]:
        # 每個請求獲取密鑰兩次
        key1 = await key_manager.get_paid_key(req_id)
        key2 = await key_manager.get_paid_key(req_id)
        
        # 檢查兩次獲取的是否是同一個密鑰
        if key1 == key2:
            log(f"✅ 請求 {req_id}: 兩次獲取了相同的密鑰 {key1}")
        else:
            log(f"❌ 請求 {req_id}: 獲取了不同的密鑰 {key1} 和 {key2}")
        
        # 釋放密鑰
        key_manager.release_key(req_id)

async def main():
    try:
        # 初始化密鑰列表
        paid_keys = ["key-A", "key-B", "key-C"]
        log(f"付費密鑰列表: {paid_keys}")
        
        # 創建密鑰管理器
        key_manager = KeyManager(paid_keys)
        
        # 測試不使用請求ID
        await test_without_request_id(key_manager)
        
        # 重置索引
        key_manager.index = 0
        log("\n已重置索引為0")
        
        # 測試使用請求ID
        await test_with_request_id(key_manager)
        
        log("\n測試完成！")
    finally:
        # 確保文件被關閉
        output_file.close()

if __name__ == "__main__":
    asyncio.run(main()) 