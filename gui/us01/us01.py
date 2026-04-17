# us01.py
if True:
    import sys
    import os
    import time
    import json

    # print("🚀 Python executable:", sys.executable) # 目前執行的python路徑 用來判斷是否是虛擬環境python 或 本機python

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
    from config import ISPC_MAINTAIN_VERSION
    from config_web import SPECIC_DOMAIN
    from share_qt5 import *
    from tool_auth import AuthManager

    from tool_options import Options
    from tool_permissions import PermissionsAdministrator
    from tool_pd_storage import ProductStorage
    from tool_pd_jogging import ProductCheck
    from tool_pd_release import ProductRelease
    from tool_company import Company
    from tool_comp_jogging import CompanyCheck
    from tool_msgbox import error, warning
    from tool_db_snapshot import SnapshotManager

    sys.path.append(os.path.join(ROOT_DIR, 'gui', 'us01'))
    from form_us01 import Ui_MainWindow

    # 引用其他作業
    sys.path.append(os.path.join(ROOT_DIR, 'gui', 'us05'))
    from us05 import MainWindow as MainWindow_us05
    sys.path.append(os.path.join(ROOT_DIR, 'gui', 'us07'))
    from us07 import MainWindow as MainWindow_us07
    sys.path.append(os.path.join(ROOT_DIR, 'gui', 'us09'))
    from us09 import MainWindow as MainWindow_us09
    sys.path.append(os.path.join(ROOT_DIR, 'gui', 'us15'))
    from us15 import MainWindow as MainWindow_us15
    sys.path.append(os.path.join(ROOT_DIR, 'gui', 'us23'))
    from us23 import MainWindow as MainWindow_us23

# === 新增自訂角色定義：用於儲存多筆資料 ===
ITEM_ACTION_ROLE = Qt.UserRole     # 用於儲存要執行的函式  指標
ITEM_UID_ROLE = Qt.UserRole + 1    # 用於儲存額外的 UID   指標

class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow();
        self.ui.setupUi(self) # 載入ui
        self.setWindowTitle(f'ispc maintain ({ISPC_MAINTAIN_VERSION})')
        self.resize(799, 460)  # 設定視窗大小

        self.auth = AuthManager()
        self.opt = Options()
        self.pa = PermissionsAdministrator()
        self.ps = ProductStorage()
        self.comp = Company()
        self.pr = ProductRelease()
        self.sn = SnapshotManager()

        self.us05 = None    # 子表單 登入
        self.us07 = None    # 子表單 檢視
        self.us09 = None    # 子表單 設定
        self.us15 = None    # 子表單 檔案
        self.us23 = None    # 子表單 文章

        self.options = self.opt.get_options_auto() # 讀取 option 依據設定 自動判斷抓取來源

        self.tree_data = {} # 選單資料 dict
        self.product_sheet = {} # 產品小抄 {uid: name}
        self.company_sheet = {} # 公司小抄 {uid: name}

        # 狀態列
        data = self.auth.load_local_data()
        full_name = data.get("full_name", "未設定")
        self.email = data.get("email", "") # 使用者 email
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
        self.load_tree_company() # 讀取公司選單
        self.display_tree(self.tree_data, self.model.invisibleRootItem()) # 展示選單
        self.ui.treeView.activated.connect(self.handle_tree_activated) # 連接 activated 信號到處理函式 (當項目被點擊或啟動時觸發)
        self.ui.treeView.setModel(self.model)  # 綁定model 到 TreeView

        self.ui.treeView.setContextMenuPolicy(Qt.CustomContextMenu) # 設定右鍵選單政策
        self.ui.treeView.customContextMenuRequested.connect(self.show_tree_context_menu)

        self.ui.treeView.setHeaderHidden(True) # 隱藏root
        self.ui.treeView.expandAll() # 展開全部
        self.ui.treeView.selectionModel().currentChanged.connect(self.handle_tree_selection_changed) # 選取事件

        if True: # button
            icon_edit = QIcon(os.path.join(ROOT_DIR, 'system', 'icons', 'edit.png'))
            icon_check = QIcon(os.path.join(ROOT_DIR, 'system', 'icons', 'run.png'))
            icon_upload = QIcon(os.path.join(ROOT_DIR, 'system', 'icons', 'upload.png'))
            icon_preview = QIcon(os.path.join(ROOT_DIR, 'system', 'icons', 'preview.png'))
            icon_release = QIcon(os.path.join(ROOT_DIR, 'system', 'icons', 'release.png'))
            icon_download = QIcon(os.path.join(ROOT_DIR, 'system', 'icons', 'download.png'))
            icon_file = QIcon(os.path.join(ROOT_DIR, 'system', 'icons', 'image.png'))
            icon_content = QIcon(os.path.join(ROOT_DIR, 'system', 'icons', 'content.png'))

            self.ui.pd_edit.clicked.connect(self.handle_pd_edit)
            self.ui.pd_check.clicked.connect(self.handle_pd_check)
            self.ui.pd_upload.clicked.connect(self.handle_pd_upload)
            self.ui.pd_preview.clicked.connect(self.handle_pd_preview)
            self.ui.pd_release.clicked.connect(self.handle_pd_release)
            self.ui.pd_download.clicked.connect(self.handle_pd_download)
            self.ui.file.clicked.connect(self.handle_file)
            self.ui.content.clicked.connect(self.handle_content)

            self.ui.pd_edit.setIcon(icon_edit)
            self.ui.pd_check.setIcon(icon_check)
            self.ui.pd_upload.setIcon(icon_upload)
            self.ui.pd_preview.setIcon(icon_preview)
            self.ui.pd_release.setIcon(icon_release)
            self.ui.pd_download.setIcon(icon_download)
            self.ui.file.setIcon(icon_file)
            self.ui.content.setIcon(icon_content)

        # 啟動計時器：每 1 小時執行一次刷新程序
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_auth_status)
        self.timer.start(3600 * 1000)  # 1 小時 = 3600 秒

    def resizeEvent(self, event):
        super().resizeEvent(event)
        new_size = event.size()
        top = 60
        left = 10
        width = new_size.width() -left -10
        height = new_size.height() -top -30
        self.ui.treeView.setGeometry( left, top, width, height)

    def closeEvent(self, event):
        reply = QMessageBox.question(self, "結束", "您確定要結束退出嗎？",   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()  # 允許關閉
        else:
            event.ignore()  # 阻止關閉

        # 如果有子窗體開啟，一併關閉子窗體
        child_windows = [self.us05, self.us07, self.us09, self.us15, self.us23]
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

        permissions = self.options['permissions'].get(self.email, None) # 抓取權限 可在 temp_options.py 測試
        # print(json.dumps(permissions, indent=4, ensure_ascii=False))

        if permissions:
            dic_p = {}
            for e in permissions:
                pdno = next(iter(e.keys()))
                attt = next(iter(e.values()))
                # print(pdno)
                # print(attt.get('name'))
                # print(attt.get('uid'))
                dic_p[attt.get('name')] = {'action': self.action_test, 'uid': attt.get('uid')}
                self.product_sheet[attt.get('uid')] = attt.get('name') # 產品小抄 {uid: name}

            self.tree_data['產品資料']  = dic_p

            # 標準格式範本
            # self.tree_data['產品資料'] = {
            #     'A': {'action': self.action_test, 'uid': '產品A的uuid'},
            #     'B': {'action': self.action_test, 'uid': '產品B的uuid'},
            # }
        else:
            warning("讀取產品選單失敗", "未設定權限!請洽管理員", detail=f"option中無法讀取到 user: {user} 的權限設定")

    def load_tree_company(self):
        # 讀取公司選單
        print('load product...')
        self.tree_data.pop('公司資料', 0) # clean
        if not self.auth.is_token_valid():
            print('尚未登入無法讀取產品資料')
            return

        garden = self.options['garden'].get(self.email, None) # 抓取權限 可在 temp_options.py 測試
        # print(json.dumps(garden, indent=4, ensure_ascii=False))

        if garden:
            dic_p = {}
            for e in garden:
                company = next(iter(e.keys()))
                attt = next(iter(e.values()))
                # print(company)
                # print(attt.get('name'))
                # print(attt.get('uid'))
                dic_p[attt.get('name')] = {'action': self.action_test, 'uid': attt.get('uid')}
                self.company_sheet[attt.get('uid')] = attt.get('name') # 公司小抄 {uid: name}

            self.tree_data['公司資料']  = dic_p

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

    def show_tree_context_menu(self, position):
        """處理右鍵點擊事件"""
        index = self.ui.treeView.indexAt(position)
        if not index.isValid():
            return

        # 取得父節點名稱來判斷是否為產品
        parent_index = index.parent()
        if parent_index.isValid():
            parent_text = parent_index.data(Qt.DisplayRole)

            # 判斷上階項目是否為 '產品資料'
            if parent_text in ['產品資料', '公司資料']:
                item_text = index.data(Qt.DisplayRole)
                item_uid = index.data(ITEM_UID_ROLE)

                # 建立選單
                menu = QMenu()
                # 只有產品資料才顯示預覽/正式版功能
                if parent_text == '產品資料':
                    action_preview = menu.addAction("開啟產品預覽版網頁")
                    action_official = menu.addAction("開啟產品正式版網頁")
                    menu.addSeparator() # 分隔線
                if parent_text == '公司資料':
                    action_company = menu.addAction("開啟公司網頁")
                    menu.addSeparator() # 分隔線

                action_copy_uid = menu.addAction("複製 UID")
                action_test = menu.addAction("測試")
                action = menu.exec_(self.ui.treeView.viewport().mapToGlobal(position))

                if parent_text == '產品資料':
                    if action == action_preview:
                        self.open_preview_version_by_product(item_text, item_uid)
                    elif action == action_official:
                        self.open_official_version_product(item_text, item_uid)

                if parent_text == '公司資料':
                    if action == action_company:
                        self.open_company(item_text, item_uid)

                if action == action_test:
                    self.test()

                # 處理複製 UID 邏輯
                if action == action_copy_uid:
                    if item_uid:
                        QApplication.clipboard().setText(item_uid)
                        # 在狀態列顯示提示 (選配)
                        self.ui.statusbar.showMessage(f"已複製 UID: {item_uid}", 2000)

    def open_preview_version_by_product(self, name, uid):
        #  開啟產品預覽版
        pdno = self.pa.get_product_by_product_uid(uid).get('pdno')
        vendor_path = self.pa.get_company_by_product_uid(uid).get('vendor_path')
        url = f'{SPECIC_DOMAIN}/en/app/v/{vendor_path}/preview/{pdno}'
        # print('url:', url)
        QDesktopServices.openUrl(QUrl(url))

    def open_official_version_product(self, name, uid):
        # 開啟產品正式版
        pdno = self.pa.get_product_by_product_uid(uid).get('pdno')
        vendor_path = self.pa.get_company_by_product_uid(uid).get('vendor_path')
        url = f'{SPECIC_DOMAIN}/en/app/v/{vendor_path}/p/{pdno}'
        # print('url:', url)
        QDesktopServices.openUrl(QUrl(url))

    def open_company(self, name, uid):
        # 開啟公司網頁
        vendor_path = self.pa.get_company_by_company_uid(uid).get('vendor_path')
        url = f'{SPECIC_DOMAIN}/en/app/v/{vendor_path}'
        # print('url:', url)
        QDesktopServices.openUrl(QUrl(url))

    def refresh_auth_status(self):
        """檢查是否過期，必要時刷新，並更新狀態列"""
        print("🙍 ", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), 'refresh_auth_status...')

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
        # 預設禁用
        self.ui.pd_download.setEnabled(False)
        self.ui.pd_edit.setEnabled(False)
        self.ui.pd_check.setEnabled(False)
        self.ui.pd_upload.setEnabled(False)
        self.ui.pd_preview.setEnabled(False)
        self.ui.pd_release.setEnabled(False)

        if index.isValid():
            parent_index = index.parent()
            if parent_index.isValid() and parent_index != self.model.invisibleRootItem().index(): # 確保有父節點且不是隱藏的根節點
                parent_text = parent_index.data(Qt.DisplayRole)
                if parent_text == '產品資料':
                    self.ui.pd_download.setEnabled(True)
                    self.ui.pd_edit.setEnabled(True)
                    self.ui.pd_check.setEnabled(True)
                    self.ui.pd_upload.setEnabled(True)
                    self.ui.pd_preview.setEnabled(True)
                    self.ui.pd_release.setEnabled(True)
                elif parent_text == '公司資料':
                    self.ui.pd_download.setEnabled(True)
                    self.ui.pd_edit.setEnabled(True)
                    self.ui.pd_check.setEnabled(True)
                    self.ui.pd_upload.setEnabled(True)
                    self.ui.pd_preview.setEnabled(True)

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

    def _get_selected_uid(self):
        # 獲取uid (有可能是 產品資料的uid 或 公司資料的uid)
        index = self.ui.treeView.selectionModel().currentIndex()
        if not index.isValid():
            return None # 1. 無效的選取

        parent_index = index.parent()
        if not parent_index.isValid() or parent_index == self.model.invisibleRootItem().index():
            return None # 2. 不是子節點

        parent_text = parent_index.data(Qt.DisplayRole)
        if parent_text not in ['產品資料', '公司資料']:
            return None # 3. 父節點不是產品資料

        item_uid = index.data(ITEM_UID_ROLE)
        if item_uid is None:
            return None # 4. 選取項是 '產品資料' 父節點本身，或沒有 UID

        return item_uid

    def _get_selected(self):
        # 獲取 產品資料 下的 uid
        index = self.ui.treeView.selectionModel().currentIndex()
        if not index.isValid():
            return None # 1. 無效的選取

        parent_index = index.parent()
        if not parent_index.isValid() or parent_index == self.model.invisibleRootItem().index():
            return None # 2. 不是子節點

        parent_text = parent_index.data(Qt.DisplayRole)
        item_uid = index.data(ITEM_UID_ROLE)
        return {
            'parent_text': parent_text,
            'uid': item_uid
        }

    def handle_file(self):
        auth_data = self.auth.load_local_data()
        jwt = auth_data.get("jwt")
        if not jwt:
            QMessageBox.warning(self, '尚未登入', '請先登入')
            return

        self.us15 = MainWindow_us15() # 檔案
        self.us15.show()

    def handle_content(self):
        auth_data = self.auth.load_local_data()
        jwt = auth_data.get("jwt")
        if not jwt:
            QMessageBox.warning(self, '尚未登入', '請先登入')
            return
        os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu --disable-software-rasterizer"
        os.environ["QT_QUICK_BACKEND"] = "software"
        self.us23 = MainWindow_us23() # 文章
        self.us23.show()

    def handle_pd_download(self):
        # 下載
        reply = QMessageBox.question(self, "下載",
            "您確定要從雲端下載資料嗎？，這動作將會覆蓋本地資料\n\n若您不確定，建議您先選擇否，手動備份後再行下載。\n",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            sel = self._get_selected()
            if sel['parent_text'] == '產品資料':
                result = self.ps.pull_data_original(sel['uid']) # 下載
                if not result['is_error']:
                    QMessageBox.information(self, "下載成功", result['message'])
            elif sel['parent_text'] == '公司資料':
                result = self.comp.pull_data_original(sel['uid']) # 下載
                if not result['is_error']:
                    QMessageBox.information(self, "下載成功", result['message'])

    def handle_pd_edit(self):
        # 編輯 以編輯器開啟
        sel = self._get_selected()
        result = self.ps.edit(sel['uid']) # 以編輯器開啟
        if result['is_error']:
            QMessageBox.warning(self, "錯誤", result['message'])

    def handle_pd_check(self):
        # print('handle_pd_check')
        self.ui.pd_check.setEnabled(False) # 目前無效，因為主線程gui凍結
        # time.sleep(3)
        sel = self._get_selected()
        if sel['parent_text'] == '產品資料':
            pc = ProductCheck(sel['uid'])
            result = pc.get_detaile() # 檢查
            if result['is_verify'] is True:
                QMessageBox.information(self, "檢查", f'{self.product_sheet[sel['uid']]}\n\n恭喜你，沒有發現錯誤。\n')
            else:
                QMessageBox.warning(self, "檢查", result['message'])

        elif sel['parent_text'] == '公司資料':
            cc = CompanyCheck(sel['uid'])
            result = cc.get_detaile() # 檢查
            if result['is_verify'] is True:
                QMessageBox.information(self, "檢查", f'{self.company_sheet[sel['uid']]}\n\n恭喜你，沒有發現錯誤。\n')
            else:
                QMessageBox.warning(self, "檢查", result['message'])

        self.ui.pd_check.setEnabled(True)

    def handle_pd_upload(self):
        # 上傳前 先檢查
        sel = self._get_selected()
        if sel['parent_text'] == '產品資料':
            product_uid = sel['uid']
            pdno = self.pa.get_product_by_product_uid(product_uid).get('pdno')
            # print('pdno:', pdno)

            reply = QMessageBox.question(self, "上傳", f"{self.product_sheet[sel['uid']]}\n\n您確定要從本地上傳資料嗎？，這動作將會覆蓋雲端資料\n", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                result = self.ps.upload(sel['uid']) # 執行上傳程序  會先檢查 驗證失敗將停止
                if result['is_verify'] is True:
                    if result['result'] is None:
                        # 未設定 Policies
                        QMessageBox.warning(self, "上傳", f"{self.product_sheet[sel['uid']]}\n\n上傳失敗!\n\n未設定 Policies!")
                    else:

                        self.ps.purge_cloudflare_cache_datajson_preview(pdno) # 清除 cloudflare 代理快取 預覽版
                        QMessageBox.information(self, "上傳", f'{self.product_sheet[sel['uid']]}\n\n上傳成功。\n')
                else:
                    QMessageBox.warning(self, "上傳", f"{self.product_sheet[sel['uid']]}\n\n驗證失敗!")

        elif sel['parent_text'] == '公司資料':
            company_uid = sel['uid']
            cono = self.pa.get_company_by_company_uid(company_uid).get('cono')
            # print('cono:', cono)

            reply = QMessageBox.question(self, "上傳", f"{self.company_sheet[sel['uid']]}\n\n您確定要從本地上傳資料嗎？，這動作將會覆蓋雲端資料\n", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                result = self.comp.upload(sel['uid']) # 執行上傳程序  會先檢查 驗證失敗將停止
                if result['is_verify'] is True:
                    if result['result'] is None:
                        # 未設定 Policies
                        QMessageBox.warning(self, "上傳", f"{self.company_sheet[sel['uid']]}\n\n上傳失敗!\n\n未設定 Policies!")
                    else:
                        self.comp.purge_cloudflare_cache_datajson_company(cono) # 清除 cloudflare 代理快取
                        self._need_snapshots(entry_type='vendor') # 標記需要更新快照
                        QMessageBox.information(self, "上傳", f'{self.company_sheet[sel['uid']]}\n\n上傳成功。\n')
                else:
                    QMessageBox.warning(self, "上傳", f"{self.company_sheet[sel['uid']]}\n\n驗證失敗!")

    def handle_pd_preview(self):
        # print('handle_pd_preview')
        sel = self._get_selected()
        if sel['parent_text'] == '產品資料':
            self.us07 = MainWindow_us07('product', sel['uid']) # 檢視
            self.us07.show()

        elif sel['parent_text'] == '公司資料':
            self.us07 = MainWindow_us07('company', sel['uid']) # 檢視
            self.us07.show()

    def handle_pd_release(self):
        # print('handle_pd_release')
        sel = self._get_selected()
        if sel['parent_text'] == '產品資料':
            product_uid = sel['uid']
            pdno = self.pa.get_product_by_product_uid(product_uid).get('pdno')
            # print('pdno:', pdno)
            if product_uid:
                reply = QMessageBox.question(self, "發布", f"{self.product_sheet[product_uid]}\n\n您確定要發布為正式版嗎？\n", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.Yes:
                    result = self.pr.release(product_uid)
                    self._need_snapshots(entry_type='product') # 標記需要更新快照

                    if result['is_error']:
                        QMessageBox.warning(self, "發布", result['message'])
                    else:
                        self.pr.purge_cloudflare_cache_datajson_product(pdno) # 清除 cloudflare 代理快取 正式版
                        QMessageBox.information(self, "發布", result['message'])

    def _need_snapshots(self, entry_type): # 標記需要更新快照
        # entry_type: 'product', 'article', 'vendor'
        print('_need_snapshots entry_type:', entry_type)
        if entry_type not in ['product', 'article', 'vendor']:
            raise KeyError("entry_type error!")

        for lang in ['en', 'zh-TW']:
            path = ''
            if entry_type == 'product':
                product_uid = self._get_selected_uid()
                pdno = self.pa.get_product_by_product_uid(product_uid).get('pdno')
                if not pdno:
                    raise KeyError('lost pdno!')
                    return
                vendor_path = self.pa.get_company_by_product_uid(product_uid).get('vendor_path')
                if not vendor_path:
                    raise KeyError('lost vendor_path!')
                path = f'/{lang}/app/v/{vendor_path}/p/{pdno}'

            elif entry_type == 'vendor':
                company_uid = self._get_selected_uid()
                vendor_path = self.pa.get_company_by_company_uid(company_uid).get('vendor_path')
                if not vendor_path:
                    raise KeyError('lost vendor_path!')
                path = f'/{lang}/app/v/{vendor_path}'

            target_path = self.sn._format_path(path)
            full_url = f'{SPECIC_DOMAIN}{target_path}'
            # print('target_path:', target_path)
            # print('full_url:', full_url)
            # print('self.sn.upsert_path:', target_path, full_url)
            self.sn.upsert_path(target_path, full_url) # 標記後端 需要更新快照
            print('成功標記後端 需要更新快照:', target_path)

    def test(self):
        print('test')

    def _get_uid_users(self, uid):
        result = []
        permissions = self.options.get('permissions', {})
        for email, items in permissions.items():
            for item in items:
                # item 是 {'ys_v_dev': {...}} 的格式，因此需要取出 value
                for data in item.values():
                    if data.get('uid') == uid:
                        result.append(email)
                        break  # 已找到該 email 的匹配 uid，就不用再找此 email 下其他項目
        return result

    def action_test(self, item_text, item_uid):
        name = item_text
        uid = item_uid
        users = self._get_uid_users(item_uid)
        # print(f"點擊的項目文字是: {name}")
        # print(f"該產品的 UID 是: {uid}")
        # print(f"具有編輯權限者是: {', '.join(users)}")
        QMessageBox.information(self, "information", f'{name}\n{uid}\n編輯權限: {', '.join(users)}')

def main():
    # startup() # 正常啟動
    app = QApplication(sys.argv)
    argv1 = sys.argv[1] if len(sys.argv) > 1 else "no argv" # 預留參數接口
    # print('argv1:', argv1)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()