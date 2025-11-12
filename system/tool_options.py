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
    from tool_exec import exec_python

class Options:
    FIXED_ID = "ba298953-40c9-423b-90cc-b1cdb6e60e61"
    OPTIONS_PATH = os.path.join(ROOT_DIR, 'admin', 'temp_options.py')
    def __init__(self):
        self.table = "rec_option"
        self.auth = AuthManager()

    def get_original(self):
        """取得固定 id 的 original"""
        data = self.auth.load_local_data()
        jwt = data.get("jwt")
        if not jwt:
            return None

        url = f"{spwr_api_url}/rest/v1/{self.table}?id=eq.{Options.FIXED_ID}&select=original"
        headers = {
            "apikey": spwr_api_anon_key,
            "Authorization": f"Bearer {jwt}",
            "Content-Type": "application/json"
        }
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            if data and isinstance(data, list) and "original" in data[0]:
                return data[0]["original"]
        else:
            print("Get failed:", resp.status_code, resp.text)
            return None
        return None

    def get_local_original(self):
        # 動態載入
        if not os.path.exists(Options.OPTIONS_PATH):
            raise FileNotFoundError(f"錯誤：找不到檔案 {file_path}")
            return None
        try:
            with open(Options.OPTIONS_PATH, 'r', encoding='utf-8') as f:
                local_original = f.read()
            return local_original
        except Exception as e:
            print(f"❌ 執行檔案時發生錯誤: {e}")
            return None

    def get_local_options(self):
        original = self.get_local_original()
        if original is None:
            print("更新已中止：無法讀取本地 original 檔案。")
            return {}

        local_vars = exec_python(original) # 建立一個局部命名空間
        if local_vars is None:
             return {} # 執行失敗，錯誤訊息已在 _execute_original_content 中列印

        options = local_vars.get('options', {})
        return options

    def get_jwt(self):
        data = self.auth.load_local_data()
        if not data.get("email") or not data.get("refresh_token"):
            print("尚未登入，請先執行 login")
            return None

        if not self.auth.is_token_valid():
            print("Token 已失")
            return None

        jwt = data.get("jwt")
        return jwt

    def update_options(self):
        # print('update_options...')
        # 無權限修改者 雖然可以執行成功，但是無法修改
        # 權限採用jwt驗證

        if not self.auth.is_token_valid():
            print("❌，請先登入")
            return None

        original = self.get_local_original()
        if original is None:
            print("更新已中止：無法讀取本地 original 檔案。")
            return

        original_hash = get_str_hash(original)
        local_vars = exec_python(original) # 建立一個局部命名空間
        if local_vars is None:
            return  # 執行失敗，錯誤訊息已在 _execute_original_content 中列印
        options = local_vars.get('options', {})
        try:
            options_json = json.dumps(options, indent=4, ensure_ascii=False)
        except TypeError as e:
            # 捕捉 json.dumps 字典中包含不可 JSON 序列化的類型
            print(f"❌ 配置內容 JSON 序列化失敗 (TypeError): 配置包含無法轉換的 Python 類型。詳情: {e}")
            return
        except Exception as e:
            print(f"❌ 執行檔案時發生錯誤: {e}")
            return

        payload = {
            "original": original,
            "original_hash": original_hash,
            "options": options_json, # 這裡傳送的是 JSON 字串
            "last_time": get_local_time(),
            }
        # print(payload)

        data = self.auth.load_local_data()
        jwt = data.get("jwt")
        if not jwt:
            return None

        url = f"{spwr_api_url}/rest/v1/rec_option?id=eq.{Options.FIXED_ID}"
        headers = {
            "apikey": spwr_api_anon_key,
            "Authorization": f"Bearer {jwt}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        resp = requests.patch(url, headers=headers, json=payload)
        if resp.status_code in (200, 204):
            print('push temp_options.py success.')
            return resp.json()
        else:
            print("Update failed:", resp.status_code, resp.text)
            return None

    def get_options(self):
        """取得固定 id 的 options"""

        data = self.auth.load_local_data()
        jwt = data.get("jwt")
        if not jwt:
            return None

        url = f"{spwr_api_url}/rest/v1/{self.table}?id=eq.{Options.FIXED_ID}&select=options"
        headers = {
            "apikey": spwr_api_anon_key,
            "Authorization": f"Bearer {jwt}",
            "Content-Type": "application/json"
        }
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            if data and isinstance(data, list) and "options" in data[0]:
                json_str = data[0]["options"]
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError as e:
                    print(f"❌ 資料庫中的 options 內容不是合法的 JSON 格式。詳情: {e}")
                    return None
        else:
            print("Get failed:", resp.status_code, resp.text)
        return None

    def get_options_auto(self):
        # 自動判斷抓取 options 的來源
        # 開發時需手動添加 options_from_local: ture 至 private.josn
        # 避免頻繁 fetch
        # 產品發布時 private.josn因設定為.gitignore 且預設值不會有此 options_from_local key
        # 故產品發布時必定會抓取 web

        data = self.auth.load_local_data()
        is_options_from_local = data.get('options_from_local', False) # 是否從本地獲取 options
        if is_options_from_local:
            print('✅📂 讀取本地資料 Load options form local')
            options = self.get_local_options()
        else:
            print('✅🌎️ 讀取雲端資料 Load options form web')
            options = self.get_options()
        return options

    def pull_original(self):
        # 拉取 original 至本地
        if self.auth.is_token_valid():
            data = self.get_original()
            with open(Options.OPTIONS_PATH, "w", encoding="utf-8") as f:
                f.write(data)
            print('pull temp_options.py success.')
        else:
            print("❌，請先登入")

    def get_remote_hash(self):
        # 取得 雲端 hash
        data = self.auth.load_local_data()
        jwt = data.get("jwt")
        if not jwt:
            return None

        url = f"{spwr_api_url}/rest/v1/{self.table}?id=eq.{Options.FIXED_ID}&select=original_hash"
        headers = {
            "apikey": spwr_api_anon_key,
            "Authorization": f"Bearer {jwt}",
            "Content-Type": "application/json"
        }
        try:
            resp = requests.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                if data and isinstance(data, list) and "original_hash" in data[0]:
                    return data[0]["original_hash"]
                print("Get remote hash failed: Supabase 查詢結果格式不正確。")
            else:
                print("Get remote hash failed:", resp.status_code, resp.text)
        except requests.exceptions.RequestException as e:
            print(f"Get remote hash failed: 網路請求錯誤: {e}")
        return None

    def is_dirty(self):
        # 檢查 local_options 是否已改變
        remote_hash = self.get_remote_hash()
        if remote_hash is None:
            print("警告：無法取得遠端雜湊值，無法執行精確比對。")
            return False

        local_content = self.get_local_original()
        if local_content is None:
            print("警告：無法讀取本地檔案內容，無法執行精確比對。")
            return False

        local_hash = get_str_hash(local_content)
        return local_hash != remote_hash

opt = Options()

def pull_original():
    opt.pull_original()

def push_options():
    opt.update_options()

FUNCTION_MAP = {
    'pull': pull_original,
    'push': push_options,
}

@click.command() # 命令行入口
@click.option('-name', help='your name', required=True) # required 必要的
def main(name):
    target_func = FUNCTION_MAP.get(name)
    if target_func:
        target_func()
    else:
        error_msg = f"錯誤：找不到對應的操作 '{name}'。"
        click.echo(error_msg, err=True)
        click.echo(f"請使用以下任一選項: {', '.join(FUNCTION_MAP.keys())}", err=True)
        sys.exit(1) # 設置返回碼，讓 shell 知道程式執行失敗

# 測試用
def test1():
    print("讀取 original:")
    original = opt.get_original()
    print(original)

def test2(): # 從雲端拉取
    opt.pull_original()
    print('ok')

def test3(): # 讀取本地
    print(opt.get_local_original())

def test4(): # 儲存
    updated = opt.update_options()
    print("更新後 options:", updated)

def test5(): # 讀取雲端 options
    options = opt.get_options()
    print(options)
    print(type(options))

def test6(): # 讀取本地 options
    options = opt.get_local_options()
    print(options)
    print(type(options))

def test7(): # 讀取 option 依據設定 自動判斷抓取來源
    options = opt.get_options_auto()
    print(options)
    print(type(options))

def test8(): # 檢查是否需要更新
    if opt.is_dirty():
        print('options 已經修改尚未更新')
    else:
        print('不需要更新')

if __name__ == "__main__":
    # test6()
    main() # 會被呼叫 預設使用 main
