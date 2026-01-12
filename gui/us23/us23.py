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
        # 遍歷 Markdown 轉換後的所有 <img> 標籤
        for img in root.iter("img"):
            src = img.get("src")
            if src and src.startswith("images/"):
                # 取得本地快取路徑 (這部分沿用您原本的 MD5 邏輯)
                local_path = get_local_cache_path(src)

                if os.path.exists(local_path):
                    # 1. 轉換路徑為 file:/// 格式供 QTextBrowser 讀取
                    img.set("src", "file:///" + local_path.replace("\\", "/"))

                    # 2. 🚀 核心邏輯：偵測寬度
                    image_info = QImage(local_path)
                    if not image_info.isNull():
                        # 如果圖片寬度大於 800 像素
                        if image_info.width() > 800:
                            # 強制在 HTML 標籤寫入 width="100%"
                            img.set("width", "100%")
                            img.set("style", "clear: both; display: block; margin: 10px 0;")
                        else:
                            # 小圖則保持原樣，或者可以設定為固定寬度
                            # img.set("width", str(image_info.width()))
                            pass


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

        # 1. 預先初始化 Markdown 引擎 (關鍵：解決第一個字卡頓)
        self.md_engine = markdown.Markdown(extensions=[
            'fenced_code',
            'tables',
            'nl2br',
            LocalImageExtension() # 確保這個 Extension 類別有被加入
        ])
        # 2. 設置防抖動計時器 (Debounce)
        self.render_timer = QTimer()
        self.render_timer.setSingleShot(True)
        self.render_timer.timeout.connect(self.update_render)

        try:
            with open(os.path.join(ROOT_DIR, 'gui', 'us23', 'style.css'), 'r', encoding='utf-8') as f:
                self.css_style = f"<style>{f.read()}</style>"
        except FileNotFoundError:
            self.css_style = ""

        # 4. 根據傳入的 key 設定預設 Markdown 內容
        self.load_default_content(key)

        # 5. 綁定事件 (改為觸發計時器，不直接渲染)
        self.ui.editor_input.textChanged.connect(lambda: self.render_timer.start(200))

        # 6. 初始啟動：手動執行一次渲染，讓開啟時就有畫面
        self.update_render()

    def resizeEvent(self, event):
        """絕對座標精確計算"""
        # 取得主視窗中央區域大小
        rect = self.centralWidget().contentsRect()
        window_w = rect.width()
        window_h = rect.height()

        margin = 10
        spacing = 10
        half_width = (window_w - (margin * 2) - spacing) // 2

        # A. 左側編輯框佈局
        self.ui.editor_input.move(margin, margin)
        self.ui.editor_input.resize(half_width, window_h - (margin * 2))

        # B. 右側 TabWidget 佈局
        self.ui.tab_widget.move(margin + half_width + spacing, margin)
        self.ui.tab_widget.resize(half_width, window_h - (margin * 2))

        # C. Tab 內部控制項佈局 (填滿 Page)
        # 由於使用絕對座標，需確保分頁內的 Widget 也能跟著縮放
        page_rect = self.ui.tab_widget.currentWidget().rect()
        pw = page_rect.width()
        ph = page_rect.height()

        self.ui.preview_window.move(0, 0)
        self.ui.preview_window.resize(pw, ph)

        self.ui.html_code_view.move(0, 0)
        self.ui.html_code_view.resize(pw, ph)

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

    # def update_render(self):
    #     # 1. 獲取 Markdown 原始文字
    #     raw_text = self.ui.editor_input.toPlainText()

    #     # 使用預建實例進行轉換
    #     self.md_engine.reset()
    #     html_body = self.md_engine.convert(raw_text)

    #     # 組合預覽用 HTML (含 CSS)
    #     full_html = f"<html><head>{self.css_style}</head><body>{html_body}</body></html>"
    #     print(full_html)
    #     # 更新 UI (阻斷訊號防止游標定位錯誤)
    #     self.ui.preview_window.blockSignals(True)
    #     self.ui.html_code_view.blockSignals(True)

    #     self.ui.preview_window.setHtml(full_html)
    #     self.ui.html_code_view.setPlainText(html_body) # HTML 分頁不顯示 CSS

    #     self.ui.preview_window.blockSignals(False)
    #     self.ui.html_code_view.blockSignals(False)

    def update_render(self):
        raw_text = self.ui.editor_input.toPlainText()

        # 重置引擎狀態
        self.md_engine.reset()

        # 執行轉換 (此時 LocalImageTreeprocessor 會介入並加上 width="100%")
        html_body = self.md_engine.convert(raw_text)

        # 組合最終 HTML
        full_html = f"""
        <html>
        <head>
            {self.css_style}
            <style>
                /* 雖然有了 HTML 屬性，但 CSS 的 height: auto 仍有助於保持比例 */
                img {{ height: auto !important; }}
            </style>
        </head>
        <body>
            {html_body}
        </body>
        </html>
        """

        self.ui.preview_window.setHtml(full_html)
        self.ui.html_code_view.setPlainText(html_body) # HTML 分頁不顯示 CSS

def main():
    app = QApplication(sys.argv)
    argv1 = sys.argv[1] if len(sys.argv) > 1 else "no argv" # 預留參數接口
    print('argv1:', argv1)

    window = MainWindow('key')
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()