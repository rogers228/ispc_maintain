# 產品發布
if True:
    import sys, os
    import json
    import time
    import requests

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
    from config import spwr_api_url, spwr_api_anon_key, WEB_ISCP_SVELTE_BUILD_HOOK_URL
    from tool_auth import AuthManager
    from tool_time import get_local_time_tz

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

        print('uid:', uid)
        payload = {
            "id": uid,
            "release_user": email,
            "release_time": get_local_time_tz(), # 取得符合 PostgreSQL 格式的帶時區時間
            "build_state": 1 # 需要編譯
        }
        print('payload:', payload)
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

            # print(f"✅ 資料更新成功")
            return {"is_error": False, "message": f"資料更新成功"}
            # print(f"✅ 資料庫已就緒 (build_state=1)，正在觸發編譯...")
            # 2. 觸發 Netlify Build Hook (如果 config 有設定)
            # try:
            #     hook_url = WEB_ISCP_SVELTE_BUILD_HOOK_URL
            #     hook_res = requests.post(hook_url, json={}) # Netlify 通常接受空的 JSON POST
            #     if hook_res.status_code in [200, 201, 202]:
            #         print("🚀 Netlify Build Hook 觸發成功！")
            #     else:
            #         print(f"⚠️ Hook 觸發異常: {hook_res.status_code}")
            # except Exception as e:
            #     print(f"⚠️ 無法連線至 Netlify Hook: {e}")

            # return {"is_error": False, "message": "發布請求已送出，系統開始編譯"}

        except Exception as e:
            print(f"❌ 執行發布程序時發生崩潰: {e}")
            return {"is_error": True, "message": str(e)}

def test1():
    print('test release...')
    pr = ProductRelease()
    uid = '4b87a39d-a0e4-4f73-8945-ebc54994e112'
    pr.release(uid)

if __name__ == '__main__':
    test1()
