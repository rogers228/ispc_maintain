# us15.py

# win + r
# %LOCALAPPDATA%\ISPC_Maintain\cache
# 開啟快取資料夾

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
    from tool_storage import StorageBuckets
    from tool_msgbox import error, info

    sys.path.append(os.path.join(ROOT_DIR, 'gui', 'us15'))
    from form_us15 import Ui_MainWindow
    sys.path.append(os.path.join(ROOT_DIR, 'gui', 'us17'))
    from us17 import MainWindow as MainWindow_us17

class ThumbWorker(QRunnable):
    """
    QRunnable 不支援訊號，所以我們需要一個小類別來轉發訊號
    """
    class Signals(QObject):
        finished_one = pyqtSignal(int, QIcon)

    def __init__(self, row_index, file_path):
        super().__init__()
        self.row_index = row_index
        self.file_path = file_path
        self.signals = self.Signals()
        self.cache_dir = ISPC_MAINTAIN_CACHE_DIR

    @pyqtSlot()
    def run(self):
        try:
            ext = os.path.splitext(self.file_path)[1]
            name_hash = hashlib.md5(self.file_path.encode()).hexdigest()
            local_path = os.path.join(self.cache_dir, f"thumb_{name_hash}{ext}")

            # 如果本地沒這張縮圖，才下載
            if not os.path.exists(local_path):
                url = f"{WEB_SPECIC_ASSETS_URL}/{self.file_path}"

                res = requests.get(url, timeout=5)
                if res.status_code == 200:
                    pix = QPixmap()
                    pix.loadFromData(res.content)
                    # 縮小圖片為 80px (保持比例)
                    thumb = pix.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    thumb.save(local_path) # <--- 這裡存入本地硬碟

            # 從本地讀取並發送給 GUI
            icon_pix = QPixmap(local_path)
            self.signals.finished_one.emit(self.row_index, QIcon(icon_pix))
        except Exception as e:
            print(f"Error: {e}")

class FullImageDownloader(QRunnable):
    class Signals(QObject):
        # 傳遞：(目前索引, 總數, 檔案名稱)
        progress = pyqtSignal(int, int, str)
        finished_all = pyqtSignal()

    def __init__(self, file_path, current_idx, total_count):
        super().__init__()
        self.file_path = file_path
        self.current_idx = current_idx
        self.total_count = total_count
        self.signals = self.Signals()
        self.cache_dir = ISPC_MAINTAIN_CACHE_DIR

    @pyqtSlot()
    def run(self):
        try:
            clean_path = self.file_path.lstrip('/')# 確保 file_path 是乾淨的相對路徑 (例如: "images/abc.jpg")
            ext = os.path.splitext(self.file_path)[1]
            # 使用乾淨的相對路徑做雜湊，保證主畫面跟預覽畫面的 Key 一致
            name_hash = hashlib.md5(clean_path.encode()).hexdigest()
            local_full_path = os.path.join(self.cache_dir, f"full_{name_hash}{ext}")

            # 發送進度：開始下載
            self.signals.progress.emit(self.current_idx, self.total_count, self.file_path)

            # 🚀 關鍵修正：下載前再次檢查，避免 ThreadPool 裡排隊的任務重複下載
            if not os.path.exists(local_full_path):
                base = WEB_SPECIC_ASSETS_URL.rstrip('/')
                url = f"{base}/{clean_path}"

                res = requests.get(url, timeout=20)
                if res.status_code == 200:
                    # 使用暫存檔寫入再更名，確保檔案寫入完整
                    temp_path = local_full_path + ".tmp"
                    with open(temp_path, 'wb') as f:
                        f.write(res.content)
                    os.replace(temp_path, local_full_path)
                print(f"✅ 背景預下載完成: {local_full_path}")

            # 如果是最後一個任務，發送完成訊號
            if self.current_idx == self.total_count:
                self.signals.finished_all.emit()

        except requests.exceptions.ConnectionError:
            # 網路斷開時，我們不 print 噴紅字，只在背景安靜結束
            pass

        except Exception as e:
            print(f"❌ 背景預下載失敗: {e}")

class EditFileInfoDialog(QDialog):
    def __init__(self, title, summary, parent=None):
        super().__init__(parent)
        self.setWindowTitle("編輯")
        self.setFixedWidth(400)
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.title_input = QLineEdit(title)
        self.summary_input = QTextEdit(summary)
        self.summary_input.setFixedHeight(100)

        form.addRow("標題:", self.title_input)
        form.addRow("摘要:", self.summary_input)
        layout.addLayout(form)

        # 加入 確定/取消 按鈕
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

    def get_values(self):
        return self.title_input.text().strip(), self.summary_input.toPlainText().strip()
# us15.py
class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow();
        self.ui.setupUi(self) # 載入ui
        self.setWindowTitle('檔案檢視')
        self.resize(1240, 798)  # 設定視窗大小
        self.sb = StorageBuckets() # 檔案儲存
        # self.zoom_mode = "auto"
        self.ui.scrollArea.setAlignment(Qt.AlignCenter) # 圖片居中
        self.ui.scrollArea.setWidgetResizable(True) # 讓內部 widget 自動伸展

        self.query_max = 100 # 查詢上限筆數


        self.us17 = None # 新增檔案子表單
        self.cache_dir = ISPC_MAINTAIN_CACHE_DIR
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

        self.content_groups = {
            "Images": ["image/jpeg", "image/png", "image/webp", "image/x-icon", "image/svg+xml"],
            "Documents": ["application/pdf"],
            "Assets": ["application/xml", "application/json", "text/markdown", "text/plain", "text/javascript", "text/css"],
            "Fonts": ["font/woff2"]
        }

        # 自動生成下拉選單要顯示的清單：全部 + 群組名 + 原始單一類型
        # 這裡用一個 flat list 方便後續調用
        self.all_mimetypes = list(set(mime for mimes in self.content_groups.values() for mime in mimes))
        self.ui_categories = ["全部"] + list(self.content_groups.keys()) + self.all_mimetypes

        self.init_table_config() # 設定 TableWidget 的外觀與標題
        self.init_query_params()
        self.init_filter_config()
        self.init_status_bar()

        icon_upload = QIcon(os.path.join(ROOT_DIR, 'system', 'icons', 'upload.png'))
        self.ui.query.clicked.connect(self.handle_query)
        self.ui.addnew.clicked.connect(self.handle_addnew)
        self.ui.addnew.setIcon(icon_upload)
        self.workers = [] # 用來存放
        self.threadpool = QThreadPool()
        # 限制同時下載數量，建議 3~5，這會讓 UI 非常流暢
        self.threadpool.setMaxThreadCount(5)

        self.load_query_cache() # 讀取上次的紀錄

    def init_status_bar(self):
        self.count_label = QLabel("篩選 0 筆 / 查詢 0 筆")
        self.count_label.setContentsMargins(0, 0, 10, 0)# 設定一點邊距讓它好看些
        self.statusBar().addPermanentWidget(self.count_label)# 加入到狀態列右側 (PermanentWidget)

    def init_table_config(self):
        """初始化表格欄位與樣式"""
        table = self.ui.treeView # 根據你的註解，此處為 QTableWidget
        table.selectionModel().selectionChanged.connect(self.on_selection_changed)

        # 開啟自動排序功能
        table.setSortingEnabled(True)
        # 確保標題列是可以點擊觸發行為的
        table.horizontalHeader().setSectionsClickable(True)

        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(['縮圖', '標題', '摘要', '類型', '上傳時間'])


        header = table.horizontalHeader()

         # 2. 設定欄位比例
        header.setSectionResizeMode(0, QHeaderView.Fixed)           # 縮圖：固定
        table.setColumnWidth(0, 80)
        header.setSectionResizeMode(1, QHeaderView.Interactive)     # 標題：可調整
        table.setColumnWidth(1, 200)
        header.setSectionResizeMode(2, QHeaderView.Stretch)         # 摘要：自動填滿剩餘空間
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents) # 類型：自動寬度
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents) # 時間：自動寬度

        # 設定選取行為
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers) # 不可直接修改

        # 允許右鍵選單
        table.setContextMenuPolicy(Qt.CustomContextMenu)
        table.customContextMenuRequested.connect(self.show_context_menu)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        new_size = event.size()
        width = new_size.width()
        height = new_size.height()


        tb = self.ui.treeView
        tb_t, tb_l = 85, 10

        tb_w_min = 800
        tb_w = max(tb_w_min, int(width*0.66))
        tb_h = height - 10 - 105
        tb.setGeometry(tb_l, tb_t, tb_w, tb_h)

        view = self.ui.scrollArea
        v_l = tb_l + tb_w + 10
        v_w = width - tb_l - tb_w - 20
        view.setGeometry(v_l, tb_t, v_w, tb_h)

        # 同步更新遮罩大小
        if hasattr(self, 'overlay') and self.overlay.isVisible():
            self.overlay.resize(self.ui.treeView.size())

        label = self.ui.label_preview
        original = label.property("original_pixmap")
        if original:
            self.set_pixmap_to_label(original) # 視窗變動時，重新計算縮放與座標

    def closeEvent(self, event):
        if self.us17: # 若新增檔案視窗也 則一併關閉
            self.us17.close()

        """當視窗關閉時，確保所有背景任務停止"""
        self.threadpool.clear() # 清空排隊中的任務
        # print("清理背景任務並關閉程式...")
        event.accept()

    def init_query_params(self):
        self.ui.w_title.setText('')
        self.ui.w_summary.setText('')
        self.ui.w_content_type.clear()
        self.ui.w_content_type.addItems(self.ui_categories)
        self.ui.w_counts.setText(str(self.query_max))

    def init_filter_config(self):
        # 設定篩選下拉選單的值
        self.ui.f_content_type.clear()
        self.ui.f_content_type.addItems(self.ui_categories)

        # 連結篩選事件：當文字改變或選單切換時即時篩選
        self.ui.f_title.textChanged.connect(self.apply_local_filter)
        self.ui.f_title.textChanged.connect(self.save_current_state_to_cache)
        self.ui.f_summary.textChanged.connect(self.apply_local_filter)
        self.ui.f_summary.textChanged.connect(self.save_current_state_to_cache)
        self.ui.f_content_type.currentTextChanged.connect(self.apply_local_filter)
        self.ui.f_content_type.currentTextChanged.connect(self.save_current_state_to_cache)

    def get_target_mimetypes(self, selected_text):
        """根據選中的文字回傳對應的 MIME 類型清單"""
        if selected_text == "全部":
            return None # 或是回傳 self.all_mimetypes

        # 如果選中的是群組名稱 (例如 "Images")
        if selected_text in self.content_groups:
            return self.content_groups[selected_text]

        # 如果選中的是單一類型 (例如 "image/jpeg")
        return [selected_text]

    def handle_query(self):
        """處理查詢按鈕點擊事件"""

        self.toggle_loading_overlay(True)
        self.ui.query.setEnabled(False)
        self.statusBar().showMessage("正在要求雲端資料...")
        QApplication.processEvents() # 確保遮罩立即出現


        # 1. 獲取介面上的參數
        title_kw = self.ui.w_title.text().strip()
        summary_kw = self.ui.w_summary.text().strip()
        # content_type = self.ui.w_content_type.currentText()
        content_type_selection = self.ui.w_content_type.currentText()
        target_mimes = self.get_target_mimetypes(content_type_selection)

        try:
            limit = min(int(self.ui.w_counts.text()), self.query_max)
            print('limit:', limit)
        except:
            limit = self.query_max

        query_params = {
            "title": title_kw,
            "summary": summary_kw,
            "content_type": content_type,
            "limit": str(limit)
        }

        # 針對 '全部' 進行處理
        if content_type == '全部':
            content_type = None

        try:
            results = self.sb.query_storage(
                search_title=title_kw if title_kw else None,
                search_summary=summary_kw if summary_kw else None,
                content_type=target_mimes, # 傳入 list 或是 None,
                limit=limit
            )

            if results is not None:
                self.render_table(results) # 渲染表格
                self.save_query_cache(query_params, results) # 儲存到快取
                self.statusBar().showMessage(f"查詢完成，共 {len(results)} 筆資料", 3000)
            else:
                self.statusBar().showMessage("查詢失敗，請檢查網路", 5000)
        finally:
            # 4. 無論成功或失敗，最後一定要關閉遮罩並還原按鈕
            self.toggle_loading_overlay(False)
            self.ui.query.setEnabled(True)
            self.update_status_info()

    def apply_local_filter(self):
        # 本地篩選
        f_title = self.ui.f_title.text().lower()
        f_summary = self.ui.f_summary.text().lower()
        f_type_selection = self.ui.f_content_type.currentText()

        # 預先取得目標類型清單，避免在迴圈內反覆運算
        target_mimes = self.get_target_mimetypes(f_type_selection)
        visible_count = 0

        for row in range(self.ui.treeView.rowCount()):
            data = self.ui.treeView.item(row, 1).data(Qt.UserRole)
            if not data: continue

            row_mime = data.get('content_type', '')

            # 判斷類型是否符合
            if f_type_selection == "全部":
                type_match = True
            else:
                # 檢查該列的類型是否在我們選定的群組或單一類型中
                type_match = row_mime in target_mimes

            match = (f_title in data.get('title', '').lower()) and \
                    (f_summary in data.get('summary', '').lower()) and \
                    type_match

            self.ui.treeView.setRowHidden(row, not match)
            if match: visible_count += 1

        self.update_status_info()

    def handle_addnew(self):
        self.us17 = MainWindow_us17() # 新增檔案視窗
        self.us17.show()

    def save_current_state_to_cache(self):
        """將目前 UI 表格中的所有資料狀態同步回本地 json 快取"""
        cache_file = os.path.join(self.cache_dir, "last_query.json")
        try:
            current_results = []
            for row in range(self.ui.treeView.rowCount()):
                # 從標題欄 (Column 1) 取出當初存入的完整 dict
                item = self.ui.treeView.item(row, 1)
                if item:
                    data = item.data(Qt.UserRole)
                    if data:
                        current_results.append(data)

            # 封裝目前的參數 (包含 w_ 和 f_)
            params = {
                "title": self.ui.w_title.text(),
                "summary": self.ui.w_summary.text(),
                "limit": str(min(int(self.ui.w_counts.text()), self.query_max)),
                "content_type": self.ui.w_content_type.currentText(),
                "f_title": self.ui.f_title.text(),
                "f_summary": self.ui.f_summary.text(),
                "f_content_type": self.ui.f_content_type.currentText()
            }

            data_to_save = {
                "params": params,
                "results": current_results
            }

            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=4)

            # print("💾 本地快取檔案已同步更新")
        except Exception as e:
            print(f"同步快取失敗: {e}")

    def save_query_cache(self, params, results):
        """將查詢參數與結果存入本地 json"""
        cache_file = os.path.join(self.cache_dir, "last_query.json")
        try:
            # 加入本地篩選欄位的數值
            params["f_title"] = self.ui.f_title.text()
            params["f_summary"] = self.ui.f_summary.text()
            params["f_content_type"] = self.ui.f_content_type.currentText()

            data = {
                "params": params,
                "results": results
            }
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            print("💾 查詢紀錄與篩選參數已存入快取")
        except Exception as e:
            print(f"儲存快取失敗: {e}")

    def load_query_cache(self):
        """啟動時讀取上次的紀錄並還原 UI 與篩選狀態"""
        cache_file = os.path.join(self.cache_dir, "last_query.json")
        if not os.path.exists(cache_file):
            return

        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            params = data.get("params", {})
            results = data.get("results", [])

             # --- 1. 還原雲端查詢參數 (w_) ---
            self.ui.w_title.setText(params.get("title", ""))
            self.ui.w_summary.setText(params.get("summary", ""))
            w_counts = params.get("limit", str(self.query_max))
            w_counts = str(min(int(w_counts), self.query_max))
            self.ui.w_counts.setText(w_counts)

            w_idx = self.ui.w_content_type.findText(params.get("content_type", "全部"))
            if w_idx >= 0: self.ui.w_content_type.setCurrentIndex(w_idx)

            # --- 2. 還原本地篩選參數 (f_) ---
            self.ui.f_title.setText(params.get("f_title", ""))
            self.ui.f_summary.setText(params.get("f_summary", ""))

            f_idx = self.ui.f_content_type.findText(params.get("f_content_type", "全部"))
            if f_idx >= 0: self.ui.f_content_type.setCurrentIndex(f_idx)

            # 3. 還原表格資料
            if results:
                print(f"🚀 正在還原上次的查詢結果 ({len(results)} 筆)")
                self.render_table(results)
                self.apply_local_filter() # 還原資料後，立即套用一次本地篩選

        except Exception as e:
            print(f"讀取快取失敗: {e}")

    def render_table(self, data_list):
        self.threadpool.clear() # ✅ 渲染新資料前，取消所有還在排隊的下載任務
        table = self.ui.treeView

        # 關鍵：填充資料前暫停排序訊號
        table.setSortingEnabled(False)

        table.setRowCount(0) # 清空現有內容

        if not data_list: return

        table.setRowCount(len(data_list))
        table.setIconSize(QSize(60, 60)) # 設定圖示顯示大小

        # 先計算總共有多少張圖片需要下載大圖 進度用
        image_tasks = [item for item in data_list if "image" in item.get('content_type', '')]
        total_images = len(image_tasks)
        current_img_count = 0
        # ------------------------

        for row, item in enumerate(data_list):
            db_id = item.get('id') # 取得資料庫 UUID 或 ID

            # A. 縮圖欄 (暫時放文字，下一階段換成圖片)
            thumb_item = QTableWidgetItem("待處理")
            # 建議將 ID 存放在每一列的第一個單元格，作為識別證
            thumb_item.setData(Qt.UserRole, db_id)
            table.setItem(row, 0, thumb_item)

            # B. 標題
            title_item = QTableWidgetItem(item.get('title', '無標題'))
            # 將完整的資料 dict 存入該 Item 的 UserRole 中，方便點擊時取用
            title_item.setData(Qt.UserRole, item)
            table.setItem(row, 1, title_item)

            # C. 摘要
            summary_text = item.get('summary', '')
            if summary_text is None: summary_text = "" # 處理資料庫回傳 null 的情況
            table.setItem(row, 2, QTableWidgetItem(summary_text))

            # D. 類型
            table.setItem(row, 3, QTableWidgetItem(item.get('content_type', '-')))

            # E. 時間
            raw_date = item.get('created_at', '')
            formatted_date = raw_date[:10] if len(raw_date) >= 10 else raw_date
            table.setItem(row, 4, QTableWidgetItem(formatted_date))

            # F. 檔案處理 (縮圖與背景大圖)
            file_path = item.get('file_path', '')
            content_type = item.get('content_type', '')
            # print('content_type:', content_type)
            if "image" in content_type:
                # 任務 A: 縮圖 (這會更新 UI)
                worker = ThumbWorker(row, file_path)
                worker.signals.finished_one.connect(self.update_row_icon)
                # 交給線程池排隊執行
                self.threadpool.start(worker)

                # 任務 B: 大圖預覽 (純背景下載，不更新 UI)
                current_img_count += 1 # 進度
                worker_full = FullImageDownloader(file_path, current_img_count, total_images)
                # 連結進度訊號
                worker_full.signals.progress.connect(self.update_full_img_status)

                # 如果是最後一張，顯示完成提示
                if current_img_count == total_images:
                    worker_full.signals.finished_all.connect(self.on_all_downloads_finished)

                self.threadpool.start(worker_full)

            icon_pdf = QIcon(os.path.join(ROOT_DIR, 'system', 'icons', 'pdf.png'))
            icon_css = QIcon(os.path.join(ROOT_DIR, 'system', 'icons', 'css.png'))
            icon_js = QIcon(os.path.join(ROOT_DIR, 'system', 'icons', 'js.png'))
            icon_json = QIcon(os.path.join(ROOT_DIR, 'system', 'icons', 'json.png'))
            icon_xml = QIcon(os.path.join(ROOT_DIR, 'system', 'icons', 'xml.png'))
            icon_txt = QIcon(os.path.join(ROOT_DIR, 'system', 'icons', 'txt.png'))
            icon_markdown = QIcon(os.path.join(ROOT_DIR, 'system', 'icons', 'markdown.png'))
            icon_svg = QIcon(os.path.join(ROOT_DIR, 'system', 'icons', 'svg.png'))
            icon_map = {
                'application/pdf': icon_pdf,
                'application/xml': icon_xml,
                'application/json': icon_json,
                'application/manifest+json': icon_json,
                'text/css':        icon_css,
                'text/plain':      icon_txt,
                'text/javascript': icon_js,
                'text/markdown':   icon_markdown,
                'image/svg+xml':   icon_svg,
            }

            if content_type in icon_map.keys():
                self.ui.treeView.setItem(row, 0, QTableWidgetItem(icon_map[content_type], ""))

        # 設定行高
        for i in range(len(data_list)):
            table.setRowHeight(i, 60)

        # 填充完畢，恢復排序功能
        table.setSortingEnabled(True)
        print(f"✅ 成功渲染 {len(data_list)} 筆資料，背景下載任務啟動：{total_images} 筆")

    def update_full_img_status(self, current, total, file_name):
        self.statusBar().showMessage(f"背景預載圖片中... ({current}/{total})")

    def on_all_downloads_finished(self):
        """下載完成後維持 3 秒提示再消失"""
        self.statusBar().showMessage("所有大圖快取完成", 3000)

    def update_row_icon(self, row, icon):
        # 1. 先取得該儲存格原本的 Item
        old_item = self.ui.treeView.item(row, 0)
        # 2. 備份原本存放在 UserRole 的 db_id (避免被覆蓋)
        db_id = old_item.data(Qt.UserRole) if old_item else None

        # 3. 建立帶有縮圖的新 Item
        new_item = QTableWidgetItem(icon, "")
        # 4. 將備份的 ID 放回新 Item 中
        if db_id:
            new_item.setData(Qt.UserRole, db_id)

        # ✅ 額外優化：讓圖標在格子內置中，並移除選取時的虛線框
        new_item.setTextAlignment(Qt.AlignCenter)
        new_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

        # 5. 更新回表格
        self.ui.treeView.setItem(row, 0, new_item)
    def get_selected_row_id(self):
        """獲取目前選中列的資料庫 ID"""
        current_row = self.ui.treeView.currentRow()
        if current_row < 0:
            return None

        # 從第 0 欄取出剛才存入的 UserRole 資料
        db_id = self.ui.treeView.item(current_row, 0).data(Qt.UserRole)
        return db_id

    def on_selection_changed(self, selected, deselected):
        indexes = self.ui.treeView.selectedIndexes()
        if not indexes:
            return
        row = indexes[0].row()
        self.handle_selection_changed(row, 1)

    def handle_selection_changed(self, row, column):
        # 1. 從標題欄取出完整資料物件
        data = self.ui.treeView.item(row, 1).data(Qt.UserRole)
        if not data: return # 安全檢查，防止 data 為 None

        file_path = data.get('file_path')
        content_type = data.get('content_type', '')
        # print('file_path:', file_path)
        if "image" in content_type and file_path:
            self.show_image_preview(file_path)
        else:
            self.clear_preview(f"{file_path} 僅支援圖片預覽")

    def show_image_preview(self, file_path):
        if not file_path: return

        try:
            # 1. 統一路徑格式 (確保雜湊 Key 與背景下載器完全一致)
            clean_path = file_path.lstrip('/')
            ext = os.path.splitext(clean_path)[1].lower()

            # 僅針對相對路徑做雜湊，避免因為 Base URL 不同導致檔名不同
            name_hash = hashlib.md5(clean_path.encode()).hexdigest()
            local_full_path = os.path.join(self.cache_dir, f"full_{name_hash}{ext}")
            # print('local_full_path:', local_full_path)
            # 2. 策略：優先從硬碟讀取快取
            if os.path.exists(local_full_path):
                # print(f"🚀 從本地快取載入大圖: {local_full_path}")
                pixmap = QPixmap(local_full_path)
                if not pixmap.isNull():
                    # 順利載入快取，直接顯示並結束
                    # print(f"self.set_pixmap_to_label(pixmap)")
                    self.set_pixmap_to_label(pixmap)
                    self.statusBar().showMessage(f"{file_path} 讀取本地快取")

                    return

            # 3. 如果快取不存在，則進行連網下載
            # 注意：這裡使用 requests 會阻塞 UI，建議增加 timeout
            base = WEB_SPECIC_ASSETS_URL.rstrip('/')
            url = f"{base}/{clean_path}"
            # print(f"雲端下載大圖: {url}")
            self.statusBar().showMessage(f"{file_path} 正在從雲端載入原圖...")

            # 執行下載 (增加 timeout 防止網路中斷時程式卡死)
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                img_data = response.content
                pixmap = QPixmap()
                pixmap.loadFromData(img_data)

                if not pixmap.isNull():
                    self.set_pixmap_to_label(pixmap)

                    # 寫入快取供下次使用
                    with open(local_full_path, 'wb') as f:
                        f.write(img_data)
                    self.statusBar().showMessage(f"{file_path} 圖片載入完成並已快取")

                else:
                    self.clear_preview(f"{file_path} 圖片格式錯誤")
            else:
                self.clear_preview(f"{file_path} 下載失敗 ({response.status_code})")

        except requests.exceptions.RequestException as e:
            self.clear_preview("網路連線異常")
            print(f"❌ 預覽下載異常: {e}")
        except Exception as e:
            self.clear_preview("預覽發生錯誤")
            print(f"❌ show_image_preview 崩潰: {e}")


    def set_pixmap_to_label(self, pixmap):
        label = self.ui.label_preview
        container = self.ui.scrollAreaWidgetContents # 取得 label 的父容器
        if not label or not container: return

        # 1. 儲存原始圖片（供 resizeEvent 使用）
        label.setProperty("original_pixmap", pixmap)

        # 2. 取得可視區域 (Viewport) 大小
        view_size = self.ui.scrollArea.viewport().size()
        vw, vh = view_size.width(), view_size.height()

        # 3. 縮放圖片以適應視窗
        scaled_pixmap = pixmap.scaled(
            vw - 2, vh - 2,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        label.setPixmap(scaled_pixmap)

        # 4. 讓 Label 大小等於圖片大小
        sw, sh = scaled_pixmap.width(), scaled_pixmap.height()
        label.resize(sw, sh)

        # 5. 🚀 手動計算 Left, Top 座標 (讓 Label 在容器中置中)
        # 確保容器 Widget 至少跟 Viewport 一樣大
        container.setMinimumSize(view_size)

        new_x = (vw - sw) // 2
        new_y = (vh - sh) // 2

        # 6. 直接設定位置
        label.move(new_x, new_y)
        # print(f"手動定位完成: x={new_x}, y={new_y}, size={sw}x{sh}")

    def clear_preview(self, message=""):
        """清除 ScrollArea 內的內容，並可選擇顯示文字提示"""
        label = self.ui.label_preview
        if isinstance(label, QLabel):
            label.clear()       # 清除圖片
            label.setText(message)
            label.adjustSize()  # 重置大小
        self.statusBar().showMessage(f"{message}", 3000)

    def clear_preview(self, message=""):
        """清除預覽並將提示文字手動置中"""
        label = self.ui.label_preview
        if not isinstance(label, QLabel):
            return

        label.clear()
        label.setText(message)

        label.adjustSize() # 讓 Label 根據文字內容縮小到剛好大小

        view_size = self.ui.scrollArea.viewport().size()
        vw, vh = view_size.width(), view_size.height()

        lw, lh = label.width(), label.height()
        new_x = (vw - lw) // 2
        new_y = (vh - lh) // 2
        label.move(new_x, new_y)

        # 同步狀態列訊息
        if message:
            self.statusBar().showMessage(f"{message}", 3000)

    def show_context_menu(self, pos):
        row = self.ui.treeView.currentRow()
        if row < 0: return

        menu = QMenu()
        action_edit = menu.addAction(QIcon(), "編輯資料")
        menu.addSeparator()
        action_open_browser = menu.addAction(QIcon(), "從瀏覽器開啟")
        action_copy = menu.addAction(QIcon(), "複製連結")
        action_copy_file_path = menu.addAction(QIcon(), "複製路徑")
        menu.addSeparator()
        action_delete = menu.addAction(QIcon(), "刪除檔案")
        # 顯示選單並取得點擊項目
        action = menu.exec_(self.ui.treeView.viewport().mapToGlobal(pos))

        if action == action_edit:
            self.handle_edit_row(row)
        elif action == action_open_browser:
            self.handle_open_in_browser(row)
        elif action == action_copy:
            self.handle_copy_link(row)
        elif action == action_copy_file_path:
            self.handle_copy_file_path(row)
        elif action == action_delete:
            self.handle_delete_row(row)

    def handle_open_in_browser(self, row):
        """取得 URL 並呼叫系統預設瀏覽器開啟"""
        data = self.ui.treeView.item(row, 1).data(Qt.UserRole)
        file_path = data.get('file_path', '')
        if not file_path: return
        url_string = f"{WEB_SPECIC_ASSETS_URL}/{file_path}"
        QDesktopServices.openUrl(QUrl(url_string))
        self.statusBar().showMessage(f"已在瀏覽器開啟", 2000)

    def handle_copy_link(self, row):
        data = self.ui.treeView.item(row, 1).data(Qt.UserRole)
        file_path = data.get('file_path', '')
        if not file_path: return
        url = f"{WEB_SPECIC_ASSETS_URL}/{file_path}"
        clipboard = QApplication.clipboard()
        clipboard.setText(url)
        self.statusBar().showMessage(f"已複製連結: {url}", 3000)

    def handle_copy_file_path(self, row):
        data = self.ui.treeView.item(row, 1).data(Qt.UserRole)
        file_path = data.get('file_path', '')
        if not file_path: return
        clipboard = QApplication.clipboard()
        clipboard.setText(file_path)
        self.statusBar().showMessage(f"已複製路徑: {file_path}", 3000)

    def handle_edit_row(self, row):
        item = self.ui.treeView.item(row, 1) # 假設標題在第 2 欄
        data = item.data(Qt.UserRole)
        db_id = data.get('id')

        dialog = EditFileInfoDialog(data.get('title', ''), data.get('summary', ''), self)

        if dialog.exec_() == QDialog.Accepted:
            new_title, new_summary = dialog.get_values()
            update_data = {"title": new_title,"summary": new_summary}

            if self.sb.update_storage(db_id, update_data):
                # 同步更新 UI 表格顯示
                self.ui.treeView.item(row, 1).setText(new_title)
                self.ui.treeView.item(row, 2).setText(new_summary) # 假設摘要在第 3 欄

                # 更新記憶體中的 data 物件
                data['title'] = new_title
                data['summary'] = new_summary
                item.setData(Qt.UserRole, data)

                # 立即同步到硬碟的 last_query.json
                self.save_current_state_to_cache()
                self.statusBar().showMessage(f"資料已更新並同步快取", 3000)
            else:
                QMessageBox.critical(self, "錯誤", "資料庫更新失敗，請檢查網路。")

    def handle_delete_row(self, row):
        item = self.ui.treeView.item(row, 1)
        data = item.data(Qt.UserRole)
        db_id = data.get('id')
        file_path = data.get('file_path')

        confirm = QMessageBox.question(self, "確認刪除",
                                     f"確定要刪除「{data.get('title')}」嗎？\n此動作無法還原。",
                                     QMessageBox.Yes | QMessageBox.No)

        if confirm == QMessageBox.Yes:
            # 1. 執行連動刪除 (DB + Cloud)
            if self.sb.delete_storage(db_id):
                self.clear_local_file_cache(file_path) # 刪除圖檔
                self.ui.treeView.removeRow(row)        # 移除 UI 行
                self.save_current_state_to_cache()     # 同步更新本地 JSON 檔案
                self.update_status_info()
                # print(f"🗑️ 已刪除並同步快取")
            else:
                QMessageBox.warning(self, "失敗", "刪除程序未完全成功。")

    def clear_local_file_cache(self, file_path):
        """根據路徑雜湊值，精準刪除硬碟上的快取檔"""
        name_hash = hashlib.md5(file_path.encode()).hexdigest()
        ext = os.path.splitext(file_path)[1]
        for prefix in ["thumb_", "full_"]:
            target = os.path.join(self.cache_dir, f"{prefix}{name_hash}{ext}")
            if os.path.exists(target):
                os.remove(target)
                print(f"🧹 已清理本地快取: {target}")

    def update_status_info(self):
        """計算並更新狀態列的筆數統計"""
        total_rows = self.ui.treeView.rowCount()
        visible_rows = 0

        for row in range(total_rows):
            if not self.ui.treeView.isRowHidden(row):
                visible_rows += 1

        # 更新顯示文字
        self.count_label.setText(f"篩選 {visible_rows} 筆 / 查詢 {total_rows} 筆")

    def toggle_loading_overlay(self, show=True):
        """控制載入遮罩的顯示與隱藏"""
        self.ui.treeView.setEnabled(not show)
        if show:
            if not hasattr(self, 'overlay'):
                # 建立遮罩 QLabel，父元件設定為 treeView
                self.overlay = QLabel(self.ui.treeView)
                self.overlay.setStyleSheet("""
                    background-color: rgba(51, 51, 51, 0.5);
                    color: #000000;
                    font-family: "Microsoft JhengHei", "Segoe UI";
                    font-size: 20px;
                    border: none;
                """)
                self.overlay.setAlignment(Qt.AlignCenter)
                # 你可以使用 Emoji 增加動態感
                self.overlay.setText("讀取中...請稍候")

            # 確保遮罩完全覆蓋目前的 treeView 區域
            self.overlay.resize(self.ui.treeView.size())
            self.overlay.show()
            self.overlay.raise_() # 確保遮罩在最上層
            QApplication.processEvents() # 刷新
        else:
            if hasattr(self, 'overlay'):
                self.overlay.hide()

def main():
    app = QApplication(sys.argv)
    # argv1 = sys.argv[1] if len(sys.argv) > 1 else "no argv" # 預留參數接口
    # print('argv1:', argv1)

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()