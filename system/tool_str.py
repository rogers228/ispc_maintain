import hashlib
import time
from datetime import datetime
import random
import string

def get_str_hash(content):
    # 接收字串內容 (content)，使用 SHA-256 演算法生成雜湊值 (Hash Value)。
    if not content:
        return None

    try:
        hash_object = hashlib.sha256()
        hash_object.update(content.encode('utf-8'))
        hex_digest = hash_object.hexdigest()
        return hex_digest

    except Exception as e:
        print(f"計算雜湊時發生錯誤: {e}")
        return None


def version_upgrade(old_version=None):
    # 升級版本號
    # AAA-YYYYMMDD  =>  AAA+1 -YYYYMMDD
    if old_version is None:
        version = 1
    else:
        try:
            version = int(old_version.split('-')[0]) + 1 # 解析舊版號
        except (ValueError, IndexError):
            print(f"警告: 舊版本 '{old_version}' 格式錯誤或不完整，版本號將從 1 開始計算。")
            version = 1

    return f"{version}-{datetime.now().strftime('%Y%m%d')}" # AAA-YYYYMMDD

def generate_random_char(length=12):
    # string.ascii_letters 包含所有大小寫英文字母
    # string.digits 包含所有數字 0-9
    characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choices(characters, k=length))
    return random_string

def generate_random_char_lower(length=12):
    # string.ascii_lowercase 僅包含所有小寫英文字母 (a-z)
    # string.digits 包含所有數字 (0-9)
    characters = string.ascii_lowercase + string.digits
    random_string = ''.join(random.choices(characters, k=length))
    return random_string

def test1():
    content_v1 = "這是一段不會變動的配置內容。"
    content_v2 = "這是一段不會變動的配置內容。"
    content_v3 = "這是一段已經被修改的配置內容。"
    hash_v1 = get_str_hash(content_v1)
    hash_v2 = get_str_hash(content_v2)
    hash_v3 = get_str_hash(content_v3)
    print(f"內容 V1 雜湊: {hash_v1}")
    print(f"內容 V2 雜湊: {hash_v2}")
    print(f"內容 V3 雜湊: {hash_v3}")
    print("-" * 30)
    # 判斷內容是否 'dirty'
    print(f"V1 和 V2 是否相同? {'是' if hash_v1 == hash_v2 else '否'}")
    print(f"V1 和 V3 是否相同? {'是' if hash_v1 == hash_v3 else '否'}")

def test2():
    # 1. 首次呼叫 (無舊版本)
    version1 = version_upgrade()
    print(f"輸入 None: {version1}") # 輸出: '1.20251012' (如果日期是 20251012)

    # 2. 正常升級
    version2 = version_upgrade('25-20250101')
    print(f"輸入 '25-20250101': {version2}") # 輸出: '26.20251012'

    # 3. 大版本升級
    version3 = version_upgrade('999-20250930')
    print(f"輸入 '999-20250930': {version3}") # 輸出: '1000.20251012'

def test3():
    for _ in range(0, 4):
        print(generate_random_char_lower(length=16))

if __name__ == '__main__':
    test3()