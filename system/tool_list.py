def is_all_include(target_list, source_list):
    """
    檢查 target_list 的所有項目是否全部都在 source_list 裡面。

    :param target_list: 目標列表（潛在的子集）
    :param source_list: 來源列表（潛在的母集）
    :return: boolean
    """
    # 將 target_list 轉換為 Set，並檢查它是否為 source_list 轉換而成的 Set 的子集
    # target_list 轉換成 Set 後，可以使用 issubset() 或 '<=' 運算符
    return set(target_list).issubset(set(source_list))

def other_itmes(target_list, source_list):
    """
    從 source_list 中減去 target_list 中包含的項目。

    1. 將 target_list 和 source_list 轉換為 Set。
    2. 執行差集運算：source_set - target_set。
    3. 將結果轉換回 List 並返回。

    :param target_list: 目標列表（要被減去的項目）
    :param source_list: 來源列表（被操作的完整項目集）
    :return: 剩餘項目的列表 (list)
    """
    # 1. 轉換為 Set
    target_set = set(target_list)
    source_set = set(source_list)

    # 2. 執行差集運算：source_set 減去 target_set
    # 集合差集 (Set Difference) 運算符 '-' 會返回只存在於 source_set 而不存在於 target_set 的項目。
    difference_set = source_set - target_set
    # 或者使用 .difference() 方法: difference_set = source_set.difference(target_set)

    # 3. 將結果轉換回 List
    return list(difference_set)


def test1():
    target1 = [1, 3, 8]
    source1 = [1, 2, 3, 4, 5]
    print(f"target1 在 source1 中: {is_all_include(target1, source1)}")

def test2():
    source_list = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
    target_list = ['c', 'd', 'z'] # 即使 'z' 不在 source_list 中，也不影響結果
    result = other_itmes(target_list, source_list)

    print(f"來源列表 (source_list): {source_list}")
    print(f"目標列表 (target_list): {target_list}")
    print(f"剩餘項目 (result): {result}")
    # 輸出：剩餘項目 (result): ['h', 'g', 'e', 'b', 'f', 'a'] （順序不固定，因為 Set 是無序的）

    # 另一個數值範例
    source_list_num = [10, 20, 30, 40]
    target_list_num = [20, 50, 40]
    result_num = other_itmes(target_list_num, source_list_num)
    print(f"\n剩餘項目 (數值): {result_num}")
    # 輸出：剩餘項目 (數值): [10, 30]

if __name__ == '__main__':
    test2()