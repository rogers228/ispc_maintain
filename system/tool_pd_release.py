# 產品發布
if True:
    import sys, os
    import json
    import time
    import requests
    import multiprocessing

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
    from config_web import spwr_api_url, spwr_api_anon_key, WEB_SPECIC_ASSETS_URL, CLOUDFLARE_ZONE_ID, CLOUDFLARE_PURAGE_CACHE_TOKEN_DATAJSON
    from tool_auth import AuthManager
    from tool_time import get_local_time_tz
    from tool_msgbox import error, info

class ProductRelease:
    def __init__(self):
        self.table = "rec_pd_release"
        self.auth = AuthManager()
        data = self.auth.load_local_data()

    def release(self, uid):
        auth_data = self.auth.load_local_data()
        jwt = auth_data.get("jwt")
        email = auth_data.get("email", "unknown")

        if not jwt:
            print("❌ 錯誤: 找不到 JWT。請確認已登入。")
            return None

        # print('uid:', uid)
        payload = {
            "id": uid,
            "release_user": email,
            "release_time": get_local_time_tz(), # 取得符合 PostgreSQL 格式的帶時區時間
            "build_state": 1 # 需要編譯
        }
        # print('payload:', payload)
        headers = {
            "apikey": spwr_api_anon_key,
            "Authorization": f"Bearer {jwt}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates" # 關鍵：若 ID 重複則執行 Update (Upsert)
        }

        url = f"{spwr_api_url}/rest/v1/{self.table}"

        try:
            # 1. 寫入資料庫
            # 使用 POST 配合 Prefer: resolution=merge-duplicates 達成 Upsert
            response = requests.post(url, headers=headers, json=payload)

            if response.status_code not in [200, 201]:
                print(f"❌ 資料庫更新失敗: {response.status_code}")
                print(response.text)
                return {"is_error": True, "message": f"DB 更新失敗: {response.text}"}

            return {"is_error": False, "message": f"✅ 發佈成功"}

        except Exception as e:
            print(f"❌ 執行發布程序時發生崩潰: {e}")
            return {"is_error": True, "message": str(e)}

    def purge_cloudflare_cache_datajson_product(self, pdno):
        # 清除 Cloudflare 快取
        zone_id = CLOUDFLARE_ZONE_ID
        api_token = CLOUDFLARE_PURAGE_CACHE_TOKEN_DATAJSON
        base_url = WEB_SPECIC_ASSETS_URL

        urls_to_purge = [f"{base_url}/api/product/{pdno}"]
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
                print(f"✅ [Cloudflare] 成功清除預覽快取: {pdno}")
                return True
            else:
                error_info = result.get('errors')
                print(f"❌ [Cloudflare] 清除失敗 (pdno: {pdno}): {error_info}")
                return False

        except requests.exceptions.Timeout:
            print(f"⚠️ [Cloudflare] 請求逾時 (pdno: {pdno})")
            return False
        except Exception as e:
            print(f"⚠️ [Cloudflare] 發生未知錯誤: {e}")
            return False

def test1():
    print('test release...')
    pr = ProductRelease()
    uid = '4b87a39d-a0e4-4f73-8945-ebc54994e112'
    pr.release(uid)

if __name__ == '__main__':
    test1()
