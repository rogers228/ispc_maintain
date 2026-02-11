# us07.py
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
        self.list_expand_keys = ['fast_model'] # 展開 list的欄位
        self._load_data()
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

    def _populate_json_tree(self,
                            data: dict or List,
                            parent_item: QStandardItem = None,
                            current_key = None): # 【修改點 1】新增 current_key 參數
        """
        遞迴地將巢狀 dict/list 轉換為 QStandardItem 結構。

        :param data: 當前的 dict 或 list 數據
        :param parent_item: 父級 QStandardItem
        :param current_key: 當前節點的 key 名稱 (用於判斷是否展開列表)
        """

        if parent_item is None:
            parent_item = QStandardItem() # 如果是頂層，創建一個虛擬根節點

        if isinstance(data, dict):
            # 處理字典 (物件)
            for key, value in data.items():

                is_container = isinstance(value, (dict, list))

                # 建立新的項目作為當前節點 (key)
                item_text = f"{key}: <{type(value).__name__}>" if is_container else f"{key}: {repr(value)}"
                key_item = QStandardItem(item_text)
                key_item.setEditable(False)

                parent_item.appendRow(key_item)

                if is_container:
                    self._populate_json_tree(value, key_item, current_key=key)

        elif isinstance(data, list):
            # 處理列表 (陣列)

            # 1. 判斷是否為單純的元素列表 (所有元素都不是容器)
            is_simple_list = all(not isinstance(item, (dict, list)) for item in data)

            # 2. 判斷是否需要強制展開 (即使是簡單列表，如果 key 在列表中也展開)
            should_expand = current_key in self.list_expand_keys

            # 【修改點 3】調整列表的顯示邏輯
            # 條件：如果不是容器列表 AND 不需要強制展開
            if is_simple_list and not should_expand:
                # 採用單一項目顯示整個列表內容 (預設行為)

                # 確保列表有內容，空列表則顯示 []
                if data:
                    item_text = f"[{len(data)} items]: {', '.join(map(repr, data))}"
                else:
                    item_text = "[] (Empty List)"

                list_item = QStandardItem(item_text)
                list_item.setEditable(False)
                parent_item.appendRow(list_item)

            else:
                # 容器列表 或 簡單列表但需要展開 (樹狀結構)

                for index, value in enumerate(data):
                    is_sub_container = isinstance(value, (dict, list))

                    # 建立新的項目作為當前節點 (索引)
                    # 只有在非容器時才顯示值
                    if is_sub_container:
                        item_text = f"[{index}]: <{type(value).__name__}>"
                    else:
                        item_text = f"[{index}]: {repr(value)}"

                    index_item = QStandardItem(item_text)
                    index_item.setEditable(False)

                    parent_item.appendRow(index_item)

                    # 遞迴處理子結構
                    if is_sub_container:
                        # 容器遞迴時，不傳遞 item 的索引作為 key
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