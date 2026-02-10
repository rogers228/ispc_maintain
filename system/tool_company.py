if True:
    import sys, os
    import json
    import time
    import requests
    import subprocess

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
    # from config import spwr_api_url, spwr_api_anon_key
    from config_web import spwr_api_url, spwr_api_anon_key, WEB_SPECIC_ASSETS_URL, CLOUDFLARE_ZONE_ID, CLOUDFLARE_PURAGE_CACHE_TOKEN_DATAJSON
    from tool_auth import AuthManager
    from tool_time import get_local_time
    from tool_str import generate_random_char_lower
    from tool_comp_jogging import CompanyCheck

class Company:
    STORAGE_PATH = os.path.join(ROOT_DIR, 'tempstorage')

    def __init__(self):
        self.table = "rec_company"
        self.auth = AuthManager()
        data = self.auth.load_local_data()
        self.editor = data.get("editor", '') # 編輯器

    def _prepare_payload(self, data: dict):
        # 處理 data_hash, last_time, edit_user, version 等欄位，並返回最終的 payload
        auth_data = self.auth.load_local_data()
        payload = data.copy()
        payload['last_time'] = get_local_time()
        payload['edit_user'] = auth_data.get("full_name", 'Unknown User')
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
            if updated_data:
                print("✅ UPDATE 成功!")
                # print("回傳更新資料:", updated_data)
                return updated_data[0]
            else:
                print(" ❌ 未通過 Policies 無法更新!")
                return None
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

    def get_one(self, uid):
        records = self.select_multiple([uid])
        if records:
            # print(f"✅ get_one 成功!")
            # print(records[0]) # 第一筆
            return records[0]
        else:
            print("❌ get_one 步驟失敗。")
            return None

    def pull_data_original(self, uid):
        # 拉取一筆資料的 data_original 建立至本地
        result = {'is_error': False, 'message': ''}
        data = self.get_one(uid)
        if data is None:
            message = '❌ 下載失敗!'
            print(message)
            return {'is_error': True, 'message': message}

        data_original = data.get('data_original', '')
        file = os.path.join(Company.STORAGE_PATH, f"{uid}.py")
        with open(file, "w", encoding="utf-8") as f:
            f.write(data_original)

        message = f'✅ 已成功建立 {uid}.py 檔案，請按編輯。'
        print(message)
        return {'is_error': False, 'message': message}

    def edit(self, uid=None): # 編輯 以編輯器開啟
        result = {'is_error': False, 'message': ''}
        if not self.editor or not os.path.exists(self.editor): #editor 不存在
            message = '❌ editor 尚未設定編輯器!'
            print(message)
            return {'is_error': True, 'message': message}

        file = os.path.join(ProductStorage.STORAGE_PATH, f"{uid}.py")
        result = None # 是否正確建立
        if not os.path.exists(file): # 若不存在
            message = '❌ 尚未建立檔案，請先下載!'
            print(message)
            return {'is_error': True, 'message': message}

        message = f'✏️ 編輯 {uid}.py'
        print(message)
        subprocess.Popen([self.editor, file], shell=True) # 以編輯器開啟
        return {'is_error': False, 'message': message}

    def upload(self, uid):
        print(f'🔼 上傳 {uid}.py')
        cc = CompanyCheck(uid)     # 檢查文件...
        storage = cc.get_detaile() # 取得結果

        # 驗證失敗
        if storage['is_verify'] is False: # 驗證失敗
            print(storage['message'])     # 錯誤訊息
            return {
                'is_verify': False,
                'message': storage['message'],
                'result': None,
            }
        # 驗證成功

        data = {
            'data_original': storage['data_original'],
            'data_json': storage['data_json'],
        }
        # print(json.dumps(data, indent=4, ensure_ascii=False))
        result = self.update_one(uid, data)
        return {
            'is_verify': True,
            'message': '',
            'result': result,
        }

    def purge_cloudflare_cache_datajson_company(self, cono):
        # 清除 Cloudflare 快取
        zone_id = CLOUDFLARE_ZONE_ID
        api_token = CLOUDFLARE_PURAGE_CACHE_TOKEN_DATAJSON
        base_url = WEB_SPECIC_ASSETS_URL

        urls_to_purge = [f"{base_url}/api/company/{cono}"]
        # Cloudflare API 端點
        api_endpoint = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/purge_cache"
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        payload = {"files": urls_to_purge}
        try:
            response = requests.post(api_endpoint, json=payload, headers=headers, timeout=10)
            result = response.json()
            if result.get("success"):
                print(f"✅ [Cloudflare] 成功清除預覽快取: {cono}")
                return True
            else:
                error_info = result.get('errors')
                print(f"❌ [Cloudflare] 清除失敗 (cono: {cono}): {error_info}")
                return False
        except requests.exceptions.Timeout:
            print(f"⚠️ [Cloudflare] 請求逾時 (cono: {cono})")
            return False
        except Exception as e:
            print(f"⚠️ [Cloudflare] 發生未知錯誤: {e}")
            return False

def test1():
    # 新增一筆，完成後請至 temp_options.py 添加使用者權限
    comp = Company()
    data = {
        'custom_index': generate_random_char_lower(),
        'title': 'yeoshe_油聖液壓科技有限公司',
        'data_original': '',
        'data_json': '',
    }
    print(data)
    print('adding')
    comp.insert_one(data)
    print('add success, 請至 temp_options.py 添加使用者權限')

def test2():
    # 更新
    comp = Company()
    uid = 'ee080167-e20e-45bf-84ce-f5516022331c'
    new_data_original = f"這是測試產品資料，修改於 {get_local_time()}"
    data = {
        'data_original': new_data_original, # 傳入新資料來重新計算 data_hash
    }
    comp.update_one(uid, data)

def test3():
    # 查詢多筆
    comp = Company()
    lis = ['ee080167-e20e-45bf-84ce-f5516022331c']
    selected_records = comp.select_multiple(lis)
    if selected_records:
        print(f"✅ SELECT MULTIPLE 成功! 查詢結果筆數: {len(selected_records)}")
        for record in selected_records:
            print(record)
    else:
        print("❌ SELECT MULTIPLE 步驟失敗。")

def test4():
    # 下載建立 uid.py
    comp = Company()
    uid = 'ee080167-e20e-45bf-84ce-f5516022331c'
    comp.pull_data_original(uid)

def test5():
    # 上傳 uid.py
    comp = Company()
    uid = 'ee080167-e20e-45bf-84ce-f5516022331c'
    result = comp.upload(uid)
    print(result)

if __name__ == '__main__':
    test5()
    print('ok')