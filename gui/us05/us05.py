if True:
    import sys
    import os

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
    sys.path.append(os.path.join(ROOT_DIR, "system"))
    from share_qt5 import *
    from tool_auth import AuthManager

    sys.path.append(os.path.join(ROOT_DIR, 'gui', 'us05'))
    from form_us05 import Ui_MainWindow

class MainWindow(QMainWindow):

    login_success = pyqtSignal(dict)  # 宣告 signal，傳回使用者資料

    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow();
        self.ui.setupUi(self) # 載入ui
        self.setWindowTitle('使用者登入')
        self.resize(550, 230)  # 設定視窗大小

        self.auth = AuthManager()
        self.user_data = self.auth.load_local_data() # 載入本地設定，如果有就帶入初始值
        self.populate_fields()

        self.ui.login.clicked.connect(self.handle_login) # 連接 Login 按鈕

    def populate_fields(self):
        """將本地資料帶入欄位"""
        self.ui.email.setText(self.user_data.get("email", ""))
        self.ui.password.setText(self.user_data.get("password", ""))
        self.ui.full_name.setText(self.user_data.get("full_name", ""))

    def handle_login(self):
        self.ui.login.setEnabled(False)

        email = self.ui.email.text().strip()
        password = self.ui.password.text().strip()
        full_name = self.ui.full_name.text().strip()

        if not email:
            QMessageBox.warning(self, "輸入錯誤", "email 不可為空白。")
            self.ui.login.setEnabled(True)
            return

        if not password:
            QMessageBox.warning(self, "輸入錯誤", "password 不可為空白。")
            self.ui.login.setEnabled(True)
            return

        if not full_name:
            QMessageBox.warning(self, "輸入錯誤", "full_name 不可為空白。")
            self.ui.login.setEnabled(True)
            return

        # 先儲存資訊
        self.auth.save_local_data({
            "email": email,
            "password": password,
            "full_name": full_name
        })

        if self.auth.login(email, password):
            # QMessageBox.information(self, "成功", "登入成功！JWT 已儲存")
            # 🔑 登入成功後發射訊號
            self.login_success.emit({
                "email": email,
                "full_name": full_name
            })
            self.close()  # 關閉登入視窗
        else:
            QMessageBox.warning(self, "錯誤", "登入失敗，請檢查帳號密碼")
            self.ui.login.setEnabled(True)

def main():
    app = QApplication(sys.argv)
    # argv1 = sys.argv[1] if len(sys.argv) > 1 else "no argv" # 預留參數接口
    # print('argv1:', argv1)

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()