if True:
    import sys, os
    import json
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
        self._check_first() # 檢查 首層
        self._check_models_a() # 檢查 models

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

    def _check_first(self): # 檢查第一層

        self.is_verify = False # 是否驗證通過
        schema = {
            'uid': {'type': 'string', 'required': True}, # required 必填
            'name': {'type': 'string', 'required': True},
            'name_en': {'type': 'string', 'required': True},
            'name_tw': {'type': 'string', 'required': True},
            'name_zh': {'type': 'string'},
            'supply_default_value': {'type': 'string', 'required': True, 'default': 's', 'allowed': ['s', 'n']},
            'models_order': {'type': 'list', 'required': True},
            'option_item_count': {'type': 'integer', 'required': True, 'min': 1},
            'main_model': {'type': 'string', 'required': True, 'allowed': self.specification['models_order']},
            'select_way': {'type': 'integer', 'required': True, 'allowed': [1, 2]},
            'models': {'type': 'dict', 'required': True},
        }

        vr = Validator(schema)
        target = self.specification
        if not vr.validate(target):
            print(f"❌ 第一層檢查失敗： {vr.errors}")
            self.is_verify = False
            self.message = f"❌ 第一層檢查失敗： {vr.errors}"
        else:
            # print("首層 檢查通過")
            self.is_verify = True
            self.message = ''

    def _check_item_c(self, model, item): # 檢查 第 c 層 item
        # print(f'_check_item_c {model} model_items: {item}')

        schema_c = { # 第 c 層  item 底下
            'item_name_en': {'type': 'string', 'required': True},
            'item_name_tw': {'type': 'string', 'required': True},
            'item_name_zh': {'type': 'string', 'required': True},
            'supply': {'type': 'string', 'required': True, 'allowed': ['', 's', 'n']}, # 供貨狀態
        }
        vr = Validator(schema_c)
        target = self.specification['models'][model]['model_items'][item]
        # print(target)
        if not vr.validate(target):
            print(f"❌ model: {model} item: {item} 檢查失敗： {vr.errors}")
            self.is_verify = False
            self.message = f"❌ model: {model} 檢查失敗： {vr.errors}"
            return
        else:
            # print("models 檢查通過")
            self.is_verify = True
            self.message = ''

    def _check_model_b(self, model): # 檢查 第 b 層 model
        # print(f'_check_model_b: {model}')

        lis_mo = list(self.specification['models'][model]['model_items'].keys())
        # print(lis_mo)

        model_item_length = self.specification['models'][model]['model_item_length'] # model字元數
        # print('model_item_length:', model_item_length)

        schema_items = {}
        for item in self.specification['models'][model]['model_items_order']:
            schema_items.setdefault(item, {'type': 'dict', 'required': True})
        # print(json.dumps(schema_items, indent=4, ensure_ascii=False))

        schema_b = { # 第 b 層  model 底下
            'name_en': {'type': 'string', 'required': True},
            'name_tw': {'type': 'string', 'required': True},
            'name_zh': {'type': 'string', 'required': True},
            'postfix_symbol': {'type': 'string', 'required': True, 'allowed': ['', '-']},
            'default_value': {'type': 'string', 'required': True},
            'model_item_length': {'type': 'integer', 'required': True},
            'model_items': {'type': 'dict', 'required': True, 'schema': schema_items, 'keysrules': { # keys規則
                'type': 'string', 'minlength': model_item_length, 'maxlength': model_item_length
                }
            },
            'model_items_order': {'type': 'list', 'required': True, 'schema':{
                    'type': 'string', 'allowed': lis_mo,
                }
            }
        }

        # print(json.dumps(schema_b, indent=4, ensure_ascii=False))

        vr = Validator(schema_b)
        target = self.specification['models'][model]
        if not vr.validate(target):
            print(f"❌ model: {model} b層檢查失敗： {vr.errors}")
            self.is_verify = False
            self.message = f"❌ model: {model} b層檢查失敗： {vr.errors}"
            return
        else:
            # print("models 檢查通過")
            self.is_verify = True
            self.message = ''

        # 尚未完成
        for item in self.specification['models'][model]['model_items']:
            # print(f'check {model} model_items: {item}')
            if self.is_verify is False:
                break
            self._check_item_c(model, item) # 檢查 第 c 層 item

    def _check_models_a(self): # 檢查 第 a 層 models
        # print(f'_check_models_a')

        # 第 a 層 models
        schema_models = {}
        for m in self.specification['models_order'][:3]: # 開發中 應刪除
        # for m in self.specification['models_order']:
            schema_models.setdefault(m, {'type': 'dict', 'required': True})
        # print(json.dumps(schema_models, indent=4, ensure_ascii=False))
        vr = Validator(schema_models)
        target = self.specification['models']
        if not vr.validate(target):
            print(f"❌ models a層檢查失敗： {vr.errors}")
            self.is_verify = False
            self.message = f"❌ models a層檢查失敗： {vr.errors}"
            return
        else:
            # print("models 檢查通過")
            self.is_verify = True
            self.message = ''

        for model in self.specification['models']:
            if self.is_verify is False:
                break
            self._check_model_b(model) # 檢查 第 b 層 model

    def get_detaile(self):
        return {
            'specification': self.specification,
            'message': self.message,
            'is_verify': self.is_verify,
        }


def test1():
    uid = 'dbdcedbe-7bde-4b2c-8cfb-b21e8ccde68d'
    pc = ProductCheck(uid)
    result = pc.get_detaile()
    # print(result)
    if result['is_verify'] is True:
        print('驗證成功')
    else:
        print(result['message'])


if __name__ == '__main__':
    test1()