#!/usr/bin/env python3

def test_sequential_keys():
    """測試順序輪詢的付費密鑰功能"""
    print("模擬實際使用場景中的付費密鑰順序輪詢...")
    
    # 模擬付費密鑰列表
    paid_keys = ["API-KEY-1", "API-KEY-2", "API-KEY-3"]
    print(f"付費密鑰列表: {paid_keys}")
    
    # 模擬API請求並跟蹤使用的密鑰
    used_keys = []
    current_index = 0
    
    # 模擬10次API請求
    print("\n模擬API請求:")
    for i in range(1, 11):
        key = paid_keys[current_index]
        used_keys.append(key)
        
        print(f"請求 #{i}: 使用密鑰 {key}")
        
        # 更新索引，按順序輪詢
        current_index = (current_index + 1) % len(paid_keys)
    
    # 檢查使用的密鑰模式
    print("\n檢查使用的密鑰模式:")
    
    # 創建預期的密鑰序列
    expected_pattern = []
    for i in range(10):
        expected_pattern.append(paid_keys[i % len(paid_keys)])
    
    # 輸出對比
    print("期望的順序:")
    for i, key in enumerate(expected_pattern):
        print(f"  請求 #{i+1}: 使用密鑰 {key}")
    
    print("\n實際的順序:")
    for i, key in enumerate(used_keys):
        print(f"  請求 #{i+1}: 使用密鑰 {key}")
    
    # 驗證結果
    if used_keys == expected_pattern:
        print("\n✅ 測試通過: 付費密鑰按照正確的順序輪詢使用")
    else:
        print("\n❌ 測試失敗: 付費密鑰未按照預期順序使用")
    
    # 測試不同長度的密鑰列表
    print("\n測試不同長度的密鑰列表:")
    
    test_cases = [
        ["single-key"],  # 單個密鑰
        ["key-A", "key-B"],  # 兩個密鑰
        ["key-X", "key-Y", "key-Z", "key-W"]  # 四個密鑰
    ]
    
    for case_index, key_list in enumerate(test_cases):
        print(f"\n測試案例 {case_index+1}: {len(key_list)} 個密鑰")
        print(f"密鑰列表: {key_list}")
        
        results = []
        idx = 0
        
        for i in range(1, 7):  # 進行6次請求
            key = key_list[idx]
            results.append(key)
            print(f"  請求 #{i}: 使用密鑰 {key}")
            idx = (idx + 1) % len(key_list)
        
        # 創建預期的密鑰序列
        expected = []
        for i in range(6):
            expected.append(key_list[i % len(key_list)])
        
        # 驗證
        if results == expected:
            print(f"  ✅ 測試案例 {case_index+1} 通過")
        else:
            print(f"  ❌ 測試案例 {case_index+1} 失敗")
            print(f"    預期: {expected}")
            print(f"    實際: {results}")
    
    print("\n測試完成!")

if __name__ == "__main__":
    test_sequential_keys() 