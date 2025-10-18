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
    PRIVATE_JSON = os.path.join(ROOT_DIR, "system", "private.json")

    sys.path.append(os.path.join(ROOT_DIR, "system"))
    from config import spwr_api_url, spwr_api_anon_key

class AuthManager:
    def __init__(self):
        self.session_data = None  # 存放登入後回傳的 json
        self.refresh_token = None

    def load_local_data(self):
        if os.path.exists(PRIVATE_JSON):
            try:
                with open(PRIVATE_JSON, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_local_data(self, extra=None):
        data = self.load_local_data()
        if extra:
            data.update(extra)
        # 找到變數 PRIVATE_JSON 所指檔案的父目錄路徑
        # 然後創建這個目錄（包括所有必要的上層目錄），如果目錄已經存在，則不要報錯。
        os.makedirs(os.path.dirname(PRIVATE_JSON), exist_ok=True)
        with open(PRIVATE_JSON, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def login(self, email, password):
        """
        使用 email + password 登入 Supabase
        """
        try:
            url = f"{spwr_api_url}/auth/v1/token?grant_type=password"
            headers = {
                "apikey": spwr_api_anon_key,
                "Content-Type": "application/json",
            }
            payload = {"email": email, "password": password}

            res = requests.post(url, headers=headers, json=payload)

            if res.status_code == 200:
                result = res.json()
                access_token = result.get("access_token")
                refresh_token = result.get("refresh_token")
                expires_in = result.get("expires_in", 3600)
                user = result.get("user")

                if access_token:
                    self.session_data = result
                    self.refresh_token = refresh_token
                    expires_at = int(time.time()) + expires_in

                    # 存 local JSON
                    self.save_local_data({
                        "jwt": access_token,
                        "refresh_token": refresh_token,
                        "expires_at": expires_at,
                        "email": email,
                        "password": password,  # ⚠️ 可選，建議不要存明碼
                    })

                    print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), "login success")
                    print("access_token:", access_token[:30], "...")
                    return True
                else:
                    if user and not user.get("email_confirmed_at"):
                        print("登入失敗: Email 尚未驗證")
                    else:
                        print("登入失敗: 未知原因")
                    return False
            else:
                print("Login HTTP error:", res.status_code, res.text)
                return False

        except Exception as e:
            print("Login failed:", e)
            return False

    def is_token_valid(self):
        """檢查 access_token 是否過期"""
        data = self.load_local_data()
        expires_at = data.get("expires_at", 0)
        now = int(time.time())
        return now < expires_at

    def refresh_session(self):
        data = self.load_local_data()
        refresh_token = data.get("refresh_token")
        if not refresh_token:
            print("No refresh_token found in local data")
            return False

        print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), "refresh_session: loaded refresh_token from file (len):", len(refresh_token))
        try:
            url = f"{spwr_api_url}/auth/v1/token?grant_type=refresh_token"
            headers = {
                "apikey": spwr_api_anon_key,
                "Content-Type": "application/json",
            }
            payload = {"refresh_token": refresh_token}

            print("Attempting refresh (requests) with refresh_token len:", len(refresh_token))
            res = requests.post(url, headers=headers, json=payload)

            if res.status_code == 200:
                new_data = res.json()
                print("Refresh success ✅ response keys:", list(new_data.keys()))
                self.save_local_data({
                    "jwt": new_data["access_token"],
                    "refresh_token": new_data["refresh_token"],
                    "expires_at": int(time.time()) + new_data["expires_in"]
                })
                return True
            else:
                print("Refresh HTTP error:", res.status_code, res.text)
                return False
        except Exception as e:
            print("Exception in refresh_session:", e)
            return False

    def logout(self):
        """登出：清理 session 與本地紀錄"""
        print('logout...')
        try:
            # Supabase 沒有明確的 logout API，這裡直接清掉本地資訊即可
            self.session_data = None
            self.refresh_token = None

            # 更新 local JSON → 移除登入相關資訊
            data = self.load_local_data()
            data['jwt'] = None
            data['refresh_token'] = None
            data['expires_at'] = 0 # int  is_token_valid()才會正確
            self.save_local_data(data)

            print("Logout success ✅ (local only)")
            return True

        except Exception as e:
            print("Logout failed ❌:", e)
            return False

def test1():
    auth = AuthManager()
    data = auth.load_local_data()
    email = data.get('email')
    password = data.get('password')

    if email and password:
        auth.login(email, password)
    else:
        print("尚未設定 email/password，請先登入")

def test2():
    auth = AuthManager()
    data = auth.load_local_data()

    # 沒有 email/refresh_token，無法檢查
    if not data.get("email") or not data.get("refresh_token"):
        print("尚未登入，請先執行 login")
        return

    # 檢查 access_token 是否有效
    if auth.is_token_valid():
        print("Token 仍有效 ✅")
    else:
        print("Token 已失效，嘗試刷新 ⏳")
        if auth.refresh_session():
            print("Refresh 成功 ✅，新的 access_token 已更新")
        else:
            print("Refresh 失敗 ❌，請重新登入")

if __name__ == '__main__':
    test2()