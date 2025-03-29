#!/usr/bin/env python3
import asyncio
import sys
from importlib import import_module

async def run_all_tests():
    """執行所有付費密鑰輪詢相關的測試"""
    print("=" * 60)
    print("開始執行付費密鑰輪詢相關的所有測試")
    print("=" * 60)
    
    test_modules = [
        "test_paid_key_rotation",
        "test_env_paid_key_rotation",
        "test_image_generation_with_paid_key"
    ]
    
    for module_name in test_modules:
        try:
            print("\n" + "=" * 60)
            print(f"執行測試模塊: {module_name}")
            print("-" * 60)
            
            # 動態導入測試模塊
            module = import_module(module_name)
            
            # 執行測試模塊的 main 函數
            if hasattr(module, 'main'):
                await module.main()
            else:
                print(f"警告: 模塊 {module_name} 沒有 main 函數")
                
        except Exception as e:
            print(f"執行測試模塊 {module_name} 時發生錯誤: {e}")
    
    print("\n" + "=" * 60)
    print("所有測試完成")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_all_tests()) 