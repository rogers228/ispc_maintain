if True:
    import sys, os
    import json
    import time
    import requests
    import click

    def find_project_root(start_path=None, project_name="ispc_maintain"):
        if start_path is None:
            start_path = os.path.dirname(os.path.abspath(sys.argv[0]))
        current = start_path
        while True:
            if os.path.basename(current) == project_name:
                return current
            parent = os.path.dirname(current)
            if parent == current:
                raise FileNotFoundError(f"找不到專案 root (資料夾名稱 {project_name})")
            current = parent

    ROOT_DIR = find_project_root()
    sys.path.append(os.path.join(ROOT_DIR, "system"))
    from config import spwr_api_url, spwr_api_anon_key
    from tool_auth import AuthManager
    from tool_time import get_local_time
    from tool_str import get_str_hash

class ProductStorage:

    def __init__(self):
        self.table = "rec_pd"
        self.auth = AuthManager()

    def _prepare_payload(self, data: dict):
        # 處理 data_hash, last_time, edit_user 等欄位，並返回最終的 payload
        auth_data = self.auth.load_local_data()
        payload = data.copy()
        data_original = payload.get('data_original', '') # 獲取 data_original 用於計算 hash

        payload['data_hash'] = get_str_hash(data_original) if data_original else ''
        payload['last_time'] = get_local_time()
        payload['edit_user'] = auth_data.get("full_name", 'Unknown User')
        # 確保 'source_id' 欄位是 None 而不是空字串，如果它沒有值 (PostgreSQL 對 UUID 欄位比較嚴格)
        if payload.get('source_id') == '':
            payload['source_id'] = None
        return payload

    def select_multiple(self, lis_uid: list):
        # 查詢 rec_pd 表格中指定多筆 uid (id) 的資料。
        auth_data = self.auth.load_local_data()
        jwt = auth_data.get("jwt")

        if not jwt:
            print("❌ 錯誤: 找不到 JWT。請確認已登入。")
            return None

        if not lis_uid or not isinstance(lis_uid, list):
            print("❌ 錯誤: 必須提供有效的 UUID 列表 (lis_uid)。")
            return None

        uid_list_str = ','.join(lis_uid)
        url = f"{spwr_api_url}/rest/v1/{self.table}?id=in.({uid_list_str})&select=*"
        headers = {
            "apikey": spwr_api_anon_key,
            "Authorization": f"Bearer {jwt}",
            "Content-Type": "application/json",
        }

        print(f"🔎 嘗試查詢 {len(lis_uid)} 筆記錄...")
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            found_data = resp.json()
            print(f"✅ 查詢成功! 找到 {len(found_data)} 筆資料。")
            return found_data
        else:
            print("❌ 查詢失敗:")
            print("狀態碼:", resp.status_code)
            try:
                error_info = resp.json()
                print("錯誤詳情:", error_info)
            except json.JSONDecodeError:
                print("原始錯誤文本:", resp.text)
            return None

    def insert_one(self, data: dict):
        auth_data = self.auth.load_local_data()
        jwt = auth_data.get("jwt")
        if not jwt:
            print("❌ 錯誤: 找不到 JWT。請確認已登入。")
            return None

        payload = self._prepare_payload(data) # 處理 data_hash, last_time, edit_user 等欄位，並返回最終的 payload
        url = f"{spwr_api_url}/rest/v1/{self.table}"
        headers = {
            "apikey": spwr_api_anon_key,
            "Authorization": f"Bearer {jwt}",
            "Content-Type": "application/json",
            "Prefer": "return=representation" # 確保 API 返回新增的資料
        }

        print(f"🚀 嘗試向 {url} 執行 INSERT...")
        resp = requests.post(url, headers=headers, json=payload)
        if resp.status_code == 201: # 201 Created 是 INSERT 成功的標準 HTTP 狀態碼
            inserted_data = resp.json()
            print("✅ INSERT 成功!")
            print("回傳資料:", inserted_data)
            return inserted_data
        else:
            print("❌ INSERT 失敗:")
            print("狀態碼:", resp.status_code)
            try:
                # 嘗試解析 Supabase 返回的錯誤訊息
                error_info = resp.json()
                print("錯誤詳情:", error_info)
            except json.JSONDecodeError:
                print("原始錯誤文本:", resp.text)
            return None

    def update_one(self, uid: str, data: dict):
        auth_data = self.auth.load_local_data()
        jwt = auth_data.get("jwt")
        if not jwt:
            print(f"❌ 錯誤: 找不到 JWT。請確認已登入，無法更新 UID: {uid}。")
            return None

        if not uid:
            print("❌ 錯誤: 必須提供有效的 uid 才能執行更新。")
            return None

        payload = self._prepare_payload(data) # 處理 data_hash, last_time, edit_user 等欄位，並返回最終的 payload
        url = f"{spwr_api_url}/rest/v1/{self.table}?id=eq.{uid}"
        headers = {
            "apikey": spwr_api_anon_key,
            "Authorization": f"Bearer {jwt}",
            "Content-Type": "application/json",
            "Prefer": "return=representation" # 確保 API 返回更新後的資料
        }

        print(f"🔄 嘗試更新 UID: {uid}...")
        resp = requests.patch(url, headers=headers, json=payload)
        if resp.status_code == 200:
            updated_data = resp.json()
            print("✅ UPDATE 成功!")
            print("回傳更新資料:", updated_data)
            return updated_data[0] # PostgREST for PATCH returns a list of objects
        elif resp.status_code == 204:
            print("✅ UPDATE 成功 (無回傳內容 - 204 No Content)。")
            return True
        else:
            print("❌ UPDATE 失敗:")
            print("狀態碼:", resp.status_code)
            try:
                # 嘗試解析 Supabase 返回的錯誤訊息
                error_info = resp.json()
                print("錯誤詳情:", error_info)
            except json.JSONDecodeError:
                print("原始錯誤文本:", resp.text)
            return None
def test1():
    # 新增一筆
    ps = ProductStorage()
    test_data_original = f"這是測試產品資料，新增於 {get_local_time()}"
    data = {
        'pdno': f'TEST_API_{int(time.time())}',
        'name': 'API 測試產品 (動態傳入)',
        'use_type': 1, # 1: 預覽版
        'data_original': test_data_original,
        'data_json': json.dumps({"test_key": "test_value"}),
        'source_id': None, # 工作預覽版無來源
    }
    ps.insert_one(data)

def test2():
    # 更新
    ps = ProductStorage()
    uid = 'dbdcedbe-7bde-4b2c-8cfb-b21e8ccde68d'
    new_data_original = f"這是測試產品資料，修改於 {get_local_time()}"
    data = {
        'name': 'API 測試產品 (已更新名稱)', # 更新名稱
        'use_type': 2, # 狀態從預覽版(1)改為正式版(2)
        'data_original': new_data_original, # 傳入新資料來重新計算 data_hash
        'data_json': json.dumps({"status": "updated"}),
        'source_id': '2022f111-ddfa-4338-8023-8a72f8bea2cb'
    }
    ps.update_one(uid, data)

def test3():
    ps = ProductStorage()
    lis = ['dbdcedbe-7bde-4b2c-8cfb-b21e8ccde68d', '2022f111-ddfa-4338-8023-8a72f8bea2cb']
    selected_records = ps.select_multiple(lis)
    if selected_records:
        print(f"✅ SELECT MULTIPLE 成功! 查詢結果筆數: {len(selected_records)}")
        for record in selected_records:
            print(record)
    else:
        print("❌ SELECT MULTIPLE 步驟失敗。")

if __name__ == '__main__':
    test3()