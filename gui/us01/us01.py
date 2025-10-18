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
    from tool_options import Options

    sys.path.append(os.path.join(ROOT_DIR, 'gui', 'us01'))
    from form_us01 import Ui_MainWindow

    # 引用其他作業
    sys.path.append(os.path.join(ROOT_DIR, 'gui', 'us05'))
    from us05 import MainWindow as MainWindow_us05
    sys.path.append(os.path.join(ROOT_DIR, 'gui', 'us09'))
    from us09 import MainWindow as MainWindow_us09

# === 新增自訂角色定義：用於儲存多筆資料 ===
ITEM_ACTION_ROLE = Qt.UserRole     # 用於儲存要執行的函式  指標
ITEM_UID_ROLE = Qt.UserRole + 1    # 用於儲存額外的 UID   指標

class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow();
        self.ui.setupUi(self) # 載入ui
        self.setWindowTitle(f'ispc maintain ({ISPC_MAINTAIN_VERSION})')
        self.resize(712, 450)  # 設定視窗大小

        self.auth = AuthManager()
        self.opt = Options()
        self.us05 = None    # 子表單 登入
        self.us09 = None    # 子表單 設定
        self.tree_data = {} # 選單資料 dict

        # 狀態列
        data = self.auth.load_local_data()
        full_name = data.get("full_name", "未設定")
        self.label_user = QLabel(f"使用者: {full_name}")
        self.label_status = QLabel("登入狀態: 檢查中...")
        self.ui.statusbar.addWidget(self.label_user)
        self.ui.statusbar.addPermanentWidget(self.label_status)  # 永遠在右側
        self.refresh_auth_status() # 刷新狀態

        # 建立選單 Model
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["選擇作業"]) # root
        self.load_tree_system()  # 讀取系統選單
        self.load_tree_product() # 讀取產品選單
        self.display_tree(self.tree_data, self.model.invisibleRootItem()) # 展示選單
        self.ui.treeView.activated.connect(self.handle_tree_activated) # 連接 activated 信號到處理函式 (當項目被點擊或啟動時觸發)
        self.ui.treeView.setModel(self.model)  # 綁定model 到 TreeView
        self.ui.treeView.setHeaderHidden(True) # 隱藏root
        self.ui.treeView.expandAll() # 展開全部
        self.ui.treeView.selectionModel().currentChanged.connect(self.handle_tree_selection_changed) # 選取事件

        # button
        self.ui.pd_edit.clicked.connect(self.handle_pd_edit)

        # 啟動計時器：每 1 小時執行一次刷新程序
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_auth_status)
        self.timer.start(3600 * 1000)  # 1 小時 = 3600 秒

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

    def load_tree_system(self):
        # 讀取系統選單
        self.tree_data.pop('系統', 0) # clean
        self.tree_data['系統'] = {
            "使用者登入": {'action': self.action_login},
            "設定":      {'action': self.action_settings},
            "重新啟動":   {'action': self.action_restart},
            "登出":      {'action': self.action_signout},
            "－－－－－－－－－－": None,
            "結束":      {'action': self.action_exit},
        }

    def load_tree_product(self):
        # 讀取產品選單
        # 測試動態讀取參數 添加至 tree
        # print('load product...')
        self.tree_data.pop('產品資料', 0) # clean
        if not self.auth.is_token_valid():
            print('尚未登入無法讀取產品資料')
            return

        data = self.auth.load_local_data()
        user = data.get("email")
        options = self.opt.get_options_auto() # 讀取 option 依據設定 自動判斷抓取來源

        # 依登入 uses, options, 轉換為僅顯示有權限的產品資料至選單
        permissions = options['permissions'][user] # # 抓取權限 可在 temp_options.py 測試
        # print('permissions:', permissions)
        dic_p = {}
        for e in permissions:
            pdno = next(iter(e.keys()))
            attt = next(iter(e.values()))
            # print(pdno)
            # print(attt.get('name'))
            # print(attt.get('uid'))
            dic_p[attt.get('name')] = {'action': self.action_test, 'uid': attt.get('uid')}

        self.tree_data['產品資料']  = dic_p

        # 標準格式範本
        # self.tree_data['產品資料'] = {
        #     'A': {'action': self.action_test, 'uid': '產品A的uuid'},
        #     'B': {'action': self.action_test, 'uid': '產品B的uuid'},
        # }

    def display_tree(self, data_dict, parent):
        # 展示選單
        # 遞迴將 dict 加到 QTreeView，並將 action 和 uid 儲存在不同的 UserRole 中
        if parent == self.model.invisibleRootItem(): # 僅在頂層調用時執行
            parent.removeRows(0, parent.rowCount()) # 清除資料後再執行遞迴

        icon_form = QIcon(os.path.join(ROOT_DIR, 'system', 'icons', 'form4.png'))
        icon_exit = QIcon(os.path.join(ROOT_DIR, 'system', 'icons', 'exit.png'))

        for key, value in data_dict.items():
            item = QStandardItem(key)
            is_action_item = False

            # 檢查 value 是否為包含 'action' 的字典 (新的結構)
            if isinstance(value, dict) and 'action' in value:
                action_func = value['action']
                item_uid = value.get('uid') # 嘗試獲取 'uid'，若無則為 None

                # 儲存函式指標 (第一個資料：ITEM_ACTION_ROLE)
                item.setData(action_func, ITEM_ACTION_ROLE)

                # 儲存 UID (第二個資料：ITEM_UID_ROLE)
                if item_uid is not None:
                    item.setData(item_uid, ITEM_UID_ROLE)

                is_action_item = True

            # 處理非字典或非動作項目的顯示設定 (例如分隔線或父節點)
            if is_action_item:
                if key == '結束':
                    item.setIcon(icon_exit)
                else:
                    item.setIcon(icon_form) # 使用系統預設 icon
            else:
                # 非動作或父節點：文字顏色設為灰色
                item.setForeground(QBrush(QColor("gray")))

            parent.appendRow(item)

            # 遞迴處理子節點：只有當 value 是字典，且它不是一個「葉子動作節點」（即不包含 'action' 鍵）時，才進行遞迴。
            if isinstance(value, dict) and 'action' not in value and value:
                self.display_tree(value, item)

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

    def action_login(self, item_text=None, item_uid=None):
        self.us05 = MainWindow_us05() # 登入
        self.us05.login_success.connect(self.on_login_success)  # 綁定事件
        self.us05.show()

    def on_login_success(self, user_data):
        """處理登入成功後更新狀態列"""
        self.load_tree_product() # 讀取產品至選單
        self.display_tree(self.tree_data, self.model.invisibleRootItem()) # 展示選單
        self.ui.treeView.expandAll() # 展開全部
        self.label_user.setText(f"使用者: {user_data.get('full_name', '')}")
        self.label_status.setText("登入狀態: 已登入")

    def action_signout(self, item_text=None, item_uid=None):
        reply = QMessageBox.question(self, "登出", "您確定要登出嗎？",   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if self.auth.logout():
                QMessageBox.information(self, "登出", "您已成功登出")
                # 更新狀態列
                self.load_tree_product() # 讀取產品至選單
                self.display_tree(self.tree_data, self.model.invisibleRootItem()) # 展示選單
                self.ui.treeView.expandAll() # 展開全部
                self.label_user.setText("使用者: 未設定")
                self.label_status.setText("登入狀態: 已登出")
            else:
                QMessageBox.warning(self, "錯誤", "登出失敗，請稍後再試")

    def action_exit(self, item_text=None, item_uid=None):
        reply = QMessageBox.question(self, "結束", "您確定要結束退出嗎？",   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            sys.exit() #正式結束程式  需要導入sys

    def action_restart(self, item_text=None, item_uid=None):
        os.execl(sys.executable, sys.executable, *sys.argv) # 重新啟動

    def action_settings(self, item_text=None, item_uid=None):
        self.us09 = MainWindow_us09() # 設定
        self.us09.show()

    def handle_tree_selection_changed(self, current_index, previous_index):
        index = current_index
        is_enable = False # 預設為禁用
        if index.isValid():
            parent_index = index.parent()
            if parent_index.isValid() and parent_index != self.model.invisibleRootItem().index(): # 確保有父節點且不是隱藏的根節點
                parent_text = parent_index.data(Qt.DisplayRole)
                if parent_text == '產品資料':
                    is_enable = True
        self.ui.pd_edit.setEnabled(is_enable)
        self.ui.pd_check.setEnabled(is_enable)
        self.ui.pd_upload.setEnabled(is_enable)
        self.ui.pd_release.setEnabled(is_enable)

    def handle_tree_activated(self, index):
        item = self.model.itemFromIndex(index)
        if item is None:
            return
        action_func = item.data(ITEM_ACTION_ROLE) # 獲取儲存的函式
        item_text = item.text()                   # 獲取顯示的文字
        item_uid = item.data(ITEM_UID_ROLE)       # 獲取儲存的 UID

        # 執行函式並傳遞 item_text
        if callable(action_func):
            try:
                action_func(item_text, item_uid) # 嘗試傳遞兩個參數 (text, uid)
            except TypeError:
                # 處理沒有設計 uid 參數的舊函式 (例如 action_login 只接收 text 或無參數)
                try:
                    action_func(item_text) # 嘗試傳遞一個參數 (text)
                except TypeError:
                    action_func() # 處理沒有設計參數的舊函式
            except Exception as e:
                print(f"執行功能 '{item_text}' 時發生錯誤: {e}")

    def handle_pd_edit(self):
        index = self.ui.treeView.selectionModel().currentIndex()
        if not index.isValid():
            return # 未選取任何項目。
        selected_text = index.data(Qt.DisplayRole)
        selected_uid = index.data(ITEM_UID_ROLE)

        parent_index = index.parent()
        if parent_index.isValid() and parent_index != self.model.invisibleRootItem().index(): # 檢查是否為頂層項目，避免獲取到 root 欄位名稱
            parent_text = parent_index.data(Qt.DisplayRole)
            if parent_text == '產品資料':
                print(f"\n--- 編輯按鈕點擊 ---")
                print(f"選取的項目: {selected_text}")
                print(f"項目的 UID: {selected_uid}") # 這裡就能獲取 UID 了！
                print("--------------------")


    def action_test(self, item_text, item_uid):
        print("\n=== 執行 action_test ===")
        print(f"點擊的項目文字是: {item_text}")
        print(f"該產品的 UID 是: {item_uid}")
        print("========================")

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