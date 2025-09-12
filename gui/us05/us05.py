if True:
    import sys
    import os
    import json
    from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
    from supabase import create_client, Client

    print("Python executable:", sys.executable) # 目前執行的python路徑 用來判斷是否是虛擬環境python 或 本機python

    def find_project_root(start_path=None, project_name="ispc_maintain"):
        """從指定路徑往上找，直到找到名稱為 project_name 的資料夾"""
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

    ROOT_DIR = find_project_root() # 專案 root
    PRIVATE_JSON = os.path.join(ROOT_DIR, "system", "private.json") # private.json 完整路徑

    sys.path.append(os.path.join(ROOT_DIR, "system"))
    from tool_auth import AuthManager

    sys.path.append(os.path.join(ROOT_DIR, 'gui', 'us05'))
    from form_us05 import Ui_MainWindow

class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow();
        self.ui.setupUi(self) # 載入ui
        self.setWindowTitle(f'Login')
        self.resize(450, 250)  # 設定視窗大小

        self.auth = AuthManager()
        # 載入本地設定，如果有就帶入初始值
        self.user_data = self.load_local_data()
        self.populate_fields()

        # 連接 Login 按鈕
        self.ui.login.clicked.connect(self.handle_login)

    def load_local_data(self):
        """讀取本地 private.json"""
        if os.path.exists(PRIVATE_JSON):
            try:
                with open(PRIVATE_JSON, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                QMessageBox.warning(self, "Warning", f"讀取本地設定失敗:\n{e}")
                return {}
        return {}

    def populate_fields(self):
        """將本地資料帶入欄位"""
        self.ui.email.setText(self.user_data.get("email", ""))
        self.ui.password.setText(self.user_data.get("password", ""))
        self.ui.full_name.setText(self.user_data.get("full_name", ""))

    def handle_login(self):
        email = self.ui.email.text()
        password = self.ui.password.text()
        full_name = self.ui.full_name.text()

        # 先儲存資訊
        self.auth.save_local_data({
            "email": email,
            "password": password,
            "full_name": full_name
        })

        if self.auth.login(email, password):
            QMessageBox.information(self, "成功", "登入成功！JWT 已儲存")
        else:
            QMessageBox.warning(self, "錯誤", "登入失敗，請檢查帳號密碼")

def main():
    app = QApplication(sys.argv)
    # argv1 = sys.argv[1] if len(sys.argv) > 1 else "no argv" # 預留參數接口
    # print('argv1:', argv1)

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()