if True:
    import sys, os
    import json
    import time
    import requests
    from supabase import create_client, Client

    def find_project_root(start_path=None, project_name="ispc_maintain"):
        import sys
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

class Options:
    FIXED_ID = "ba298953-40c9-423b-90cc-b1cdb6e60e61"
    def __init__(self):
        """建立 supabase client"""
        self.client: Client = create_client(spwr_api_url, spwr_api_anon_key)
        self.table = "rec_option"
        self.auth = AuthManager()

    def create_options(self, options: dict):
        """建立一筆新的 options 設定"""
        data = {"options": options}
        res = self.client.table(self.table).insert(data).execute()
        return res.data

    def get_options(self):
        res = (
            self.client.table(self.table)
            .select("options")
            .eq("id", self.FIXED_ID)
            .single()
            .execute()
        )
        if res.data:
            return res.data["options"]
        return None

    def update_options(self, new_options):
        # print('update_options...')
        # 無權限修改者 雖然可以執行成功，但是無法修改
        data = self.auth.load_local_data()
        jwt = data.get("jwt")
        if not jwt:
            raise RuntimeError("尚未登入，請先使用 AuthManager.login()")

        url = f"{spwr_api_url}/rest/v1/rec_option?id=eq.{Options.FIXED_ID}"
        headers = {
            "apikey": spwr_api_anon_key,
            "Authorization": f"Bearer {jwt}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        data = {"options": new_options}
        resp = requests.patch(url, headers=headers, json=data)
        return resp.json()

# 測試用
def test1(): # 建立
    print("讀取 options:")
    opt = Options()
    current = opt.get_options()
    print(current)

def test2(): # update options
    opt = Options()
    new_data = {
        "name": "dark",
        "version": 0.12345,
    }
    updated = opt.update_options(new_data)


    print("更新後 options:", updated)

if __name__ == "__main__":
    test2()
