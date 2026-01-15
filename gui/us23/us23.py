# us23.py
if True:
    import sys
    import os
    import hashlib
    import json
    import markdown
    from markdown.treeprocessors import Treeprocessor
    from markdown.extensions import Extension

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
    from share_qt5 import * # 所有 qt5
    from tool_time import get_local_time_tz, format_to_local_time
    from tool_pd_article import ProductArticle

    sys.path.append(os.path.join(ROOT_DIR, 'gui', 'us23'))
    from form_us23 import Ui_MainWindow

# --- Markdown 圖片本地化擴充 ---
def get_local_cache_path(file_path, prefix="full_"):
    # 對應 us15.py 的邏輯：將相對路徑轉為本地快取路徑
    if not file_path: return ""
    clean_path = file_path.lstrip('/')
    ext = os.path.splitext(clean_path)[1].lower()
    name_hash = hashlib.md5(clean_path.encode()).hexdigest()
    return os.path.join(ISPC_MAINTAIN_CACHE_DIR, f"{prefix}{name_hash}{ext}")

class LocalImageTreeprocessor(Treeprocessor):
    def run(self, root):
        for img in root.iter("img"):
            src = img.get("src")
            if src and src.startswith("images/"):
                local_path = get_local_cache_path(src)
                if os.path.exists(local_path):
                    # 只要給它正確的本地路徑即可
                    img.set("src", "file:///" + local_path.replace("\\", "/"))

class LocalImageExtension(Extension):
    def extendMarkdown(self, md):
        md.treeprocessors.register(LocalImageTreeprocessor(md), "local_image", 15)


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow();
        self.ui.setupUi(self) # 載入ui

        self.setWindowTitle('Markdown Editer')
        self.resize(1228, 500)  # 設定視窗大小
        self.pa = ProductArticle()
        self.all_data = []  # 儲存從雲端抓回來的原始資料
        self.last_html_body = ""
        self.cache_file = os.path.join(ISPC_MAINTAIN_CACHE_DIR, "last_article_query.json")
        self.is_loading_state = False # 防止載入快取時觸發過多事件

        # 初始化順序
        self.init_ui_components()
        self.init_markdown_engine()
        self.init_signals()

        # 恢復上次狀態
        self.load_ui_state()
        self.update_render()

    def init_ui_components(self):
        """初始化 UI 組件設定"""
        self.setWindowTitle('Markdown Editor')
        self.resize(1300, 750)
        # 表格設定
        table = self.ui.article_table
        table.setEditTriggers(QAbstractItemView.NoEditTriggers) # 不可編輯
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["自訂ID", "標題", "最後更新"])
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setAlternatingRowColors(True)

        # 瀏覽器設定
        self.browser = QWebEngineView(self.ui.tab_widget.widget(0))

        # 載入 CSS
        css_path = os.path.join(ROOT_DIR, 'gui', 'us23', 'style.css')
        self.css_style = ""
        if os.path.exists(css_path):
            with open(css_path, 'r', encoding='utf-8') as f:
                self.css_style = f"<style>{f.read()}</style>"
        self.ui.style_code_view.setPlainText(self.css_style)

    def init_markdown_engine(self):
        """初始化 Markdown 引擎與防抖計時器"""
        self.md_engine_loacl = markdown.Markdown(extensions=['fenced_code', 'tables', LocalImageExtension()])

        self.md_engine_clean = markdown.Markdown(extensions=[
            'extra',          # 支援表格、註腳等
            'codehilite',     # 程式碼高亮
            'tables',         # 表格支援
            'fenced_code'     # 圍欄程式碼區塊
        ])

        self.render_timer = QTimer()
        self.render_timer.setSingleShot(True)
        self.render_timer.timeout.connect(self.update_render)


    def init_signals(self):
        """綁定所有 UI 訊號"""
        # 查詢按鈕
        self.ui.btn_addnew.clicked.connect(self.on_addnew_clicked)
        self.ui.btn_query.clicked.connect(self.on_query_clicked)
        self.ui.btn_save.clicked.connect(self.on_save_clicked)
        self.ui.btn_delete.clicked.connect(self.on_delete_clicked)

        # 本地篩選 (連動渲染表格)
        self.ui.f_custom_index.textChanged.connect(self.refresh_table_view)
        self.ui.f_title.textChanged.connect(self.refresh_table_view)
        self.ui.f_content.textChanged.connect(self.refresh_table_view)

        # 列表選取連動編輯器
        self.ui.article_table.itemSelectionChanged.connect(self.load_selected_article)
        self.ui.article_table.cellClicked.connect(self.load_selected_article)

        # 編輯器內容改變 (觸發防抖渲染)
        self.ui.editor_input.textChanged.connect(lambda: self.render_timer.start(350))

        # 同步捲動
        self.ui.editor_input.verticalScrollBar().valueChanged.connect(self.sync_scroll)



    def refresh_table_view(self):
        """純本地篩選觸發的渲染"""
        if self.is_loading_state: return
        self.render_table(self.all_data)
        self.save_ui_state()

    def on_query_clicked(self):
        """點擊查詢按鈕：從雲端抓取"""
        params = {}
        if self.ui.w_custom_index.text():
            params['custom_index'] = f"ilike.*{self.ui.w_custom_index.text()}*"
        if self.ui.w_title.text():
            params['title'] = f"ilike.*{self.ui.w_title.text()}*"
        if self.ui.w_content.text():
            params['content'] = f"ilike.*{self.ui.w_content.text()}*"

        limit = int(self.ui.w_counts.text()) if self.ui.w_counts.text().isdigit() else 200

        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            results = self.pa.select_multiple(params, limit=limit)
            if results is not None:
                self.all_data = results
                self.render_table(results)
                self.save_ui_state() # 儲存狀態及所有資料
        finally:
            QApplication.restoreOverrideCursor()

    def on_addnew_clicked(self):
        """點擊新增按鈕：清空右側編輯器"""
        # 取消左側列表的選取（防止誤導）
        self._last_selected_id = None
        self.ui.article_table.clearSelection()

        # 清空右側
        self.ui.editor_custom_index.clear()
        self.ui.editor_custom_index.setReadOnly(False) # 新增時通常允許編輯 ID
        self.ui.editor_custom_index.setPlaceholderText("請輸入自訂ID...")
        self.ui.editor_title.clear()
        self.ui.editor_title.setPlaceholderText("請輸入新文章標題...")
        self.ui.editor_input.clear()

        # 焦點移至標題
        self.ui.editor_title.setFocus()

        # 更新視窗標題標記為新文章
        self.setWindowTitle("Markdown Editor - [新建文章模式]")
        self.statusBar().showMessage("進入新建模式，請輸入內容後按下儲存", 5000)

    def on_save_clicked(self):
        """儲存按鈕：自動判斷 新增 或 更新"""

        # 1. 取得 UI 資料
        current_id = self.ui.editor_custom_index.text().strip()
        current_title = self.ui.editor_title.text().strip()
        current_content = self.ui.editor_input.toPlainText()

        # 2. 檢查必填欄位
        if not current_id or not current_title:
            QMessageBox.warning(self, "錯誤", "自訂ID與標題為必填項目")
            return

        self.md_engine_clean.reset()
        clean_html = self.md_engine_clean.convert(current_content)

        # 3. 判斷模式：根據左側表格是否有選中列來決定
        selected_ranges = self.ui.article_table.selectedRanges()
        is_update_mode = len(selected_ranges) > 0

        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            if is_update_mode:
                # --- 更新模式 ---
                # 取得選中列原始的 ID (防止使用者改了 ID 欄位導致對不上)
                row = selected_ranges[0].topRow()
                original_id = self.ui.article_table.item(row, 0).text()

                update_data = {
                    "custom_index": current_id, # 允許修改 ID
                    "title": current_title,
                    "content": current_content,
                    "html_snapshot": clean_html,
                    "updated_at": get_local_time_tz()
                }
                result = self.pa.update(original_id, update_data)
                msg_prefix = "更新"
            else:
                # --- 新增模式 ---
                insert_data = {
                    "custom_index": current_id,
                    "title": current_title,
                    "content": current_content,
                    "html_snapshot": clean_html
                }
                result = self.pa.insert(insert_data)
                msg_prefix = "新增"

            # 4. 處理結果
            if result:
                # 無論新增或更新，只要有 custom_index，就通知 Cloudflare 清除快取
                self.pa.cloudflare_purge_snippet(current_id)

                # 更新本地記憶體 all_data
                if is_update_mode:
                    # 找到舊資料並替換
                    for i, item in enumerate(self.all_data):
                        if str(item.get('custom_index')) == original_id:
                            self.all_data[i] = result if isinstance(result, dict) else update_data
                            break
                else:
                    # 新增資料插入到最前面
                    self.all_data.insert(0, result if isinstance(result, dict) else insert_data)

                # 5. UI 同步與快取
                self.ui.article_table.blockSignals(True)
                self.render_table(self.all_data)
                self.ui.article_table.blockSignals(False)

                self.save_ui_state() # 寫入 last_article_query.json
                self._last_selected_id = current_id
                self.statusBar().showMessage(f"{msg_prefix}成功：{current_id}", 3000)
                QMessageBox.information(self, "完成", f"文章已成功{msg_prefix}")
            else:
                QMessageBox.critical(self, "失敗", f"雲端{msg_prefix}失敗，請檢查網路或 ID 是否重複")

        except Exception as e:
            QMessageBox.critical(self, "錯誤", f"執行時發生異常: {str(e)}")
        finally:
            QApplication.restoreOverrideCursor()

    def on_delete_clicked(self):
        """刪除按鈕邏輯"""
        # 1. 檢查是否有選中項目
        selected_ranges = self.ui.article_table.selectedRanges()
        if not selected_ranges:
            QMessageBox.warning(self, "提示", "請先從列表中選取要刪除的文章")
            return

        current_row = selected_ranges[0].topRow()
        custom_index = self.ui.article_table.item(current_row, 0).text()
        title = self.ui.article_table.item(current_row, 1).text()

        # 2. 二次確認對話框
        reply = QMessageBox.question(self, '確認刪除',
            f"您確定要刪除這篇文章嗎？\n\nID: {custom_index}\n標題: {title}\n\n注意：刪除後無法復原。",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            try:
                # 3. 執行雲端刪除
                success = self.pa.delete(custom_index)

                if success:
                    # 4. 從本地記憶體 all_data 移除該筆資料
                    self.all_data = [item for item in self.all_data if str(item.get('custom_index')) != custom_index]

                    # 5. 刷新 UI
                    self.render_table(self.all_data)

                    # 6. 清空編輯器 (因為該文章已不存在)
                    self.ui.editor_custom_index.clear()
                    self.ui.editor_title.clear()
                    self.ui.editor_input.clear()

                    # 7. 更新快取檔案
                    self.save_ui_state()

                    self.statusBar().showMessage(f"已刪除文章: {custom_index}", 3000)
                    QMessageBox.information(self, "成功", "文章已成功刪除")

                    self.on_addnew_clicked() # 新增模式

                else:
                    QMessageBox.critical(self, "失敗", "雲端刪除失敗，請檢查網路連線")
            except Exception as e:
                QMessageBox.critical(self, "錯誤", f"刪除時發生異常: {str(e)}")
            finally:
                QApplication.restoreOverrideCursor()

    def render_table(self, data_list):
        """執行過濾並填充表格 UI"""
        f_id = self.ui.f_custom_index.text().lower()
        f_title = self.ui.f_title.text().lower()
        f_content = self.ui.f_content.text().lower()

        filtered = [
            item for item in data_list
            if f_id in str(item.get('custom_index', '')).lower()
            and f_title in str(item.get('title', '')).lower()
            and f_content in str(item.get('content', '')).lower()
        ]

        self.ui.article_table.blockSignals(True) # 渲染時暫時擋住訊號，防止誤發 load_selected
        self.ui.article_table.setRowCount(len(filtered))
        for row, item in enumerate(filtered):
            self.ui.article_table.setItem(row, 0, QTableWidgetItem(str(item.get('custom_index', ''))))
            self.ui.article_table.setItem(row, 1, QTableWidgetItem(str(item.get('title', ''))))
            updated_at = format_to_local_time(item.get('updated_at', ''))
            self.ui.article_table.setItem(row, 2, QTableWidgetItem(updated_at))
        self.ui.article_table.blockSignals(False)

    def load_selected_article(self):
        # print('load_selected_article')
        """切換文章時檢查 dirty 狀態，若未儲存則詢問是否放棄"""
        # 如果正在加載初始狀態，跳過檢查
        if getattr(self, 'is_loading_state', False):
            self.execute_load_data() # 將讀取 UI 的動作抽離出來
            return

        # 取得目前點擊的列 (新的選取項)
        selected_ranges = self.ui.article_table.selectedRanges()
        if not selected_ranges: return
        new_row = selected_ranges[0].topRow()
        new_id = self.ui.article_table.item(new_row, 0).text()

        # --- 關鍵修正：如果是重複點擊同一列，且目前不是 Dirty，就直接跳過 ---
        # 這樣可以避免重複點擊時一直執行讀取
        if hasattr(self, '_last_selected_id') and new_id == self._last_selected_id:
            if not self.is_dirty():
                return
        # -------------------------------------------------------------

        # --- Dirty Check 核心邏輯 ---
        # 如果之前有選過文章 (不是第一次開啟)，且內容已被修改
        if hasattr(self, '_last_selected_id') and self.is_dirty():
            # 如果新選的 ID 跟舊的一樣（點到同一列），則不觸發詢問
            if new_id != self._last_selected_id:
                reply = QMessageBox.question(
                    self, "尚未儲存", "尚未儲存，您確定要離開嗎?",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

                if reply == QMessageBox.No:
                    # 使用者想留下來，將 Table 選取狀態強制跳回「原本編輯中」的那一列
                    self.ui.article_table.blockSignals(True)
                    for row in range(self.ui.article_table.rowCount()):
                        if self.ui.article_table.item(row, 0).text() == self._last_selected_id:
                            self.ui.article_table.selectRow(row)
                            break
                    self.ui.article_table.blockSignals(False)
                    return # 終止方法，不讀取新資料
        # --------------------------

        # --- 執行讀取新資料邏輯 ---
        self._last_selected_id = new_id  # 更新最後選取的 ID

        target = next((item for item in self.all_data if str(item.get('custom_index')) == new_id), None)
        if target:
            # 填入 UI
            self.ui.editor_custom_index.setText(target.get('custom_index', ''))
            self.ui.editor_title.setText(target.get('title', ''))
            self.ui.editor_input.setPlainText(target.get('content', ''))
            self.setWindowTitle(f"Markdown Editor - {target.get('title', '')}")
            self.update_render()

    def execute_load_data(self):
        """純粹執行資料填入 UI 的動作，不含邏輯判斷"""
        selected_ranges = self.ui.article_table.selectedRanges()
        if not selected_ranges: return

        row = selected_ranges[0].topRow()
        current_id = self.ui.article_table.item(row, 0).text()
        self._last_selected_id = current_id # 更新目前的追蹤 ID

        target = next((item for item in self.all_data if str(item.get('custom_index')) == current_id), None)
        if target:
            self.ui.editor_custom_index.setText(target.get('custom_index', ''))
            self.ui.editor_title.setText(target.get('title', ''))
            self.ui.editor_input.setPlainText(target.get('content', ''))
            # 確保觸發預覽刷新
            self.update_render()

    def update_render(self):
        """Markdown 渲染至瀏覽器"""
        raw_text = self.ui.editor_input.toPlainText()
        self.md_engine_loacl.reset()
        html_body = self.md_engine_loacl.convert(raw_text)

        if html_body == self.last_html_body: return
        self.last_html_body = html_body

        full_html = f"""
        <!DOCTYPE html><html><head><meta charset="utf-8">{self.css_style}</head>
        <body id="content_body"><div id="content">{html_body}</div></body></html>
        """
        # 使用 setHtml，並設定路徑以抓取本地圖片
        base_url = QUrl.fromLocalFile(ISPC_MAINTAIN_CACHE_DIR + os.path.sep)
        self.browser.setHtml(full_html, base_url)
        self.ui.html_code_view.setPlainText(html_body)

        # clean_html_view
        md_text = self.ui.editor_input.toPlainText()
        self.md_engine_clean.reset()
        clean_html = self.md_engine_clean.convert(md_text)
        self.ui.clean_html_view.setPlainText(clean_html)

        QTimer.singleShot(50, self.sync_scroll)

    def sync_scroll(self):
        """編輯器與瀏覽器同步捲動"""
        cursor = self.ui.editor_input.textCursor()
        total_blocks = self.ui.editor_input.document().blockCount()
        current_block = cursor.blockNumber() + 1
        percentage = current_block / total_blocks if total_blocks > 1 else 0

        js_code = f"""
            var scrollHeight = document.documentElement.scrollHeight;
            var clientHeight = document.documentElement.clientHeight;
            window.scrollTo({{ top: (scrollHeight * {percentage}) - (clientHeight / 2), behavior: 'smooth' }});
        """
        if hasattr(self, 'browser'):
            self.browser.page().runJavaScript(js_code)

    # --- 狀態存取邏輯 ---
    def save_ui_state(self):
        state = {
            "results": self.all_data,
            "query": {
                "custom_index": self.ui.w_custom_index.text(),
                "title": self.ui.w_title.text(),
                "content": self.ui.w_content.text(),
                "counts": self.ui.w_counts.text()
            },
            "filter": {
                "custom_index": self.ui.f_custom_index.text(),
                "title": self.ui.f_title.text(),
                "content": self.ui.f_content.text()
            }
        }
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=4)
        except Exception as e: print(f"Save failed: {e}")

    def load_ui_state(self):
        if not os.path.exists(self.cache_file): return
        self.is_loading_state = True
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                state = json.load(f)

            q = state.get("query", {})
            self.ui.w_custom_index.setText(q.get("custom_index", ""))
            self.ui.w_title.setText(q.get("title", ""))
            self.ui.w_content.setText(q.get("content", ""))
            self.ui.w_counts.setText(q.get("counts", "200"))

            fp = state.get("filter", {})
            self.ui.f_custom_index.setText(fp.get("custom_index", ""))
            self.ui.f_title.setText(fp.get("title", ""))
            self.ui.f_content.setText(fp.get("content", ""))

            self.all_data = state.get("results", [])
            if self.all_data:
                self.render_table(self.all_data)

            if self.all_data and self.ui.article_table.rowCount() > 0:
                # 假設預設選中第一列
                self.ui.article_table.selectRow(0)
                self._last_selected_id = self.ui.article_table.item(0, 0).text()

            if self.all_data and self.ui.article_table.rowCount() > 0:
                # 開啟旗標：告訴 load_selected_article 現在是自動化流程，不要問 Dirty
                self.is_loading_state = True

                # 1. 強制選取第一列 (這會觸發 load_selected_article)
                self.ui.article_table.selectRow(0)

                # 2. 取得第一列的 ID 並初始化
                first_id = self.ui.article_table.item(0, 0).text()
                self._last_selected_id = first_id

                # 關閉旗標：恢復正常的 Dirty Check 攔截功能
                self.is_loading_state = False

        except Exception as e: print(f"Load failed: {e}")
        finally:
            self.is_loading_state = False

    def get_current_editor_data(self):
        """取得目前編輯器中的內容物件"""
        return {
            "custom_index": self.ui.editor_custom_index.text().strip(),
            "title": self.ui.editor_title.text().strip(),
            "content": self.ui.editor_input.toPlainText()
        }

    def is_dirty(self):
        # 1. 取得目前 UI 上的內容
        curr = self.get_current_editor_data()

        # 情況 A：新增模式 (目前沒有追蹤任何已存在的文章)
        if not hasattr(self, '_last_selected_id') or self._last_selected_id is None:
            # 只要 ID、標題或內容任一處有填寫，就判定為 Dirty (避免切換時消失)
            return any([curr["custom_index"], curr["title"], curr["content"]])

        # 情況 B：編輯模式 (正在編輯某篇已存在的文章)
        # 從 self.all_data 找出該篇文章原始的數值
        origin = next((item for item in self.all_data
                       if str(item.get('custom_index')) == str(self._last_selected_id)), None)

        # 如果找不到原始資料（理論上不應發生，除非資料被刪除），視為不髒
        if not origin:
            return False

        # 比對三項核心欄位
        # 注意：將原始數值轉為字串並 strip() 以確保比對基準一致
        is_changed = (
            curr["custom_index"] != str(origin.get("custom_index") or "").strip() or
            curr["title"] != str(origin.get("title") or "").strip() or
            curr["content"] != (origin.get("content") or "")
        )

        return is_changed

    def resizeEvent(self, event):
        # 取得視窗可用區域大小
        rect = self.centralWidget().contentsRect()
        win_w = rect.width()
        win_h = rect.height()

        if win_w <= 0 or win_h <= 0: return

        # --- 基礎參數設定 ---
        margin = 10        # 視窗邊距
        spacing = 10       # 組件間距
        left_w = 420       # 左側欄固定寬度
        title_h = 24       # 輸入框高度 (ID 與 標題共用)

        # 計算剩餘給「編輯」與「預覽」的寬度
        remaining_w = win_w - (margin * 2) - left_w - (spacing * 2)
        half_w = remaining_w // 2

        # ==========================================================
        # 1. 左側區域 (代碼維持不變...)
        # ==========================================================
        label_w = 81
        self.ui.label_w_custom_index.setGeometry(margin, margin, label_w, 24)
        self.ui.w_custom_index.setGeometry(margin + label_w+2, margin, left_w - label_w-2, 24)
        self.ui.label_w_title.setGeometry(margin, margin + 26, label_w, 24)
        self.ui.w_title.setGeometry(margin + label_w+2, margin + 26, left_w - label_w-2, 24)
        self.ui.label_w_content.setGeometry(margin, margin + 52, label_w, 24)
        self.ui.w_content.setGeometry(margin + label_w+2, margin + 52, left_w-2 - 122, 24)
        self.ui.w_counts.setGeometry(margin + left_w - 41, margin + 52, 41, 24)
        self.ui.btn_query.setGeometry(margin, margin + 78, left_w, 31)

        filter_start_y = margin + 115
        self.ui.label_f_custom_index.setGeometry(margin, filter_start_y, label_w, 24)
        self.ui.f_custom_index.setGeometry(margin + label_w+2, filter_start_y, left_w - label_w-2, 24)
        self.ui.label_f_title.setGeometry(margin, filter_start_y + 26, label_w, 24)
        self.ui.f_title.setGeometry(margin + label_w+2, filter_start_y + 26, left_w - label_w-2, 24)
        self.ui.label_f_content.setGeometry(margin, filter_start_y + 52, label_w, 24)
        self.ui.f_content.setGeometry(margin + label_w+2, filter_start_y + 52, left_w - label_w-2, 24)

        table_y = filter_start_y + 80
        table_h = win_h - table_y - margin
        self.ui.article_table.setGeometry(margin, table_y, left_w, table_h)

        # ==========================================================
        # 2. 中間區域 (新增/儲存/刪除按鈕 + ID編輯 + 標題編輯 + 內容編輯)
        # ==========================================================
        mid_x = margin + left_w + spacing

        # 按鈕橫列
        btn_w = (half_w - (spacing * 2)) // 3
        self.ui.btn_addnew.setGeometry(mid_x, margin, btn_w, 51)
        self.ui.btn_save.setGeometry(mid_x + btn_w + spacing, margin, btn_w, 51)
        self.ui.btn_delete.setGeometry(mid_x + (btn_w + spacing) * 2, margin, btn_w, 51)

        # --- 修改部分：加入 editor_custom_index ---
        # 自訂 ID 輸入框 (在按鈕下方)
        id_y = margin + 51 + 10
        self.ui.editor_custom_index.setGeometry(mid_x, id_y, half_w, title_h)

        # 文章標題輸入框 (在 ID 輸入框下方)
        title_y = id_y + title_h + 5
        self.ui.editor_title.setGeometry(mid_x, title_y, half_w, title_h)

        # Markdown 編輯器 (佔滿中間剩餘高度)
        editor_y = title_y + title_h + 5
        editor_h = win_h - editor_y - margin
        self.ui.editor_input.setGeometry(mid_x, editor_y, half_w, editor_h)

        # ==========================================================
        # 3. 右側區域 (代碼維持不變...)
        # ==========================================================
        right_x = mid_x + half_w + spacing
        self.ui.tab_widget.setGeometry(right_x, margin, half_w, win_h - (margin * 2))

        tab_inner_w = self.ui.tab_widget.width() - 2
        tab_inner_h = self.ui.tab_widget.height() - 45

        if hasattr(self, 'browser'):
            self.browser.setGeometry(0, 0, tab_inner_w, tab_inner_h)

        self.ui.clean_html_view.setGeometry(0, 0, tab_inner_w, tab_inner_h)
        self.ui.html_code_view.setGeometry(0, 0, tab_inner_w, tab_inner_h)
        self.ui.style_code_view.setGeometry(0, 0, tab_inner_w, tab_inner_h)

        super().resizeEvent(event)

    def closeEvent(self, event):
        self.save_ui_state()
        event.accept()

def main():
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu --disable-software-rasterizer"
    os.environ["QT_QUICK_BACKEND"] = "software"
    app = QApplication(sys.argv)
    # argv1 = sys.argv[1] if len(sys.argv) > 1 else "no argv" # 預留參數接口
    # print('argv1:', argv1)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()