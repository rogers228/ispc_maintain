if True:
    import sys
    import os
    import time
    import json

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

    sys.path.append(os.path.join(ROOT_DIR, "system"))
    from share_qt5 import *
    from tool_auth import AuthManager
    from tool_gui import hide_cmd_window

    sys.path.append(os.path.join(ROOT_DIR, 'gui', 'us01'))
    from form_us01 import Ui_MainWindow

    # 引用其他作業
    sys.path.append(os.path.join(ROOT_DIR, 'gui', 'us05'))
    from us05 import MainWindow as MainWindow_us05

class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow();
        self.ui.setupUi(self) # 載入ui
        self.setWindowTitle(f'ispc maintain')
        self.resize(600, 450)  # 設定視窗大小

        # 建立 Model
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["選擇作業"]) # root

        # 導入 dict
        data = {
            "使用者": {
                "使用者登入": self.action_login,
                "登出": self.action_signout,
                "結束": self.action_exit,
            },
            "產品資料": {
                "產品建立作業": self.action_create_product,
                "產品維護作業": self.action_edit_product,
                "使用者查詢": self.action_query_user,
                 },
            "系統": {
                "設定": self.action_system_settings,
                "權限設定作業": self.action_permission_settings,
            },
        }

        self.dict_to_tree(data, self.model.invisibleRootItem()) # 遞迴轉換 dict → QTreeView

        self.ui.treeView.setModel(self.model) # 綁定model 到 TreeView
        self.ui.treeView.expandAll() # 展開全部
        self.ui.treeView.setHeaderHidden(True) # 隱藏root
        self.ui.treeView.doubleClicked.connect(self.on_tree_double_clicked) # 綁定雙擊事件

        # === 狀態列整合 AuthManager ===
        self.auth = AuthManager()
        data = self.auth.load_local_data()
        full_name = data.get("full_name", "未設定")
        self.label_user = QLabel(f"使用者: {full_name}")
        self.label_status = QLabel("登入狀態: 檢查中...")

        # 加入狀態列
        self.ui.statusbar.addWidget(self.label_user)
        self.ui.statusbar.addPermanentWidget(self.label_status)  # 永遠在右側

        # 啟動時檢查 & 刷新
        self.refresh_auth_status()

        # 啟動計時器：每 1 小時執行一次刷新程序
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_auth_status)
        self.timer.start(3600 * 1000)  # 1 小時 = 3600 秒

        # 子表單
        self.us05 = None

    def closeEvent(self, event):
        reply = QMessageBox.question(self, "結束", "您確定要結束退出嗎？",   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()  # 允許關閉
        else:
            event.ignore()  # 阻止關閉

        # 如果有子窗體開啟，一併關閉子窗體
        child_windows = [self.us05]
        for window in child_windows:
            if window and isinstance(window, QWidget) and window.isVisible():
                window.close()

    def dict_to_tree(self, data_dict, parent):
        """遞迴將 dict 加到 QTreeView"""
        icon_form = QIcon(os.path.join(ROOT_DIR, 'system', 'icons', 'form4.png'))

        for key, value in data_dict.items():
            item = QStandardItem(key)

            # 如果 value 是可呼叫物件 (function)，加 icon
            if callable(value):
                item.setData(value, Qt.UserRole)  # 存函式指標
                item.setIcon(icon_form)  # 使用系統預設 icon
            else:
                # 非可呼叫：文字顏色設為灰色
                item.setForeground(QBrush(QColor("gray")))

            parent.appendRow(item)
            if isinstance(value, dict) and value:
                self.dict_to_tree(value, item)

    def on_tree_double_clicked(self, index):
        """處理 TreeView 雙擊事件"""
        item = self.model.itemFromIndex(index)
        func = item.data(Qt.UserRole)
        if callable(func):  # 如果 value 是函式
            func()  # 執行對應的功能

    # === 刷新程序 ===
    def refresh_auth_status(self):
        """檢查是否過期，必要時刷新，並更新狀態列"""
        print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), 'refresh_auth_status...')

        if self.auth.is_token_valid():
            self.label_status.setText("登入狀態: 已登入")
        else:
            if self.auth.refresh_session():
                self.label_status.setText("登入狀態: 已登入(刷新)")
            else:
                self.label_status.setText("登入狀態: 已登出")

    # === 以下是功能函式 ===
    def action_login(self):
        print("執行 → 使用者登入程序")
        self.us05 = MainWindow_us05() # 材質設定
        self.us05.login_success.connect(self.on_login_success)  # 綁定事件
        self.us05.show()

    def on_login_success(self, user_data):
        """處理登入成功後更新狀態列"""
        self.label_user.setText(f"使用者: {user_data.get('full_name', '')}")
        self.label_status.setText("登入狀態: 已登入")

    def action_signout(self):
        reply = QMessageBox.question(self, "登出", "您確定要登出嗎？",   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if self.auth.logout():
                QMessageBox.information(self, "登出", "您已成功登出")
                # 更新狀態列
                self.label_user.setText("使用者: 未設定")
                self.label_status.setText("登入狀態: 已登出")
            else:
                QMessageBox.warning(self, "錯誤", "登出失敗，請稍後再試")

    def action_exit(self):
        reply = QMessageBox.question(self, "結束", "您確定要結束退出嗎？",   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            sys.exit() #正式結束程式  需要導入sys

    def action_create_product(self):
        print("執行 → 產品建立作業程序")

    def action_edit_product(self):
        print("執行 → 產品維護作業程序")

    def action_query_user(self):
        print("執行 → 使用者查詢程序")

    def action_system_settings(self):
        print("執行 → 系統設定程序")

    def action_permission_settings(self):
        print("執行 → 權限設定作業程序")

def main():
    if True: # 非開發 隱藏命令視窗  判斷尚未完成
        hide_cmd_window()

    app = QApplication(sys.argv)
    argv1 = sys.argv[1] if len(sys.argv) > 1 else "no argv" # 預留參數接口
    # print('argv1:', argv1)

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()