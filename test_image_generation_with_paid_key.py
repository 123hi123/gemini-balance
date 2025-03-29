import asyncio
import os
import sys
import time
from unittest.mock import AsyncMock, patch

# 添加專案根目錄到Python路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config.config import settings
from app.domain.openai_models import ImageGenerationRequest
from app.service.image.image_create_service import ImageCreateService
from app.service.key.key_manager import get_key_manager_instance

async def test_image_generation_with_key_rotation():
    """
    測試圖像生成服務中的付費密鑰輪詢功能
    
    注意：這個測試使用了Mock來避免實際調用Google API
    """
    print("測試圖像生成中的付費密鑰輪詢功能...")
    
    # 獲取環境中的 API 密鑰和付費密鑰
    api_keys = settings.API_KEYS
    paid_keys = settings.PAID_KEY
    
    print(f"環境中的 API 密鑰數量: {len(api_keys)}")
    
    if not isinstance(paid_keys, list) or len(paid_keys) <= 1:
        print("⚠️ 警告: 付費密鑰不是列表或僅包含一個密鑰，輪詢功能無法測試")
        if isinstance(paid_keys, str) and paid_keys:
            print(f"發現單個付費密鑰: {paid_keys}")
            paid_keys = [paid_keys]  # 轉換為列表以便繼續測試
        else:
            print("未找到有效的付費密鑰，使用模擬密鑰進行測試")
            paid_keys = ["mock-paid-key-1", "mock-paid-key-2", "mock-paid-key-3"]
            
            # 手動設置模擬的付費密鑰
            settings.PAID_KEY = paid_keys
    
    print(f"使用的付費密鑰: {paid_keys}")
    
    # 模擬圖像生成請求
    image_request = ImageGenerationRequest(
        model="dall-e-3",
        prompt="A beautiful landscape with mountains and a lake",
        n=1,
        size="1024x1024"
    )
    
    # 創建圖像服務實例
    image_service = ImageCreateService()
    
    # 收集使用的付費密鑰
    used_keys = []
    
    # 使用 Mock 替代實際的 genai.Client 以避免真實 API 調用
    with patch('google.genai.Client') as mock_client:
        # 設置mock客戶端的行為
        client_instance = mock_client.return_value
        models_attr = AsyncMock()
        client_instance.models = models_attr
        
        # 設置模擬的 generate_images 方法
        generate_images_mock = AsyncMock()
        models_attr.generate_images = generate_images_mock
        
        # 存儲每次調用時使用的密鑰
        api_keys_used = []
        
        original_init = mock_client.__init__
        
        def mock_init(self, api_key=None, **kwargs):
            api_keys_used.append(api_key)
            original_init(self, api_key=api_key, **kwargs)
            
        mock_client.__init__ = mock_init
        
        # 模擬多次圖像生成請求
        print("\n模擬多次圖像生成請求:")
        for i in range(len(paid_keys) * 2):
            try:
                # 每次調用前清空已使用的密鑰列表
                api_keys_used.clear()
                
                # 設置模擬響應
                mock_response = AsyncMock()
                mock_response.generated_images = []  # 空列表表示無圖像生成
                generate_images_mock.return_value = mock_response
                
                print(f"發送第 {i+1} 次圖像生成請求...")
                
                # 嘗試調用圖像生成服務
                try:
                    await image_service.generate_images(image_request)
                except Exception as e:
                    # 預期會拋出異常，因為我們模擬了空的生成圖像
                    if "I can't generate these images" not in str(e):
                        print(f"意外錯誤: {e}")
                
                # 獲取使用的密鑰
                if api_keys_used:
                    used_key = api_keys_used[0]
                    used_keys.append(used_key)
                    print(f"請求使用了密鑰: {used_key}")
            
            except Exception as e:
                print(f"測試過程中發生錯誤: {e}")
                
    # 打印所有使用的密鑰
    print("\n所有使用的付費密鑰順序:")
    for i, key in enumerate(used_keys):
        print(f"{i+1}: {key}")
    
    # 檢查是否按預期輪詢
    is_rotating = True
    if len(used_keys) >= len(paid_keys) * 2:
        for i in range(len(paid_keys)):
            if used_keys[i] != used_keys[i + len(paid_keys)]:
                is_rotating = False
                break
                
        if is_rotating:
            print("\n✅ 測試通過: 付費密鑰在圖像生成請求中正確輪詢")
        else:
            print("\n❌ 測試失敗: 付費密鑰在圖像生成請求中未按預期輪詢")
            print(f"第一輪密鑰: {used_keys[:len(paid_keys)]}")
            print(f"第二輪密鑰: {used_keys[len(paid_keys):len(paid_keys)*2]}")
    else:
        print(f"\n⚠️ 警告: 收集到的密鑰數量不足，無法完全驗證輪詢邏輯 (收集到 {len(used_keys)} 個，需要 {len(paid_keys)*2} 個)")

async def main():
    await test_image_generation_with_key_rotation()

if __name__ == "__main__":
    asyncio.run(main()) 