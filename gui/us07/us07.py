if True:
    import sys
    import os
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
    from config import ISPC_MAINTAIN_VERSION
    from share_qt5 import * # 載入所有 qt5

    sys.path.append(os.path.join(ROOT_DIR, 'gui', 'us07'))
    from form_us07 import Ui_MainWindow
    from tool_pd_jogging import ProductCheck


class MainWindow(QMainWindow):

    def __init__(self, uid):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow();
        self.ui.setupUi(self) # 載入ui
        self.setWindowTitle(f'檢視')
        self.resize(962, 650)  # 設定視窗大小
        self.uid = uid
        self.tree = None # treeview 資料來源
        self._load_data()
        # print(self.tree)
        self._load_treeview()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        new_size = event.size()
        width = new_size.width()
        height = new_size.height()
        self.ui.treeView.setGeometry(0, 0, width, height)

    def _load_data(self):
        pc = ProductCheck(self.uid) # 檢查
        result = pc.get_detaile()
        if result['is_verify'] is True:
            result = pc.get_detaile()
            self.tree = result['fruit'] # dict
        else:
            self.tree = {}

    def _populate_json_tree(self, data: dict or list, parent_item: QStandardItem = None):
        # 遞迴地將巢狀 dict/list 轉換為 QStandardItem 結構。

        if parent_item is None:
            parent_item = QStandardItem() # 如果是頂層，創建一個虛擬根節點

        if isinstance(data, dict):
            # 處理字典 (物件)
            for key, value in data.items():

                # 判斷是否為容器類型 (需要遞迴)
                is_container = isinstance(value, (dict, list))

                # 建立新的項目作為當前節點 (key)
                item_text = f"{key}: <{type(value).__name__}>" if is_container else f"{key}: {repr(value)}"
                key_item = QStandardItem(item_text)
                key_item.setEditable(False)

                # 將新的項目添加到父節點
                parent_item.appendRow(key_item)

                # 如果是容器，則遞迴調用
                if is_container:
                    # 遞迴處理子結構
                    self._populate_json_tree(value, key_item)

        elif isinstance(data, list):
            # 處理列表 (陣列)

            # 檢查列表是否為單純的元素列表 (所有元素都不是容器)
            is_simple_list = all(not isinstance(item, (dict, list)) for item in data)

            if is_simple_list:
                # 遵循您的要求 4: 列表無子項目時
                # 建立一個單一項目來顯示整個列表內容
                item_text = f"[{len(data)} items]: {', '.join(map(repr, data))}"
                list_item = QStandardItem(item_text)
                list_item.setEditable(False)
                parent_item.appendRow(list_item)

            else:
                # 遵循您的要求 5: 列表有子項目的容器
                for index, value in enumerate(data):
                    is_sub_container = isinstance(value, (dict, list))

                    # 建立新的項目作為當前節點 (索引)
                    item_text = f"[{index}]: <{type(value).__name__}>" if is_sub_container else f"[{index}]: {repr(value)}"
                    index_item = QStandardItem(item_text)
                    index_item.setEditable(False)

                    parent_item.appendRow(index_item)

                    # 遞迴處理子結構
                    if is_sub_container:
                        self._populate_json_tree(value, index_item)

        return parent_item

    def _load_treeview(self):
        # 將 self.tree 載入至控制項 self.ui.treeView
        if not self.tree: # 數據為空，不做處理
            return

        # 1. 建立 QStandardItemModel
        model = QStandardItemModel(0, 1) # 由於我們只顯示 Key: Value 在單一欄位，所以列數為 1
        model.setHorizontalHeaderLabels(['Key: Value'])

        # 2. 遞迴填充模型
        # _populate_json_tree 返回的是一個虛擬的根節點
        root_item = self._populate_json_tree(self.tree)

        # 3. 將虛擬根節點的子項  加入到模型中
        # 這裡需要將根節點的每一個子節點 (即 JSON 的頂層 key) 逐一取出並加入到模型
        for i in range(root_item.rowCount()):
            item = root_item.takeRow(0)[0] # takeRow(index) 返回一個 list of items
            model.appendRow(item)

        # 4. 設置模型到 QTreeView
        self.ui.treeView.setModel(model)

        # 5. 初始設置 (讓使用者一開始能看到結構)
        self.ui.treeView.expandAll() # 展開所有節點
        self.ui.treeView.resizeColumnToContents(0) # 自動調整欄寬
        self.ui.treeView.setHeaderHidden(True) # 隱藏root

def main():
    app = QApplication(sys.argv)
    argv1 = sys.argv[1] if len(sys.argv) > 1 else "no argv" # 預留參數接口
    print('argv1:', argv1)
    window = MainWindow(argv1)
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()