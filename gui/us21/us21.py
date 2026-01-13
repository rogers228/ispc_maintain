# us21.py
# rec_article 的列表查詢視窗

if True:
    import sys
    import os
    import hashlib
    import requests
    import json

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
    from config import ISPC_MAINTAIN_CACHE_DIR
    from config_web import WEB_SPECIC_ASSETS_URL
    from share_qt5 import *
    from tool_pd_article import ProductArticle
    from tool_msgbox import error, info

    sys.path.append(os.path.join(ROOT_DIR, 'gui', 'us21'))
    from form_us21 import Ui_MainWindow
    sys.path.append(os.path.join(ROOT_DIR, 'gui', 'us23'))
    from us23 import MainWindow as MainWindow_us23 # Markdown Editer

class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow();
        self.ui.setupUi(self) # 載入ui
        self.setWindowTitle('文章內容')
        self.resize(1240, 798)  # 設定視窗大小
        self.pa = ProductArticle() # 文章儲存

        self.us23 = None # 子表單
        self.cache_dir = ISPC_MAINTAIN_CACHE_DIR
        self.query_max = 100 # 查詢上限筆數
        self.ui.w_counts.setText(str(self.query_max))

        # 呈現表格
        # self.ui.treeView (QTableWidget)

        # 查詢雲端的參數
        # self.ui.w_custom_index (QLineEdit)
        # self.ui.w_title (QLineEdit)
        # self.ui.w_content (QLineEdit)
        # self.ui.w_counts (QLineEdit)

        # 篩選用本快取
        # self.ui.f_custom_index (QLineEdit)
        # self.ui.f_title (QLineEdit)
        # self.ui.f_content (QLineEdit)



        self.init_table_config() # 設定 TableWidget 的外觀與標題
        self.init_filter_config()
        self.init_status_bar()

    def init_table_config(self):
        """初始化表格欄位與樣式"""
        table = self.ui.treeView # 根據你的註解，此處為 QTableWidget
        table.selectionModel().selectionChanged.connect(self.on_selection_changed)

        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(['自訂ID', '標題', '內容'])

        header = table.horizontalHeader()
         # 2. 設定欄位比例
        header.setSectionResizeMode(0, QHeaderView.Fixed)           # 縮圖：固定
        table.setColumnWidth(0, 80)
        header.setSectionResizeMode(1, QHeaderView.Interactive)     # 標題：可調整
        table.setColumnWidth(1, 200)
        header.setSectionResizeMode(2, QHeaderView.Stretch)         # 摘要：自動填滿剩餘空間


        # 設定選取行為
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers) # 不可直接修改

        # 允許右鍵選單
        # table.setContextMenuPolicy(Qt.CustomContextMenu)
        # table.customContextMenuRequested.connect(self.show_context_menu)

    def init_status_bar(self):
        self.count_label = QLabel("篩選 0 筆 / 查詢 0 筆")
        self.count_label.setContentsMargins(0, 0, 10, 0)# 設定一點邊距讓它好看些
        self.statusBar().addPermanentWidget(self.count_label)# 加入到狀態列右側 (PermanentWidget)

    def init_filter_config(self):
        # 設定篩選下拉選單的值
        pass

        # 連結篩選事件：當文字改變或選單切換時即時篩選
        # self.ui.f_title.textChanged.connect(self.apply_local_filter)
        # self.ui.f_title.textChanged.connect(self.save_current_state_to_cache)
        # self.ui.f_summary.textChanged.connect(self.apply_local_filter)
        # self.ui.f_summary.textChanged.connect(self.save_current_state_to_cache)
        # self.ui.f_content_type.currentTextChanged.connect(self.apply_local_filter)
        # self.ui.f_content_type.currentTextChanged.connect(self.save_current_state_to_cache)

    def closeEvent(self, event):
        if self.us23: # 子表單一併關閉
            self.us23.close()