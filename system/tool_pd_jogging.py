if True:
    import sys, os
    # import json
    # import time

    from cerberus import Validator
    # from deepmerge import Merger
    # import copy

    def find_project_root(start_path=None, project_name="ispc_maintain"):
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

    ROOT_DIR = find_project_root()
    sys.path.append(os.path.join(ROOT_DIR, "system"))

class ProductCheck:
    STORAGE_PATH = os.path.join(ROOT_DIR, 'tempstorage')

    def __init__(self, uid):
        self.uid = uid
        self.specification = {} # 預設值
        self.message = '' # 檢查訊息
        self.is_verify = None # 是否驗證通過

        self._load_specification() # 動態讀取 specification
        self._check() # 檢查

    def _load_specification(self): # 動態讀取 specification
        file_path = os.path.join(ProductCheck.STORAGE_PATH, f"{self.uid}.py")
        data_original = None
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data_original = file.read() # 讀取整個檔案內容
        except FileNotFoundError:
            self.message = f"錯誤: 找不到檔案 {file_path}"
            return # 檔案不存在，直接返回，使用預設空的 self.specification
        except Exception as e:
            self.message = f"錯誤: 讀取檔案 {file_path} 時發生未預期錯誤: {e}"
            return # 讀取失敗，直接返回

        local_vars = {}
        try:
            exec(data_original, {}, local_vars)

        except SyntaxError as e: # 專門處理語法錯誤，這是配置檔案最常見的錯誤
            self.message = f"❌ 語法錯誤: {e}"
            return

        except Exception as e: # 處理其他運行時錯誤 (例如 NameError, TypeError 等)
            self.message = f"❌ 運行時錯誤: {e}"
            return

        specification = local_vars.get('specification', {})
        if isinstance(specification, dict):
            dic_default = { # 預設值
                'uid': self.uid,
            }
            specification.update(dic_default)
            self.specification = specification

        elif specification is None:
            self.message = f"警告: 執行結果中找不到 'specification' 變數 (UID: {uid})。"
            return
        else:
            self.message = f"錯誤: 'specification' 變數類型錯誤 (UID: {uid})。預期 dict，實際為 {type(specification).__name__}。"
            return

    def _check(self): # 檢查
        self.is_verify = False # 是否驗證通過

        lis_models = self.specification['models_order'] # 所有選型

        schema_models = {}
        for model in lis_models[:1]:

            schema_a = {
                'name_en': {'type': 'string', 'required': True},
                'name_tw': {'type': 'string', 'required': True},
                'name_zh': {'type': 'string', 'required': True},
                'postfix_symbol': {'type': 'string', 'required': True, 'allowed': ['', '-']},
            }
            schema_models.setdefault(model, {'type': 'dict', 'required': True, 'schema': schema_a})
        # print(schema_models)
        schema = {
            'uid': {'type': 'string', 'required': True}, # required 必填
            'name': {'type': 'string', 'required': True},
            'name_en': {'type': 'string', 'required': True},
            'name_tw': {'type': 'string', 'required': True},
            'name_zh': {'type': 'string'},
            'supply_default_value': {'type': 'string', 'required': True, 'default': 's', 'allowed': ['s', 'n']},
            'models_order': {'type': 'list', 'required': True,
                'schema': {'type': 'string'}
            },
            'option_item_count': {'type': 'integer', 'required': True, 'min': 1},
            'main_model': {'type': 'string', 'required': True, 'allowed': lis_models},
            'select_way': {'type': 'integer', 'required': True, 'allowed': [1, 2]},
            'models': {'type': 'dict', 'required': True, 'schema': schema_models},
        }

        vr = Validator(schema)
        if not vr.validate(self.specification):
            print("檢查失敗：", vr.errors)
            self.is_verify = False
            self.message = vr.errors
        else:
            print("檢查通過")
            self.is_verify = True
            self.message = ''

    def get_detaile(self):
        return {
            'specification': self.specification,
            'message': self.message,
            'is_verify': self.is_verify,
        }


def test1():
    uid = 'dbdcedbe-7bde-4b2c-8cfb-b21e8ccde68d'
    pc = ProductCheck(uid)
    spec = pc.get_detaile()
    if not spec:
        print(message)
    else:
        print(spec)

if __name__ == '__main__':
    test1()