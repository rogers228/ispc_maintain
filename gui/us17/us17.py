# us17.py
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
    from tool_storage import StorageBuckets
    from tool_msgbox import error, info

    sys.path.append(os.path.join(ROOT_DIR, 'gui', 'us17'))
    from form_us17 import Ui_MainWindow

class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow();
        self.ui.setupUi(self) # 載入ui
        self.setWindowTitle('上傳檔案')
        self.resize(1228, 500)  # 設定視窗大小
        self.sb = StorageBuckets() # 檔案儲存

        # 1. 初始化 TableWidget 欄位
        self.ui.treeView.setColumnCount(3)
        self.ui.treeView.setHorizontalHeaderLabels(['檔案路徑', '顯示標題', '摘要'])

        # 設定欄位寬度調整模式：第一欄自動伸展，或指定寬度
        self.ui.treeView.setColumnWidth(0, 200) # source
        self.ui.treeView.setColumnWidth(1, 400) # title
        self.ui.treeView.setColumnWidth(2, 460) # summary
        self.ui.treeView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.treeView.customContextMenuRequested.connect(self.show_context_menu)

        # 2. 開啟拖放功能 (TableWidget 本身也需要設定)
        self.setAcceptDrops(True)
        self.ui.treeView.setAcceptDrops(True)

        # button
        self.ui.upload.clicked.connect(self.handle_upload)
        self.ui.cancel.clicked.connect(self.handle_cancel)
        self.ui.clean.clicked.connect(self.handle_clean)

        # 定義合法的附檔名 (全部小寫方便後續比對)
        self.LEGAL_EXTENSIONS = {
            '.jpg', '.jpeg', '.png', '.webp', # 圖片
            '.pdf',                          # 文件
            '.zip', '.rar',                  # 壓縮檔
            '.svg'                           # 向量圖
        }

    def resizeEvent(self, event):
        super().resizeEvent(event)
        new_size = event.size()
        width = new_size.width()
        height = new_size.height()

        tb = self.ui.treeView
        tb_t, tb_l = 10, 10
        tb_w = width -10 -10
        tb_h = height - 10 - 60
        tb.setGeometry(tb_l, tb_t, tb_w, tb_h)

        button_t = tb_t + tb_h + 5
        cancel_left = int(width/2 - self.ui.cancel.width()) -10
        upload_left = cancel_left +self.ui.cancel.width() +10
        self.ui.clean.move(10, button_t)
        self.ui.cancel.move(cancel_left, button_t)
        self.ui.upload.move(upload_left, button_t)

    # --- 拖放邏輯實作 ---
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        files = [u.toLocalFile() for u in urls]

        skipped_files = []  # 用來記錄被略過的檔案名稱
        valid_count = 0     # 成功新增的數量

        for file_path in files:
            ext = os.path.splitext(file_path)[1].lower()

            # 檢查：是否為檔案 且 附檔名合法
            if os.path.isfile(file_path) and ext in self.LEGAL_EXTENSIONS:
                # 檢查重複
                if not self.is_file_exists_in_table(file_path):
                    self.add_file_to_table(file_path)
                    valid_count += 1
            else:
                # 記錄非法的檔案名稱（僅存檔名，避免路徑太長）
                skipped_files.append(os.path.basename(file_path))

        # 批次顯示警告訊息
        if skipped_files:
            msg = "部分檔案因格式不符或為資料夾已被略過"
            detail = "\n".join(skipped_files[:10])  # 最多顯示前 10 個，避免視窗過長
            if len(skipped_files) > 10:
                detail += f"\n... 以及其他 {len(skipped_files) - 10} 個檔案"

            # 使用您的 tool_msgbox 顯示
            error('錯誤', msg, detail)

        # 可選：在控制台列印簡單結果
        print(f"拖曳處理完成：新增 {valid_count} 筆，略過 {len(skipped_files)} 筆。")

    def add_file_to_table(self, file_path):
        # 檢查是否已存在 (避免重複)
        if self.is_file_exists_in_table(file_path):
            return

        row_count = self.ui.treeView.rowCount()
        self.ui.treeView.insertRow(row_count)

        # 檔名處理 (無附檔名)
        file_name = os.path.splitext(os.path.basename(file_path))[0]

        # 建立 Item 並填入表格
        item_source = QTableWidgetItem(file_path)
        item_title = QTableWidgetItem(file_name)
        item_summary = QTableWidgetItem("")

        # 設定唯讀屬性 (Source 唯讀)
        item_source.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)

        self.ui.treeView.setItem(row_count, 0, item_source)
        self.ui.treeView.setItem(row_count, 1, item_title)
        self.ui.treeView.setItem(row_count, 2, item_summary)

    def is_file_exists_in_table(self, file_path):
        """檢查路徑是否已存在於第一欄 (Source)"""
        for row in range(self.ui.treeView.rowCount()):
            existing_item = self.ui.treeView.item(row, 0)
            if existing_item and existing_item.text() == file_path:
                return True
        return False

    def is_records_error(self, data_list):
        """檢查所有欄位，若有錯誤回傳錯誤訊息，否則回傳 None"""
        if not data_list:
            return "清單中沒有檔案，請先拖曳檔案進來。"

        for i, row in enumerate(data_list):
            # 檢查檔案路徑是否依然有效
            if not os.path.exists(row['source']):
                self.ui.treeView.setCurrentCell(i, 0)
                return f"第 {i + 1} 列的檔案路徑已失效或檔案被移除。"

            # 檢查 Title
            if not row['title'].strip():
                self.ui.treeView.setCurrentCell(i, 1)
                return f"第 {i + 1} 列輸入顯示標題。"

            # 檢查 Summary
            if not row['summary'].strip():
                self.ui.treeView.setCurrentCell(i, 2)
                return f"第 {i + 1} 列請輸入摘要。"

        return None # 代表檢查通過

    def handle_upload(self):
        self.ui.treeView.clearFocus() # 讓 treeView 失去焦點 迫使輸入完成
        self.ui.treeView.setCurrentCell(-1, -1) # 更保險地強制關閉編輯器
        # 1. 蒐集目前表格中的資料
        data_list = []
        for row in range(self.ui.treeView.rowCount()):
            data_list.append({
                "source": self.ui.treeView.item(row, 0).text(),
                "title": self.ui.treeView.item(row, 1).text(),
                "summary": self.ui.treeView.item(row, 2).text(),
            })

        # 2. 驗證資料
        records_error = self.is_records_error(data_list)
        if records_error:
            error(title='錯誤',message=records_error)
            return

        # 3. 初始化進度條對話框
        total_files = len(data_list)
        progress = QProgressDialog("正在準備上傳...", "取消上傳", 0, total_files, self)
        progress.setWindowTitle("上傳進度")
        progress.setFixedSize(600, 150) # 寬 600, 高 150
        progress.setWindowModality(Qt.WindowModal) # 鎖定視窗，避免重複點擊
        progress.setMinimumDuration(0)             # 立即顯示
        progress.show()

        # 4. 執行上傳
        # print(f"✅ 檢查通過，準備上傳 {len(data_list)} 筆資料")
        success_count = 0
        for i, task in enumerate(data_list):
            # 更新進度條文字與數值
            progress.setLabelText(f"正在上傳 ({i+1}/{total_files}):\n{task['title']}")
            progress.setValue(i)

            # 檢查使用者是否點擊了「取消」
            if progress.wasCanceled():
                error("上傳已中斷。")
                break

            # 執行實際的上傳動作
            try:
                # 呼叫 tool_storage
                self.sb.upload_file(
                    local_file_path=task['source'],
                    title=task['title'],
                    summary=task['summary']
                )
                success_count += 1
            except Exception as e:
                print(f"檔案 {task['title']} 上傳異常: {e}")

            # 讓介面有機會更新（避免視窗凍結）
            QApplication.processEvents()

        # 5. 完成後的處理
        progress.setValue(total_files) # 確保進度條跑滿

        if success_count > 0:
            info("上傳", f"成功處理 {success_count} 筆檔案！")
            self.handle_clean()
            # 如果想上傳完自動關閉視窗，可加上：
            # self.close()

    def handle_cancel(self):
        # print('handle_cancel')
        self.close()

    def handle_clean(self):
        # print('handle_clean')
        # 移除所有資料列
        self.ui.treeView.setRowCount(0)

    def show_context_menu(self, pos):
        """處理右鍵選單彈出"""
        index = self.ui.treeView.indexAt(pos)
        if not index.isValid():
            return

        # 取得被點擊的行號
        row = index.row()

        # 建立選單
        menu = QMenu()
        delete_action = menu.addAction("刪除")

        # 顯示選單並取得使用者點擊的動作
        action = menu.exec_(self.ui.treeView.viewport().mapToGlobal(pos))

        if action == delete_action:
            self.handle_delete_table_row(row)

    def handle_delete_table_row(self, row):
        """執行刪除表格中的某一列"""
        # 取得該列的標題，用於提示使用者
        title_item = self.ui.treeView.item(row, 1)
        title = title_item.text() if title_item else "未知檔案"
        self.ui.treeView.removeRow(row)
        print(f"已從清單移除: {title}")

def main():
    app = QApplication(sys.argv)
    # argv1 = sys.argv[1] if len(sys.argv) > 1 else "no argv" # 預留參數接口
    # print('argv1:', argv1)

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()