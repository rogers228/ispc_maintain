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
    from tool_auth import AuthManager

    sys.path.append(os.path.join(ROOT_DIR, 'gui', 'us09'))
    from form_us09 import Ui_MainWindow

class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow();
        self.ui.setupUi(self) # 載入ui
        self.setWindowTitle('設定')
        self.resize(800, 230)  # 設定視窗大小

        self.auth = AuthManager()
        self.user_data = self.auth.load_local_data() # 載入本地設定，如果有就帶入初始值
        self.populate_fields()

        self.ui.save.clicked.connect(self.handle_save) # 連接 Login 按鈕
        self.ui.browse_editor.clicked.connect(self.handle_browse_editor)

    def populate_fields(self):
        """將本地資料帶入欄位"""
        self.ui.editor.setText(self.user_data.get("editor", ""))

    def handle_browse_editor(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "選擇編輯器",
            "", # 預設開啟路徑，可設為上次儲存的位置或常用路徑
            "執行檔 (*.exe);;所有檔案 (*)" # 篩選器
        )

        if file_path:
            self.ui.editor.setText(file_path)

    def handle_save(self):
        self.ui.save.setEnabled(False)

        editor = self.ui.editor.text().strip()

        if not editor:
            QMessageBox.warning(self, "輸入錯誤", "編輯器 不可為空白。")
            self.ui.save.setEnabled(True)
            return

        # 儲存
        self.auth.save_local_data({
            "editor": editor,
        })
        self.close()  # 關閉視窗

def main():
    app = QApplication(sys.argv)
    # argv1 = sys.argv[1] if len(sys.argv) > 1 else "no argv" # 預留參數接口
    # print('argv1:', argv1)

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()