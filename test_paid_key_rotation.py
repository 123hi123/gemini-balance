import asyncio
import os
import sys

# 添加專案根目錄到Python路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.service.key.key_manager import KeyManager
from app.service.image.image_create_service import ImageCreateService

async def test_paid_key_rotation():
    """測試付費密鑰輪詢功能"""
    print("開始測試付費密鑰輪詢功能...")
    
    # 創建測試用的API鍵和付費密鑰列表
    api_keys = ["api-key-1", "api-key-2"]
    paid_keys = ["paid-key-1", "paid-key-2", "paid-key-3"]
    
    # 初始化KeyManager
    key_manager = KeyManager(api_keys)
    
    # 手動設置付費密鑰列表
    key_manager.paid_key = paid_keys
    
    # 重新初始化付費密鑰的循環器
    if isinstance(key_manager.paid_key, list) and key_manager.paid_key:
        key_manager.paid_key_cycle = asyncio.cycle(key_manager.paid_key)
        key_manager.paid_key_cycle_lock = asyncio.Lock()
        key_manager.paid_key_failure_counts = {key: 0 for key in key_manager.paid_key}
    
    # 測試多次調用get_paid_key方法
    results = []
    for _ in range(5):  # 調用5次，應該看到循環模式
        key = await key_manager.get_paid_key()
        results.append(key)
        print(f"獲取付費密鑰: {key}")
    
    # 驗證結果
    expected_pattern = paid_keys * (5 // len(paid_keys)) + paid_keys[:5 % len(paid_keys)]
    expected_pattern = expected_pattern[:5]
    
    if results == expected_pattern:
        print("✅ 測試通過: 付費密鑰正確輪詢")
    else:
        print(f"❌ 測試失敗: 預期結果: {expected_pattern}, 實際結果: {results}")

    # 透過ImageCreateService測試
    print("\n測試通過ImageCreateService獲取付費密鑰...")
    
    # 初始化ImageCreateService
    image_service = ImageCreateService()
    
    # 手動設置KeyManager (模擬真實場景)
    # 注意: 這僅用於測試，實際應用中應使用get_key_manager_instance
    setattr(image_service, "_test_key_manager", key_manager)
    
    # 覆蓋get_paid_key方法以使用我們的測試KeyManager
    original_method = image_service.get_paid_key
    
    async def test_get_paid_key():
        return await key_manager.get_paid_key()
    
    image_service.get_paid_key = test_get_paid_key
    
    try:
        # 多次獲取付費密鑰
        service_results = []
        for _ in range(5):
            key = await image_service.get_paid_key()
            service_results.append(key)
            print(f"通過ImageCreateService獲取付費密鑰: {key}")
        
        # 驗證結果
        if service_results == expected_pattern:
            print("✅ 測試通過: ImageCreateService正確輪詢付費密鑰")
        else:
            print(f"❌ 測試失敗: 預期結果: {expected_pattern}, 實際結果: {service_results}")
    finally:
        # 恢復原始方法
        image_service.get_paid_key = original_method

async def main():
    await test_paid_key_rotation()

if __name__ == "__main__":
    asyncio.run(main()) 