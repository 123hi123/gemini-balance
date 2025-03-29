#!/usr/bin/env python3

def test_basic():
    print("開始基本測試...")
    
    # 模擬付費密鑰列表
    paid_keys = ["key-1", "key-2", "key-3"]
    print(f"付費密鑰列表: {paid_keys}")
    
    # 模擬順序輪詢
    results = []
    index = 0
    
    print("\n模擬輪詢:")
    for i in range(10):
        key = paid_keys[index]
        results.append(key)
        print(f"  第 {i+1} 次獲取: {key}")
        
        # 更新索引
        index = (index + 1) % len(paid_keys)
    
    # 驗證結果
    expected = []
    for i in range(10):
        expected_key = paid_keys[i % len(paid_keys)]
        expected.append(expected_key)
    
    print("\n驗證結果:")
    if results == expected:
        print("  ✅ 測試通過: 密鑰按照正確順序使用")
    else:
        print("  ❌ 測試失敗: 密鑰使用順序不符合預期")
    
    print("\n測試完成!")

if __name__ == "__main__":
    test_basic() 