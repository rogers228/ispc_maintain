import hashlib

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

if __name__ == '__main__':
    test1()