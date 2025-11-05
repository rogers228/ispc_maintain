if True:
    import sys, os
    import json
    # import time

    from cerberus import Validator
    from deepmerge import Merger
    import copy

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
    from tool_parser import LineParser, BuildingWorker

class ProductCheck:
    # 檢查文件，使用者輸入的文件  並產出結果

    STORAGE_PATH = os.path.join(ROOT_DIR, 'tempstorage')
    def __init__(self, uid):
        self.uid = uid
        self.data_original = '' # 原始檔案內容 (整個py文字檔)
        self.specification = {} # 主要規格 dict
        self.friendly = {}      # 動態推格 dict 親切人類寫法輸入
        self.fruit = {}         # 最終合併後的結果 dict
        self.message = '' # 檢查訊息
        self.is_verify = None # 是否驗證通過

        self.bw = BuildingWorker() # 建構者
        self.merger = Merger([(list, ["append"]), (dict, ["merge"])],["override"], ["override"]) # 合併者的策略
        self._load_content()                # 動態讀取 python content

        if self.is_verify is True:
            self._add_specification_required()  # 添加 specification 必需的

        if self.is_verify is True:
            self._check_specification_root()    # 檢查 specification 根層

        if self.is_verify is True:
            self._check_specification_a()       # 檢查 specification 第a層 models

        if self.is_verify is True:
            self._transform_friendly()          # 重新構造 friendly

        if self.is_verify is True:
            self._check_friendly_alias()        # 檢查 friendly alias

        if self.is_verify is True: # 將 specification, friendly 合併為最終的結果 fruit
            self._merge_fruit()

    def _load_content(self): # 動態讀取 python content
        self.is_verify = False
        file_path = os.path.join(ProductCheck.STORAGE_PATH, f"{self.uid}.py")

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                self.data_original = file.read() # 讀取整個檔案內容
        except FileNotFoundError:
            self.message = f"錯誤: 找不到檔案 {file_path}"
            return # 檔案不存在，直接返回，使用預設空的 self.specification
        except Exception as e:
            self.message = f"錯誤: 讀取檔案 {file_path} 時發生未預期錯誤: {e}"
            return # 讀取失敗，直接返回

        local_vars = {}
        try:
            exec(self.data_original, {}, local_vars)
            # print(local_vars)
        except SyntaxError as e: # 專門處理語法錯誤，這是配置檔案最常見的錯誤
            self.message = f"❌ 語法錯誤: {e}"
            return

        except Exception as e: # 處理其他運行時錯誤 (例如 NameError, TypeError 等)
            self.message = f"❌ 運行時錯誤: {e}"
            return

        specification = local_vars.get('specification', None)
        friendly = local_vars.get('friendly', None)

        if isinstance(specification, dict):
            self.specification = specification
        elif specification is None:
            self.message = f"❌ 找不到 specification"
            return
        else:
            self.message = f"❌ specification 類型錯誤"
            return

        if isinstance(friendly, dict):
            self.friendly = friendly

        elif friendly is None:
            self.message = f"❌ 找不到 friendly"
            return
        else:
            self.message = f"❌ friendly 類型錯誤"
            return

        self.is_verify = True

    def _add_specification_required(self): # 添加 specification 必需的
        dic_default = { # 預設值
            'uid': self.uid,
            'option_item_count': len(self.specification.get('models_order', [])),
        }
        self.specification.update(dic_default)

    def _check_specification_root(self): # 檢查 specification 根層

        self.is_verify = False # 是否驗證通過
        schema = {
            'uid': {'type': 'string', 'required': True}, # required 必填
            'name': {'type': 'string', 'required': True},
            'name_en': {'type': 'string', 'required': True},
            'name_tw': {'type': 'string', 'required': True},
            'name_zh': {'type': 'string'},
            'supply_default_value': {'type': 'string', 'required': True, 'default': 's', 'allowed': ['s', 'n']},
            'models_order': {'type': 'list', 'required': True},
            'option_item_count': {'type': 'integer', 'required': True, 'min': 1}, # 非必要，會依照 models_order 更新
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

    def _check_specification_c(self, model, item): # 檢查 specification 第c層 item
        # print(f'_check_specification_c {model} model_items: {item}')

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

    def _check_specification_b(self, model): # 檢查 specification 第b層 model
        # print(f'_check_specification_b: {model}')

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
            'postfix_symbol': {'type': 'string', 'required': True, 'allowed': ['', '-','/','\\']},
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
            self._check_specification_c(model, item) # 檢查 specification 第c層 item

    def _check_specification_a(self): # 檢查 specification 第a層 models
        # print(f'_check_specification_a')

        # 第 a 層 models
        schema_models = {}
        # for m in self.specification['models_order'][:3]: # 開發中 應刪除
        for m in self.specification['models_order']:
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
            self._check_specification_b(model) # 檢查 specification 第b層 model

    def _transform_friendly(self): # 重新構造 friendly

        alias = LineParser(lines = self.friendly['alias'],
            columns = ['model', 'item', 'alias'],
            text_fields=['item', 'alias']) # 轉換為 records格式的 dict

        # print(alias.to_dict())
        # print(json.dumps(alias.to_dict(), indent=4, ensure_ascii=False))

        friendly_structured = {
            'alias': alias.to_dict(),
            }

        self.friendly.update(friendly_structured)

    def _check_friendly_alias(self): # 檢查 friendly alias

        for target in self.friendly['alias']: # target = dict
            # print(target)
            if target['model'] not in self.specification['models']:
                self.is_verify = False
                self.message = f"❌ alias 檢查失敗： model: {target['model']} keyerror!"
                return
            if target['item'] not in self.specification['models'][target['model']]['model_items_order']:
                self.is_verify = False
                self.message = f"❌ alias 檢查失敗： model: {target['item']} keyerror!"
                return

            schema_alias = {
                'model': {'type': 'string', 'required': True,
                    'allowed': self.specification['models_order']},
                'item': {'type': 'string', 'required': True,
                    'allowed': self.specification['models'][target['model']]['model_items_order']},
                'alias': {'type': 'string', 'required': True},
            }
            # print(schema_alias)

            vr = Validator(schema_alias)
            if not vr.validate(target):
                # print(f"❌ alias 檢查失敗： {vr.errors}, model: {target['model']}, item: {target['item']}, alias: {target['alias']}")
                self.is_verify = False
                self.message = f"❌ alias 檢查失敗： {vr.errors}, model: {target['model']}, item: {target['item']}, alias: {target['alias']}"
                return
            else:
                # print("alias 檢查通過")
                self.is_verify = True
                self.message = ''

    def _dict_to_json(self, data):
        # 將 data(dict) 轉換為 json
        try:
            data_json = json.dumps(data, indent=4, ensure_ascii=False)
        except TypeError as e:
            # 捕捉 json.dumps 字典中包含不可 JSON 序列化的類型
            print(f"❌ 配置內容 JSON 序列化失敗 (TypeError): 配置包含無法轉換的 Python 類型。詳情: {e}")
            return None
        except Exception as e:
            print(f"❌ 執行檔案時發生錯誤: {e}")
            return None

        return data_json

    def _merge_fruit(self):
        # 將 specification, friendly 合併為最終的結果 fruit
        fruit = copy.deepcopy(self.specification)

        records_alias = self.friendly.get('alias', [])
        if records_alias:
            dic_alias = self.bw.build_alias(records_alias) # record 建構為 dict
            # print(json.dumps(dic_alias, indent=4, ensure_ascii=False))
            self.merger.merge(fruit, dic_alias) # 合併

        self.fruit = fruit

    def get_detaile(self):
        # 將 fruit 轉換為 json
        json_result = self._dict_to_json(self.fruit)
        data_json = json_result if json_result is not None else ""

        return {
            'data_original': self.data_original, # 原始檔案內容 (整個py文字檔) string
            'specification': self.specification, # 規格      使用者輸入     dict
            'friendly':      self.friendly,      # 其他規格  友善使用者輸入  dict
            'fruit':         self.fruit,         # 最終結果  輸出           dict
            'data_json':     data_json,          # 最終結果  輸出   json string
            'message':       self.message,       # 錯誤訊息         string
            'is_verify':     self.is_verify,     # 檢查輸入是否合法  boolean
        }

def test1():
    uid = 'dbdcedbe-7bde-4b2c-8cfb-b21e8ccde68d'
    pc = ProductCheck(uid)
    result = pc.get_detaile()
    # print(result)
    if result['is_verify'] is True:
        print('驗證成功')
        # print(result['data_original'])
        # print(json.dumps(result['specification'], indent=4, ensure_ascii=False))
        # print(json.dumps(result['friendly'], indent=4, ensure_ascii=False))
        # print(result['fruit'])
        print(result['data_json'])

    else:
        print(result['message'])


if __name__ == '__main__':
    test1()