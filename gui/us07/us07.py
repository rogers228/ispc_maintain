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
    from config import ISPC_MAINTAIN_VERSION
    from share_qt5 import *

    sys.path.append(os.path.join(ROOT_DIR, 'gui', 'us07'))
    from form_us07 import Ui_MainWindow

    from tool_pd_jogging import ProductCheck

class MainWindow(QMainWindow):

    def __init__(self, uid):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow();
        self.ui.setupUi(self) # 載入ui
        self.setWindowTitle(f'預覽')
        self.resize(712, 460)  # 設定視窗大小
        self.uid = uid
        self.tree = None # treeview 資料來源
        self._load_data()
        print(self.tree)

    def _load_data(self):
        pc = ProductCheck(self.uid) # 檢查
        result = pc.get_detaile()
        if result['is_verify'] is True:
            result = pc.get_detaile()
            self.tree = result['fruit'] # dict
        else:
            self.tree = {}

def main():
    app = QApplication(sys.argv)
    argv1 = sys.argv[1] if len(sys.argv) > 1 else "no argv" # 預留參數接口
    print('argv1:', argv1)
    window = MainWindow(argv1)
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()