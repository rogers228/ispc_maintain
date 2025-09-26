if True:
    import sys, os
    import json
    import time
    from supabase import create_client, Client

    # 專案 root 下的 private.json
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
    PRIVATE_JSON = os.path.join(ROOT_DIR, "system", "private.json")

    sys.path.append(os.path.join(ROOT_DIR, "system"))
    from config import spwr_api_url, spwr_api_anon_key

class AuthManager:
    def __init__(self):
        # 直接讀 config 建立 supabase client
        self.db: Client = create_client(spwr_api_url, spwr_api_anon_key)
        self.session = None
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
        os.makedirs(os.path.dirname(PRIVATE_JSON), exist_ok=True)
        with open(PRIVATE_JSON, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def login(self, email, password):
        try:
            result = self.db.auth.sign_in(email=email, password=password)
            access_token = getattr(result, "access_token", None)
            refresh_token = getattr(result, "refresh_token", None)
            expires_at = getattr(result, "expires_at", None)
            user = getattr(result, "user", None)

            if access_token:
                self.session = result
                self.refresh_token = refresh_token

                # 存 local JSON
                self.save_local_data({
                    "jwt": access_token,
                    "refresh_token": refresh_token,
                    "expires_at": expires_at,
                    "email": email
                })

                print("login success")
                print("access_token:", access_token[:30], "...")
                return True
            else:
                # session 為 None，檢查 email 驗證
                if user and getattr(user, "email_confirmed_at", None) is None:
                    print("登入失敗: Email 尚未驗證")
                else:
                    print("登入失敗: 未知原因")
                return False

        except Exception as e:
            print("Login failed:", e)
            return False


    def is_token_valid(self):
        """檢查 access_token 是否過期"""
        if not self.session:
            # 嘗試從 local JSON 讀取
            data = self.load_local_data()
            expires_at = data.get("expires_at", 0)
            now = int(time.time())
            return now < expires_at
        now = int(time.time())
        return now < self.session.expires_at

    def refresh_session(self):
        """使用 refresh_token 取得新的 access_token"""
        if not self.refresh_token:
            print("No refresh token available.")
            return False
        try:
            session = self.db.auth.refresh_session(self.refresh_token)
            if session and session.access_token:
                self.session = session
                self.refresh_token = session.refresh_token

                # 更新 local JSON
                self.save_local_data({
                    "jwt": session.access_token,
                    "refresh_token": session.refresh_token,
                    "expires_at": session.expires_at
                })
                return True
            else:
                print("Refresh failed: no access_token returned")
                return False
        except Exception as e:
            print("Refresh failed:", e)
            return False

    def logout(self):
        """登出：清理 session 與本地紀錄"""
        try:
            # 嘗試通知 Supabase 登出（若 API 支援）
            try:
                self.db.auth.sign_out()
            except Exception as e:
                print("Supabase sign_out 警告:", e)

            # 清掉內存的 session
            self.session = None
            self.refresh_token = None

            # 更新 local JSON → 移除登入相關資訊
            data = self.load_local_data()
            for key in ["jwt", "refresh_token", "expires_at"]:
                data.pop(key, None)
            self.save_local_data(data)

            print("Logout success ✅")
            return True

        except Exception as e:
            print("Logout failed ❌:", e)
            return False

def test1():
    auth = AuthManager()
    data = auth.load_local_data()
    email = data.get('email')
    password = data.get('password')
    auth.login(email, password)

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