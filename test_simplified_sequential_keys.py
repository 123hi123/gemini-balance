#!/usr/bin/env python3
import asyncio

class MockKeyManager:
    def __init__(self, paid_keys):
        self.paid_key = paid_keys
        self.paid_key_index = 0
        self.paid_key_lock = asyncio.Lock()
    
    async def get_paid_key(self):
        """按順序獲取付費密鑰"""
        if not self.paid_key:
            return ""
            
        async with self.paid_key_lock:
            key = self.paid_key[self.paid_key_index]
            self.paid_key_index = (self.paid_key_index + 1) % len(self.paid_key)
            print(f"[INFO] 獲取付費密鑰: {key}，下一個索引: {self.paid_key_index}")
            return key

class MockImageService:
    def __init__(self, key_manager):
        self.key_manager = key_manager
    
    async def generate_image(self, prompt):
        key = await self.key_manager.get_paid_key()
        print(f"[IMG] 使用密鑰 '{key}' 生成圖像: '{prompt}'")
        return {"success": True, "used_key": key}

async def test_simplified_sequential_keys():
    print("開始簡化版付費密鑰順序輪詢測試...")
    
    # 創建測試用的付費密鑰列表
    paid_keys = ["key-1", "key-2", "key-3"]
    print(f"付費密鑰列表: {paid_keys}")
    
    # 初始化密鑰管理器和圖像服務
    key_manager = MockKeyManager(paid_keys)
    image_service = MockImageService(key_manager)
    
    # 測試順序輪詢
    print("\n測試密鑰管理器順序輪詢:")
    for i in range(len(paid_keys) * 2):
        key = await key_manager.get_paid_key()
        print(f"  第 {i+1} 次獲取: {key}")
    
    # 測試圖像生成使用密鑰
    print("\n測試圖像生成使用密鑰:")
    results = []
    for i in range(1, 10):
        prompt = f"測試圖像_{i}"
        response = await image_service.generate_image(prompt)
        key = response["used_key"]
        results.append(key)
        print(f"  #{i}: 生成結果使用密鑰: {key}")
    
    # 驗證結果
    print("\n驗證密鑰使用順序:")
    expected = []
    for i in range(len(results)):
        expected_key = paid_keys[i % len(paid_keys)]
        expected.append(expected_key)
        
    if results == expected:
        print("  ✅ 測試通過: 密鑰按照正確順序使用")
    else:
        print("  ❌ 測試失敗: 密鑰使用順序不符合預期")
        print(f"  預期順序: {expected}")
        print(f"  實際順序: {results}")
    
    print("\n測試完成!")

if __name__ == "__main__":
    asyncio.run(test_simplified_sequential_keys()) 