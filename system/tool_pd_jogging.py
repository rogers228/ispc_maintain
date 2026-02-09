if True:
    import sys, os
    import json
    # import time

    from cerberus import Validator
    from deepmerge import Merger
    import copy
    import re

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
    from tool_auth import AuthManager
    from tool_options import Options
    from tool_parser import LineParser, BuildingWorker
    from tool_list import is_all_include, other_itmes

class ProductCheck:
    # 檢查文件，使用者輸入的文件  並產出結果
    STORAGE_PATH = os.path.join(ROOT_DIR, 'tempstorage')
    SUPPLY_ALLOWED_LIST = ['s', 'n', 'd'] # 供貨方式 s正常供貨, n不供貨, d特殊供貨
    HUMAN_EXPRESSION_LIST = ['-s', '-u'] # 人類表達方式以  -s向方式表達 與 -u反向方式表達
    POSTFIX_SPMBOL_LIST = ['', '-','/','\\'] # 後置符號 \\ 即 \

    def __init__(self, uid):
        self.uid = uid
        self.data_original = '' # 原始檔案內容 (整個py文字檔)
        self.specification = {} # 主要規格 dict
        self.friendly = {}      # 動態推格 dict 親切人類寫法輸入
        self.fruit = {}         # 最終合併後的結果 dict
        self.message = '' # 檢查訊息
        self.is_verify = None # 是否驗證通過

        self.auth = AuthManager()
        data = self.auth.load_local_data()
        self.email = data.get("email", "") # 使用者 email
        # print(self.email)
        self.opt = Options()
        self.options = self.opt.get_options_auto()
        # print(self.options)
        self.pdno = self._find_pdno_by_uid(self.options['permissions'][self.email], self.uid)
        # print(self.pdno)

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
            self._check_friendly()              # 檢查 friendly

        if self.is_verify is True:
            self._insert_opposite()             # 添加對向規則

        if self.is_verify is True: # 將 specification, friendly 合併為最終的結果 fruit
            self._merge_fruit()

    def _find_pdno_by_uid(self, permissions_user, target_uid):
        # permissions_user 是 self.option[permissions][email]
        for item in permissions_user:
            # 每個 item 是一個只有一個 key 的 dict，例如 {"ys_v_dev": {...}}
            for _, info in item.items():
                # info 就是內層 dict
                if info.get("uid") == target_uid:
                    return info.get("pdno")
        return None

    def _toggle_human(self, flag):
        # 切換 -s | -u
        mapping = {
            '-s': '-u',
            '-u': '-s'
        }
        return mapping.get(flag, None)

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
            'pdno': self.pdno,
            'option_item_count': len(self.specification.get('models_order', [])),
        }
        self.specification.update(dic_default)

    def _check_unique_list(self, field, value, error): # 自訂檢查 list 項目不可重複
        lis = value
        if len(lis) != len(set(lis)):
            error(field, '列表中的項目不可重複')

    def _check_pattern(self, field, value, error): # 自訂檢查 正則表達式 是否合法
        try:
            pattern = value
            re.compile(pattern)  # 嘗試編譯正則表達式
        except re.error as e:
            error(field, f"正則表達式錯誤")

    def _check_specification_root(self): # 檢查 specification 根層

        self.is_verify = False # 是否驗證通過
        schema = {
            'uid': {'type': 'string', 'required': True}, # required 必填
            'pdno': {'type': 'string', 'required': True}, # 自動
            'name': {'type': 'string', 'required': True},
            'name_en': {'type': 'string', 'required': True},
            'name_tw': {'type': 'string', 'required': True},
            'name_zh': {'type': 'string'},
            'supply_default_value': {'type': 'string', 'required': True, 'default': 's', 'allowed': ProductCheck.SUPPLY_ALLOWED_LIST},
            'models_order': {'type': 'list', 'required': True, 'check_with': self._check_unique_list},
            'option_item_count': {'type': 'integer', 'required': True, 'min': 1}, # 非必要，會依照 models_order 更新
            'main_model': {'type': 'string', 'required': True, 'allowed': self.specification['models_order']},
            'select_way': {'type': 'integer', 'required': True, 'allowed': [1, 2]},
            'models': {'type': 'dict', 'required': True},
            'description': {'type': 'string', 'required': True, 'maxlength': 500},
            'introduction_id': {'type': 'string', 'required': True},
            'photo_album': {'type': 'list', 'required': True, 'schema': {'type': 'string'}},
            'og_image': {'type': 'string', 'required': True},
            'keywords': {'type': 'list', 'required': True, 'schema': {'type': 'string'}},
        }

        vr = Validator(schema)
        target = self.specification
        if not vr.validate(target):
            # print(f"❌ 第一層檢查失敗： {vr.errors}")
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
            'supply': {'type': 'string', 'required': True, 'allowed': ProductCheck.SUPPLY_ALLOWED_LIST}, # 供貨狀態
        }
        vr = Validator(schema_c)
        target = self.specification['models'][model]['model_items'][item]
        # print(target)
        if not vr.validate(target):
            # print(f"❌ model: {model} item: {item} c層檢查失敗： {vr.errors}")
            self.is_verify = False
            self.message = f"❌ model: {model} c層檢查失敗： {vr.errors}"
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
            'postfix_symbol': {'type': 'string', 'required': True, 'allowed': ProductCheck.POSTFIX_SPMBOL_LIST},
            'default_value': {'type': 'string', 'required': True},
            'model_item_length': {'type': 'integer', 'required': True},
            'model_items': {'type': 'dict', 'required': True, 'schema': schema_items, 'keysrules': { # keys規則
                'type': 'string', 'minlength': model_item_length, 'maxlength': model_item_length
                }
            },
            'model_items_order': {'type': 'list', 'required': True, 'check_with': self._check_unique_list, 'schema':{
                    'type': 'string', 'allowed': lis_mo,
                }
            }
        }

        # print(json.dumps(schema_b, indent=4, ensure_ascii=False))

        vr = Validator(schema_b)
        target = self.specification['models'][model]
        if not vr.validate(target):
            # print(f"❌ model: {model} b層檢查失敗： {vr.errors}")
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
        # 僅能解析後，以使用者資料重新構造     若欲新增資料應在檢查後才能進行，否則會有錯誤
        # 多行文字轉換為 records [{}...]
        # records = rd

        if True: # alias
            rd_alias = LineParser(lines = self.friendly['alias'],
                columns = ['model', 'item', 'alias'],
                text_fields=['item', 'alias'])

            result = rd_alias.parse_info() # 解析結果
            if result['is_error'] is True: # 解析錯誤
                self.is_verify = False
                self.message = f"❌ friendly['alias'] 解析失敗：{result['message']}"
                return

            new_records_alias = rd_alias.to_dict()
            # print(json.dumps(new_records_alias, indent=4, ensure_ascii=False))

        if True: # runtime_supply
            rd_runtime_supply = LineParser(lines = self.friendly['runtime_supply'],
                columns = ['pattern', 'model', 'items', 'supply'],
                text_fields=['pattern', 'model', 'items', 'supply'])

            result = rd_runtime_supply.parse_info() # 解析結果
            if result['is_error'] is True: # 解析錯誤
                self.is_verify = False
                self.message = f"❌ friendly['runtime_supply'] 解析失敗：{result['message']}"
                return

            new_records_runtime_supply = rd_runtime_supply.to_dict()
            # print(json.dumps(new_records_runtime_supply, indent=4, ensure_ascii=False))

        if True: # runtime_filter
            rd_runtime_filter = LineParser(lines = self.friendly['runtime_filter'],
                columns = ['pattern', 'model', 'items', 'method'],
                text_fields=['pattern', 'model', 'items', 'method'])

            result = rd_runtime_filter.parse_info() # 解析結果
            if result['is_error'] is True: # 解析錯誤
                self.is_verify = False
                self.message = f"❌ friendly['runtime_filter'] 解析失敗：{result['message']}"
                return

            new_records_runtime_filter = rd_runtime_filter.to_dict()
            # print(json.dumps(new_records_runtime_filter, indent=4, ensure_ascii=False))

        if True: # runtime_disable
            rd_runtime_disable = LineParser(lines = self.friendly['runtime_disable'],
                columns = ['pattern', 'model', 'items', 'method'],
                text_fields=['pattern', 'model', 'items', 'method'])

            result = rd_runtime_disable.parse_info() # 解析結果
            if result['is_error'] is True: # 解析錯誤
                self.is_verify = False
                self.message = f"❌ friendly['runtime_disable'] 解析失敗：{result['message']}"
                return

            new_records_runtime_disable = rd_runtime_disable.to_dict()
            # print(json.dumps(new_records_runtime_disable, indent=4, ensure_ascii=False))

        if True: # fast_model
            lis_index = lambda count: [f'index_{i}' for i in range(count)] # 建立 lis_index 函數 回傳 ['index_0', 'index_1'...]
            columns = lis_index(len(self.specification['models_order']))
            rd_fast_model = LineParser(lines = self.friendly['fast_model'],
                columns = columns,
                text_fields = columns)

            result = rd_fast_model.parse_info() # 解析結果
            if result['is_error'] is True: # 解析錯誤
                self.is_verify = False
                self.message = f"❌ friendly['fast_model'] 解析失敗：{result['message']}"
                return

            new_records_fast_model = rd_fast_model.to_dict()
            # print(json.dumps(new_records_fast_model, indent=4, ensure_ascii=False))

        friendly_structured = { # 重新構造
            'alias':           new_records_alias,
            'runtime_supply':  new_records_runtime_supply,
            'runtime_filter':  new_records_runtime_filter,
            'runtime_disable': new_records_runtime_disable,
            'fast_model':      new_records_fast_model,
            }

        self.friendly.update(friendly_structured) # 更新

    def _check_friendly(self): # 檢查 friendly
        if True: # check alias
            for target in self.friendly['alias']: # target = dict
                # print(target)
                # 提前檢查 target['model'] keyerror 避免 schema_alias 錯誤
                if target['model'] not in self.specification['models']:
                    self.is_verify = False
                    self.message = f"❌ alias 檢查失敗： model: {target['model']} keyerror!"
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

        if True: # check runtime_supply
            # print('check runtime_supply')
            for target in self.friendly['runtime_supply']: # target = dict
                # print(target)
                # 提前檢查 target['model'] keyerror 避免 schema_alias 錯誤
                if target['model'] not in self.specification['models']:
                    self.is_verify = False
                    self.message = f"❌ runtime_supply 檢查失敗： model: {target['model']} keyerror!"
                    return

                schema_alias = {
                    'pattern': {'type': 'string', 'required': True, 'check_with': self._check_pattern },
                    'model': {'type': 'string', 'required': True, 'allowed': self.specification['models']},
                    'items': {'type': 'list', 'required': True, 'check_with': self._check_unique_list, 'schema': { # 巢狀內容的規則
                        'type': 'string',
                        'allowed': self.specification['models'][target['model']]['model_items_order']
                        }
                     },
                    'supply': {'type': 'string', 'required': True, 'allowed': ProductCheck.SUPPLY_ALLOWED_LIST},
                }
                vr = Validator(schema_alias)
                if not vr.validate(target):
                    # print(f"❌ runtime_supply 檢查失敗： {vr.errors},  model: {target['model']} pattern: {target['pattern']}")
                    self.is_verify = False
                    self.message = f"❌ runtime_supply 檢查失敗： {vr.errors}, {target['pattern']}  {target['model']}  {','.join(target['items'])}"
                    return
                else:
                    # print("alias 檢查通過")
                    self.is_verify = True
                    self.message = ''

        if True: # check runtime_filter
            # print('check runtime_filter')
            for target in self.friendly['runtime_filter']: # target = dict
                # print(target)
                # 提前檢查 target['model'] keyerror 避免 schema_alias 錯誤
                if target['model'] not in self.specification['models']:
                    self.is_verify = False
                    self.message = f"❌ runtime_filter 檢查失敗： model: {target['model']} keyerror!"
                    return

                schema_filter = {
                    'pattern': {'type': 'string', 'required': True, 'check_with': self._check_pattern },
                    'model': {'type': 'string', 'required': True, 'allowed': self.specification['models']},
                    'items': {'type': 'list', 'required': True, 'check_with': self._check_unique_list, 'schema': { # 巢狀內容的規則
                        'type': 'string',
                        'allowed': self.specification['models'][target['model']]['model_items_order']
                        }
                     },
                    'method': {'type': 'string', 'required': True, 'allowed': ProductCheck.HUMAN_EXPRESSION_LIST},
                }
                vr = Validator(schema_filter)
                if not vr.validate(target):
                    # print(f"❌ runtime_supply 檢查失敗： {vr.errors},  model: {target['model']} pattern: {target['pattern']}")
                    self.is_verify = False
                    self.message = f"❌ runtime_filter 檢查失敗： {vr.errors}, {target['pattern']}  {target['model']}  {','.join(target['items'])}"
                    return
                else:
                    # print("alias 檢查通過")
                    self.is_verify = True
                    self.message = ''

        if True: # check runtime_disable
            # print('check runtime_disable')
            for target in self.friendly['runtime_disable']: # target = dict
                # print(target)
                # 提前檢查 target['model'] keyerror 避免 schema_alias 錯誤
                if target['model'] not in self.specification['models']:
                    self.is_verify = False
                    self.message = f"❌ runtime_disable 檢查失敗： model: {target['model']} keyerror!"
                    return

                schema_disable = {
                    'pattern': {'type': 'string', 'required': True, 'check_with': self._check_pattern },
                    'model': {'type': 'string', 'required': True, 'allowed': self.specification['models']},
                    'items': {'type': 'list', 'required': True, 'check_with': self._check_unique_list, 'schema': { # 巢狀內容的規則
                        'type': 'string',
                        'allowed': self.specification['models'][target['model']]['model_items_order']
                        }
                     },
                    'method': {'type': 'string', 'required': True, 'allowed': ProductCheck.HUMAN_EXPRESSION_LIST},
                }
                vr = Validator(schema_disable)
                if not vr.validate(target):
                    # print(f"❌ runtime_supply 檢查失敗： {vr.errors},  model: {target['model']} pattern: {target['pattern']}")
                    self.is_verify = False
                    self.message = f"❌ runtime_disable 檢查失敗： {vr.errors}, {target['pattern']}  {target['model']}  {','.join(target['items'])}"
                    return
                else:
                    # print("alias 檢查通過")
                    self.is_verify = True
                    self.message = ''

        if True: # check fast_model
            # print('check fast_model')
            for target in self.friendly['fast_model']: # target = dict
                # print(target)
                schema_fast_model = {}
                for key, _ in target.items(): # key = 'index_8'
                    index = key.split('_')[1]
                    target_model = self.specification['models_order'][int(index)]
                    # print('key:', key, 'index:', index, 'model:', target_model)

                    # 提前檢查 self.specification['models'] keyerror 避免 schema_fast_model 錯誤
                    if target_model not in self.specification['models']:
                        self.is_verify = False
                        self.message = f"❌ fast_model 檢查失敗： model: {target_model} keyerror!"
                        return

                    schema_fast_model.setdefault(key, {'type': 'string', 'required': True,
                        'allowed': self.specification['models'][target_model]['model_items_order']})

                # print(json.dumps(schema_fast_model, indent=4, ensure_ascii=False))
                vr = Validator(schema_fast_model)
                if not vr.validate(target):
                    # print(f"❌ fast_model 檢查失敗： {vr.errors})
                    self.is_verify = False
                    self.message = f"❌ fast_model 檢查失敗： {vr.errors}"
                    return
                else:
                    # print("alias 檢查通過")
                    self.is_verify = True
                    self.message = ''

    def _insert_opposite(self): # 添加對向規則
        if True: # runtime_filter
            # 建立反向規則 record
            opposite_records = copy.deepcopy(self.friendly['runtime_filter'])
            for record in opposite_records:
                new_items = other_itmes(record['items'], self.specification['models'][record['model']]['model_items_order'])
                new_method = self._toggle_human(record['method'])
                # print('new_items:', new_items)
                # print('new_method:', new_method)
                record.update({'items': new_items, 'method': new_method}) # 更新

            # print(json.dumps(opposite_records, indent=4, ensure_ascii=False))
            self.friendly['runtime_filter'].extend(opposite_records) # 添加入主規則
            # print(json.dumps(self.friendly['runtime_filter'], indent=4, ensure_ascii=False))

        if True: # runtime_disable
            # 建立反向規則 record
            opposite_records = copy.deepcopy(self.friendly['runtime_disable'])
            for record in opposite_records:
                new_items = other_itmes(record['items'], self.specification['models'][record['model']]['model_items_order'])
                new_method = self._toggle_human(record['method'])
                # print('new_items:', new_items)
                # print('new_method:', new_method)
                record.update({'items': new_items, 'method': new_method}) # 更新

            # print(json.dumps(opposite_records, indent=4, ensure_ascii=False))
            self.friendly['runtime_disable'].extend(opposite_records) # 添加入主規則
            # print(json.dumps(self.friendly['runtime_disable'], indent=4, ensure_ascii=False))

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

    def _models_pattern_dict(self):
        models_pattern = {}
        code_lenght = 0
        for model in self.specification['models_order']:
            models_pattern.setdefault(f"{model}", f'^.{{{code_lenght}}}')
            code_lenght += self.specification['models'][model]['model_item_length']
        return models_pattern

    def _merge_fruit(self):
        # 將 specification, friendly 合併為最終的結果 fruit
        fruit = copy.deepcopy(self.specification)

        # records = rd
        # alias
        rd_alias = self.friendly.get('alias', []) # 已先經過重新構造 _transform_friendly() 才會抓取正確
        if rd_alias:
            dic_alias = self.bw.build_alias(rd_alias) # record 建構為 dict
            # print(json.dumps(dic_alias, indent=4, ensure_ascii=False))
            self.merger.merge(fruit, dic_alias) # 合併至 fruit

        # runtime_supply
        rd_runtime_supply = self.friendly.get('runtime_supply', [])
        if rd_runtime_supply:
            dic_runtime_supply = self.bw.build_supply(rd_runtime_supply) # record 建構為 dict
            # print(json.dumps(dic_runtime_supply, indent=4, ensure_ascii=False))
            self.merger.merge(fruit, dic_runtime_supply) # 合併至 fruit

        # runtime_filter
        rd_runtime_filter = self.friendly.get('runtime_filter', [])
        if rd_runtime_filter:
            dic_runtime_filter = self.bw.build_filter(rd_runtime_filter) # record 建構為 dict
            # print(json.dumps(dic_runtime_filter, indent=4, ensure_ascii=False))
            self.merger.merge(fruit, dic_runtime_filter) # 合併至 fruit

        # runtime_disable
        rd_runtime_disable = self.friendly.get('runtime_disable', [])
        if rd_runtime_disable:
            dic_runtime_disable = self.bw.build_disable(rd_runtime_disable) # record 建構為 dict
            # print(json.dumps(dic_runtime_disable, indent=4, ensure_ascii=False))
            self.merger.merge(fruit, dic_runtime_disable) # 合併至 fruit

        # fast_model
        rd_fast_model = self.friendly.get('fast_model', [])
        if rd_fast_model:
            fruit.setdefault('fast_model', self.bw.build_fast_model(rd_fast_model)) # 添加 fast_model

        # models_pattern
        fruit.setdefault('models_pattern', self._models_pattern_dict()) # 添加 models_pattern

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
    uid = '4b87a39d-a0e4-4f73-8945-ebc54994e112'
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