# us15.py
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

    sys.path.append(os.path.join(ROOT_DIR, 'gui', 'us15'))
    from form_us15 import Ui_MainWindow

class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow();
        self.ui.setupUi(self) # 載入ui
        self.setWindowTitle('檔案檢視')
        self.resize(958, 680)  # 設定視窗大小
        self.sb = StorageBuckets() # 檔案儲存

        self.init_table_config() # 設定 TableWidget 的外觀與標題
        # self.ui.scrollArea

        self.init_query_params()

        # button
        self.ui.query.clicked.connect(self.handle_query)

    def init_table_config(self):
        """初始化表格欄位與樣式"""
        table = self.ui.treeView # 根據你的註解，此處為 QTableWidget
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(['縮圖', '標題', '類型', '上傳時間'])

        # 設定欄位伸縮：標題欄自動填滿
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed) # 縮圖固定寬度
        table.setColumnWidth(0, 80)
        header.setSectionResizeMode(1, QHeaderView.Stretch) # 標題自動拉長
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)

        # 設定選取行為
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers) # 不可直接修改

    def init_query_params(self):
        self.ui.w_title.setText('')
        self.ui.w_summary.setText('')
        self.ui.w_content_type.clear()
        self.ui.w_content_type.addItems(['全部', 'application/pdf', 'image/jpeg']) # QComboBox
        self.ui.w_counts.setText('250')

    def handle_query(self):
        """處理查詢按鈕點擊事件"""
        # 1. 獲取介面上的參數
        title_kw = self.ui.w_title.text().strip()
        summary_kw = self.ui.w_summary.text().strip()
        content_type = self.ui.w_content_type.currentText()

        try:
            limit = int(self.ui.w_counts.text())
        except:
            limit = 200

        # 針對 '全部' 進行處理
        if content_type == '全部':
            content_type = None

        print(f"🔍 執行查詢: Title={title_kw}, Summary={summary_kw}, Limit={limit}")

        # 2. 呼叫後端查詢 (注意：你的 query_storage 暫時沒支援 content_type 參數，我們等一下微調它)
        # 如果 query_storage 尚未加入 content_type，我們可以先在前端過濾或後續擴充
        results = self.sb.query_storage(
            search_title=title_kw if title_kw else None,
            search_summary=summary_kw if summary_kw else None,
            limit=limit
        )

        # 3. 將資料填入表格
        self.render_table(results)

    def render_table(self, data_list):
        """將 JSON 資料清單渲染到 QTableWidget"""
        table = self.ui.treeView
        table.setRowCount(0) # 清空現有內容

        if not data_list:
            print("⚠️ 查詢結果為空")
            return

        table.setRowCount(len(data_list))

        for row, item in enumerate(data_list):
            # A. 縮圖欄 (暫時放文字，下一階段換成圖片)
            table.setItem(row, 0, QTableWidgetItem("載入中..."))

            # B. 標題
            title_item = QTableWidgetItem(item.get('title', '無標題'))
            # 將完整的資料 dict 存入該 Item 的 UserRole 中，方便點擊時取用
            title_item.setData(Qt.UserRole, item)
            table.setItem(row, 1, title_item)

            # C. 類型
            table.setItem(row, 2, QTableWidgetItem(item.get('content_type', '-')))

            # D. 時間 (格式化：2024-01-01T12:00:00 -> 2024-01-01)
            raw_date = item.get('created_at', '')
            formatted_date = raw_date[:10] if len(raw_date) >= 10 else raw_date
            table.setItem(row, 3, QTableWidgetItem(formatted_date))

        # 設定行高以預留縮圖空間
        for i in range(len(data_list)):
            table.setRowHeight(i, 60)

        print(f"✅ 成功渲染 {len(data_list)} 筆資料")

def main():
    app = QApplication(sys.argv)
    # argv1 = sys.argv[1] if len(sys.argv) > 1 else "no argv" # 預留參數接口
    # print('argv1:', argv1)

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()