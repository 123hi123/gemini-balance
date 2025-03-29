import asyncio
import os
import sys
import json

# 添加專案根目錄到Python路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config.config import settings
from app.service.key.key_manager import KeyManager, get_key_manager_instance
from app.service.image.image_create_service import ImageCreateService

async def test_env_paid_key_rotation():
    """測試環境配置中的付費密鑰輪詢功能"""
    print("開始測試環境配置中的付費密鑰輪詢功能...")
    
    # 獲取環境中的 API 密鑰和付費密鑰
    api_keys = settings.API_KEYS
    paid_keys = settings.PAID_KEY
    
    print(f"環境中的 API 密鑰數量: {len(api_keys)}")
    print(f"環境中的付費密鑰: {paid_keys}")
    
    if not isinstance(paid_keys, list) or len(paid_keys) <= 1:
        print("⚠️ 警告: 付費密鑰不是列表或僅包含一個密鑰，輪詢功能無法測試")
        if isinstance(paid_keys, str) and paid_keys:
            print(f"發現單個付費密鑰: {paid_keys}")
        return
    
    # 初始化 KeyManager 實例
    key_manager = await get_key_manager_instance(api_keys)
    
    # 測試多次調用 get_paid_key 方法
    results = []
    print("\n直接從 KeyManager 獲取付費密鑰:")
    for i in range(len(paid_keys) * 2):  # 調用足夠多次以觀察完整輪詢
        key = await key_manager.get_paid_key()
        results.append(key)
        print(f"第 {i+1} 次獲取: {key}")
    
    # 檢查輪詢邏輯
    is_rotating = True
    for i in range(len(paid_keys)):
        if results[i] != results[i + len(paid_keys)]:
            is_rotating = False
            break
    
    if is_rotating:
        print("✅ 測試通過: 付費密鑰正確輪詢")
    else:
        print("❌ 測試失敗: 付費密鑰未按預期輪詢")
        
    # 透過 ImageCreateService 測試
    print("\n通過 ImageCreateService 獲取付費密鑰:")
    image_service = ImageCreateService()
    
    service_results = []
    for i in range(len(paid_keys) * 2):
        key = await image_service.get_paid_key()
        service_results.append(key)
        print(f"第 {i+1} 次獲取: {key}")
    
    # 檢查通過服務獲取的密鑰輪詢
    is_service_rotating = True
    for i in range(len(paid_keys)):
        if service_results[i] != service_results[i + len(paid_keys)]:
            is_service_rotating = False
            break
    
    if is_service_rotating:
        print("✅ 測試通過: ImageCreateService 正確輪詢付費密鑰")
    else:
        print("❌ 測試失敗: ImageCreateService 未按預期輪詢密鑰")
    
    # 檢查兩種方法是否一致
    if results[:len(paid_keys)] == service_results[:len(paid_keys)]:
        print("✅ 測試通過: 兩種方法獲取的密鑰序列一致")
    else:
        print("❌ 測試失敗: 兩種方法獲取的密鑰序列不一致")
        print(f"KeyManager 序列: {results[:len(paid_keys)]}")
        print(f"ImageService 序列: {service_results[:len(paid_keys)]}")

async def main():
    await test_env_paid_key_rotation()

if __name__ == "__main__":
    asyncio.run(main()) 