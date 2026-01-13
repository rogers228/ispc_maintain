# us23.py
if True:
    import sys
    import os
    import hashlib
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
    from share_qt5 import * # 所有 qt5

    sys.path.append(os.path.join(ROOT_DIR, 'gui', 'us23'))
    from form_us23 import Ui_MainWindow

def get_local_cache_path(file_path, prefix="full_"):
    """
    對應 us15.py 的邏輯：將相對路徑轉為本地快取路徑
    """
    if not file_path: return ""

    clean_path = file_path.lstrip('/')
    ext = os.path.splitext(clean_path)[1].lower()
    name_hash = hashlib.md5(clean_path.encode()).hexdigest()

    cache_dir = os.path.join(os.getenv('LOCALAPPDATA'), "ISPC_Maintain", "cache")
    return os.path.join(cache_dir, f"{prefix}{name_hash}{ext}")

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

    def __init__(self, key):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow();
        self.ui.setupUi(self) # 載入ui
        self.setWindowTitle('Markdown Editer')
        self.resize(1228, 500)  # 設定視窗大小

        self.key = key # 由主表單傳入的 key 暫定，可能使用 key來讀取markdown 設定為預設值
        print('key:', key)

        self.last_html_body = ""

        # 快取路徑
        self.cache_dir = os.path.abspath(os.path.join(os.getenv('LOCALAPPDATA'), "ISPC_Maintain", "cache"))
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir, exist_ok=True)

        self.ui.editor_input.verticalScrollBar().valueChanged.connect(self.sync_scroll)
        # self.ui.editor_input.cursorPositionChanged.connect(self.sync_scroll) # 當游標位置改變時（打字、換行、滑鼠點擊），也觸發同步

        # 建立 Chromium 瀏覽器實例
        self.browser = QWebEngineView(self.ui.tab_widget.widget(0))

        # 1. 預先初始化 Markdown 引擎 (關鍵：解決第一個字卡頓)
        self.md_engine = markdown.Markdown(extensions=['fenced_code', 'tables', LocalImageExtension()])
        # 2. 設置防抖動計時器 (Debounce)
        self.render_timer = QTimer()
        self.render_timer.setSingleShot(True)
        self.render_timer.timeout.connect(self.update_render)

        # 讀取 CSS
        css_path = os.path.join(ROOT_DIR, 'gui', 'us23', 'style.css')
        if os.path.exists(css_path):
            with open(css_path, 'r', encoding='utf-8') as f:
                self.css_style = f"<style>{f.read()}</style>"
        else:
            self.css_style = ""

        self.ui.style_code_view.setPlainText(self.css_style)

        # 4. 根據傳入的 key 設定預設 Markdown 內容
        self.load_default_content(key)

        # 5. 綁定事件 (改為觸發計時器，不直接渲染)
        self.ui.editor_input.textChanged.connect(lambda: self.render_timer.start(350))

        # 6. 初始渲染
        self.update_render()

    def resizeEvent(self, event):
        rect = self.centralWidget().contentsRect()
        w, h = rect.width(), rect.height()
        if w <= 0 or h <= 0: return

        margin, spacing = 10, 10
        half_w = (w - (margin * 2) - spacing) // 2

        # 佈局主元件
        self.ui.editor_input.setGeometry(margin, margin, half_w, h - (margin * 2))
        self.ui.tab_widget.setGeometry(margin + half_w + spacing, margin, half_w, h - (margin * 2))

        # 讓瀏覽器填滿 Tab 內部空間
        # 使用 QTabWidget 的內部大小
        tab_inner_w = self.ui.tab_widget.width() - 2 # 扣除邊框誤差
        tab_inner_h = self.ui.tab_widget.height() - 35 # 扣除標籤欄高度 (大約值)

        self.browser.setGeometry(0, 0, tab_inner_w, tab_inner_h)
        self.ui.html_code_view.setGeometry(0, 0, tab_inner_w, tab_inner_h)
        self.ui.style_code_view.setGeometry(0, 0, tab_inner_w, tab_inner_h)


    def load_default_content(self, key):
        """根據傳入的參數讀取預設內容"""
        # 這裡可以根據 key 去資料庫或檔案讀取內容
        # 目前先設定一段自定義的測試 Markdown
        sample_text = f"""# 圖片預覽測試
這是一張來自雲端路徑但已快取至本地的圖片：

![我的圖片](images/f12ek1gxbb249ggp.jpg)

*如果本地快取資料夾有這張圖，上方會直接顯示。*
"""
        self.ui.editor_input.setPlainText(sample_text)

    def update_render(self):
        raw_text = self.ui.editor_input.toPlainText()
        self.md_engine.reset()
        html_body = self.md_engine.convert(raw_text)

        # 如果內容沒變，直接回傳，避免不必要的渲染
        if html_body == self.last_html_body:
            return
        self.last_html_body = html_body

        # 判斷是否為第一次加載
        # 如果是第一次，或是 browser 還沒內容，使用 setHtml
        # 如果已經有內容，使用 runJavaScript 局部更新 body
        if not hasattr(self, 'browser_initialized') or not self.browser_initialized:
            full_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                {self.css_style}
            </head>
            <body>
                {html_body}
            </body>
            </html>
            """
            base_url = QUrl.fromLocalFile(self.cache_dir + os.path.sep)
            self.browser.setHtml(full_html, base_url)
            self.ui.html_code_view.setPlainText(html_body)
        else:
            escaped_html = html_body.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
            js_code = f"document.getElementById('content').innerHTML = `{escaped_html}`;"
            self.browser.page().runJavaScript(js_code)

        self.ui.html_code_view.setPlainText(html_body)

        # 延遲一點點時間執行同步滾動 確保 Chromium 已經完成渲染
        QTimer.singleShot(20, self.sync_scroll)

    def sync_scroll(self):
        # 1. 取得編輯器的游標資訊
        cursor = self.ui.editor_input.textCursor()

        # 取得目前文件總行數與目前行號
        total_blocks = self.ui.editor_input.document().blockCount()
        current_block = cursor.blockNumber() + 1 # 從 1 開始計算

        if total_blocks <= 1:
            scroll_percentage = 0
        else:
            # 計算游標在全文件的百分比位置
            scroll_percentage = current_block / total_blocks

        # 2. 透過 JS 讓瀏覽器捲動
        # 我們讓瀏覽器的中央位置對準這個百分比，體感會更準確
        js_code = f"""
            var scrollHeight = document.documentElement.scrollHeight;
            var clientHeight = document.documentElement.clientHeight;
            var targetPos = (scrollHeight * {scroll_percentage}) - (clientHeight / 2);

            // 防止目標位置小於 0
            if (targetPos < 0) targetPos = 0;

            window.scrollTo({{
                top: targetPos,
                behavior: 'smooth'  // 改用 smooth 讓跟隨感更絲滑
            }});
        """
        if hasattr(self, 'browser'):
            self.browser.page().runJavaScript(js_code)

def main():
    # 禁用硬體加速，防止 svga 驅動噴錯
    # 1. 禁用 GPU 加速
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu --disable-software-rasterizer"

    # 2. 強制 Qt 使用軟體渲染器 (針對 Windows/Linux 繪圖後端)
    os.environ["QT_QUICK_BACKEND"] = "software"

    # 3. 針對某些驅動程式，禁用多執行緒組合器
    os.environ["QTWEBENGINE_DISABLE_GPU_THREAD"] = "1"

    app = QApplication(sys.argv)
    argv1 = sys.argv[1] if len(sys.argv) > 1 else "no argv" # 預留參數接口
    print('argv1:', argv1)

    window = MainWindow('key')
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()