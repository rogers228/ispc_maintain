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

class Options:
    FIXED_ID = "ba298953-40c9-423b-90cc-b1cdb6e60e61"
    OPTIONS_PATH = os.path.join(ROOT_DIR, 'admin', 'temp_options.json')
    def __init__(self):
        self.table = "rec_option"
        self.auth = AuthManager()

    def get_options(self):
        """取得固定 id 的 options"""
        url = f"{spwr_api_url}/rest/v1/{self.table}?id=eq.{Options.FIXED_ID}&select=options"
        headers = {
            "apikey": spwr_api_anon_key,
            "Content-Type": "application/json"
        }
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            if data and isinstance(data, list) and "options" in data[0]:
                return data[0]["options"]
        else:
            print("Get failed:", resp.status_code, resp.text)
        return None

    def update_options(self, new_options):
        # print('update_options...')
        # 無權限修改者 雖然可以執行成功，但是無法修改
        # 權限採用jwt驗證
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
        payload = {"options": new_options}
        resp = requests.patch(url, headers=headers, json=payload)
        if resp.status_code in (200, 204):
            try:
                return resp.json()
            except:
                return None
        else:
            print("Update failed:", resp.status_code, resp.text)
            return None

    def pull_options(self):
        data = self.get_options()
        with open(Options.OPTIONS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

# 測試用
def test1(): # 讀取
    print("讀取 options:")
    opt = Options()
    current = opt.get_options()
    print(current)

def test2(): # update options
    opt = Options()
    new_data = {
        "name": "dark",
        "version": 0.12346,
    }
    updated = opt.update_options(new_data)
    print("更新後 options:", updated)

def test3():
    opt = Options()
    opt.pull_options()
    print('ok')

if __name__ == "__main__":
    test1()
