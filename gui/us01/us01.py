if True:
    import sys
    import os
    import time
    import json

    # print("Python executable:", sys.executable) # 目前執行的python路徑 用來判斷是否是虛擬環境python 或 本機python

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
    from tool_launch import startup
    from config import ISPC_MAINTAIN_VERSION
    import tool_options

    sys.path.append(os.path.join(ROOT_DIR, 'gui', 'us01'))
    from form_us01 import Ui_MainWindow

    # 引用其他作業
    sys.path.append(os.path.join(ROOT_DIR, 'gui', 'us05'))
    from us05 import MainWindow as MainWindow_us05
    sys.path.append(os.path.join(ROOT_DIR, 'gui', 'us09'))
    from us09 import MainWindow as MainWindow_us09

class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow();
        self.ui.setupUi(self) # 載入ui
        self.setWindowTitle(f'ispc maintain ({ISPC_MAINTAIN_VERSION})')
        self.resize(600, 450)  # 設定視窗大小

        # 建立 Model
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["選擇作業"]) # root

        # 導入 dict
        tree = {
            "系統": {
                "使用者登入": self.action_login,
                "設定": self.action_settings,
                "重新啟動": self.restart,
                "登出": self.action_signout,
                "－－－－－－－－－－": None,
                "結束": self.action_exit,
            }
        }

        # 測試動態讀取參數 添加至 tree
        # self.opt = tool_options.Options()
        # options = self.opt.get_options()
        # if options:
        #     print(options)
        tree['產品資料'] = {
            'A': self.action_test,
            'B': self.action_test,
        }

        self.dict_to_tree(tree, self.model.invisibleRootItem()) # 遞迴轉換 dict → QTreeView
        self.ui.treeView.activated.connect(self.handle_tree_activated) # 連接 activated 信號到處理函式 (當項目被點擊或啟動時觸發)

        self.ui.treeView.setModel(self.model) # 綁定model 到 TreeView
        self.ui.treeView.expandAll() # 展開全部
        self.ui.treeView.setHeaderHidden(True) # 隱藏root
        self.ui.treeView.selectionModel().currentChanged.connect(self.handle_tree_selection_changed) # 選取事件

        self.ui.pd_edit.clicked.connect(self.handle_pd_edit)

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
        self.us09 = None

    def closeEvent(self, event):
        reply = QMessageBox.question(self, "結束", "您確定要結束退出嗎？",   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()  # 允許關閉
        else:
            event.ignore()  # 阻止關閉

        # 如果有子窗體開啟，一併關閉子窗體
        child_windows = [self.us05, self.us09]
        for window in child_windows:
            if window and isinstance(window, QWidget) and window.isVisible():
                window.close()

    def dict_to_tree(self, data_dict, parent):
        # 遞迴將 dict 加到 QTreeView
        if parent == self.model.invisibleRootItem(): # 僅在頂層調用時執行
            parent.removeRows(0, parent.rowCount()) # 清除資料後再執行遞迴

        icon_form = QIcon(os.path.join(ROOT_DIR, 'system', 'icons', 'form4.png'))
        icon_exit = QIcon(os.path.join(ROOT_DIR, 'system', 'icons', 'exit.png'))

        for key, value in data_dict.items():
            item = QStandardItem(key)

            # 如果 value 是可呼叫物件 (function)，加 icon
            if callable(value):
                item.setData(value, Qt.UserRole)  # 存函式指標
                if key == '結束':
                    item.setIcon(icon_exit)
                else:
                    item.setIcon(icon_form)  # 使用系統預設 icon

            else:
                # 非可呼叫：文字顏色設為灰色
                item.setForeground(QBrush(QColor("gray")))

            parent.appendRow(item)
            if isinstance(value, dict) and value:
                self.dict_to_tree(value, item)

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
        # print("執行 → 使用者登入程序")
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

    def restart(self):
        # 重新啟動
        os.execl(sys.executable, sys.executable, *sys.argv)

    def action_settings(self):
        # print("執行 → 系統設定程序")
        self.us09 = MainWindow_us09() # 材質設定
        self.us09.show()

    def handle_tree_selection_changed(self, current_index, previous_index):
        index = current_index
        if not index.isValid():
            return # 未選取任何項目。
        # selected_text = index.data(Qt.DisplayRole)
        parent_index = index.parent()
        if parent_index.isValid() and parent_index != self.model.invisibleRootItem().index():
            parent_text = parent_index.data(Qt.DisplayRole)
            if parent_text == '產品資料':
                self.ui.pd_edit.setEnabled(True)
                self.ui.pd_check.setEnabled(True)
                self.ui.pd_upload.setEnabled(True)
                self.ui.pd_release.setEnabled(True)
            else:
                self.ui.pd_edit.setEnabled(False)
                self.ui.pd_check.setEnabled(False)
                self.ui.pd_upload.setEnabled(False)
                self.ui.pd_release.setEnabled(False)

    def handle_tree_activated(self, index):
        item = self.model.itemFromIndex(index)
        if item is None:
            return

        # 獲取儲存的函式 (UserRole 儲存著要執行的 self.action_xxx 函式)
        action_func = item.data(Qt.UserRole)
        item_text = item.text()

        # 執行函式並傳遞 item_text
        if callable(action_func):
            try:
                action_func(item_text) # 傳遞 item_text 作為參數
            except TypeError:
                action_func() # 處理沒有設計參數的舊函式 (例如 self.action_login)，以確保向下兼容
            except Exception as e:
                print(f"執行功能 '{item_text}' 時發生錯誤: {e}")

    def handle_pd_edit(self):
        index = self.ui.treeView.selectionModel().currentIndex()
        if not index.isValid():
            return # 未選取任何項目。
        selected_text = index.data(Qt.DisplayRole)
        parent_index = index.parent()
        if parent_index.isValid() and parent_index != self.model.invisibleRootItem().index(): # 檢查是否為頂層項目，避免獲取到 root 欄位名稱
            parent_text = parent_index.data(Qt.DisplayRole)
            if parent_text == '產品資料':
                print(f"選取的項目: {selected_text}")


    def action_test(self, item_text):
        print(f"執行測試動作，點擊的項目文字是: {item_text}")

def main():
    startup() # 正常啟動
    app = QApplication(sys.argv)
    argv1 = sys.argv[1] if len(sys.argv) > 1 else "no argv" # 預留參數接口
    # print('argv1:', argv1)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()