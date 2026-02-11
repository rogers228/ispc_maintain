# tool_comp_jogging.py
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
    # from tool_parser import LineParser, BuildingWorker
    from tool_list import is_all_include, other_itmes

class CompanyCheck:
    STORAGE_PATH = os.path.join(ROOT_DIR, 'tempstorage')

    def __init__(self, uid):
        self.uid = uid
        self.data_original = '' # 原始檔案內容 (整個py文字檔)
        self.specification = {} # 主要規格 dict
        self.fruit = {}         # 最終合併後的結果 dict
        self.message = '' # 檢查訊息
        self.is_verify = None # 是否驗證通過

        self.merger = Merger([(list, ["append"]), (dict, ["merge"])],["override"], ["override"]) # 合併者的策略

        self.auth = AuthManager()
        data = self.auth.load_local_data()
        self.email = data.get("email", "") # 使用者 email
        # print(self.email)
        self.opt = Options()
        self.options = self.opt.get_options_auto()
        # print(json.dumps(self.options, indent=4, ensure_ascii=False))
        self.cono = self._find_cono_by_uid(self.options['garden'][self.email], self.uid)
        # print(self.cono)
        self._load_content()                # 動態讀取 python content

        if self.is_verify is True:
            self._add_specification_required()  # 添加 specification 必需的

        if self.is_verify is True:
            self._check_root()    # 檢查 specification 根層

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

    def _find_cono_by_uid(self, garden_user, target_uid):
        # garden_user 是 self.option[garden][email]
        for item in garden_user:
            # 每個 item 是一個只有一個 key 的 dict，例如 {"ys_v_dev": {...}}
            for _, info in item.items():
                # info 就是內層 dict
                if info.get("uid") == target_uid:
                    return info.get("cono")
        return None

    def _load_content(self): # 動態讀取 python content
        self.is_verify = False
        file_path = os.path.join(CompanyCheck.STORAGE_PATH, f"{self.uid}.py")

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

        if isinstance(specification, dict):
            self.specification = specification
        elif specification is None:
            self.message = f"❌ 找不到 specification"
            return
        else:
            self.message = f"❌ specification 類型錯誤"
            return

        self.is_verify = True

    def _add_specification_required(self): # 添加 specification 必需的
        dic_default = { # 預設值
            'uid': self.uid,
            'cono': self.cono,
        }
        self.specification.update(dic_default)

    def _check_root(self): # 檢查 specification 根層
        self.is_verify = False # 是否驗證通過
        schema = {
            'uid': {'type': 'string', 'required': True}, # required 必填
            'cono': {'type': 'string', 'required': True}, # 自動
            'company_name': {'type': 'string', 'required': True},
            'company_name_en': {'type': 'string', 'required': True},
            'company_name_tw': {'type': 'string', 'required': True},
            'company_name_zh': {'type': 'string', 'required': True},
            'description_en': {'type': 'string', 'required': True},
            'description_tw': {'type': 'string', 'required': True},
            'description_zh': {'type': 'string', 'required': True},
            'address_tw': {'type': 'string', 'required': True},
            'address_en': {'type': 'string', 'required': True},
            'email': {'type': 'string', 'required': True},
            'tel': {'type': 'string', 'required': True},
            'fax': {'type': 'string', 'required': True},
            'sales_tw': {'type': 'string', 'required': True},
            'sales_en': {'type': 'string', 'required': True},

            'Facebook': {'type': 'string', 'required': True},
            'YouTube': {'type': 'string', 'required': True},
            'Line': {'type': 'string', 'required': True},
            'Instagram': {'type': 'string', 'required': True},
            'Twitter': {'type': 'string', 'required': True},
            'LinkedIn': {'type': 'string', 'required': True},
            'Reddit': {'type': 'string', 'required': True},
            'TikTok': {'type': 'string', 'required': True},

            'website': {'type': 'string', 'required': True},
            'introduction_id': {'type': 'string', 'required': True},
            'company_image_url': {'type': 'string', 'required': True},
            'logo_url': {'type': 'string', 'required': True},
            'google_map_url': {'type': 'string', 'required': True},
            'products': {'type': 'list', 'required': True, 'schema': {'type': 'string'}},
            'articles': {'type': 'list', 'required': True, 'schema': {'type': 'string'}},
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

    def _merge_fruit(self):
        # 將 specification, friendly 合併為最終的結果 fruit
        fruit = copy.deepcopy(self.specification)

        dic_products = {'extend_products': self._extend_products()}
        print(json.dumps(dic_products, indent=4, ensure_ascii=False))

        self.merger.merge(fruit, dic_products) # 合併至 fruit

        self.fruit = fruit

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

    def _extend_products(self):
        # print(self.specification['products'])
        result = []
        for uid in self.specification['products']:
            pdno = self._find_pdno_by_uid(self.options['permissions'][self.email], uid)
            path = os.path.join(self.STORAGE_PATH, f"{uid}.py")
            if not os.path.exists(path): continue

            try:
                # 讀取並執行產品配置檔
                with open(path, 'r', encoding='utf-8') as f:
                    local_v = {}
                    exec(f.read(), {}, local_v)
                    s = local_v.get('specification', {})
                    # 組裝結果
                    result.append({
                        'pdno': pdno,
                        'name_en': s.get('name_en', ''),
                        'name_tw': s.get('name_tw', ''),
                        'name_zh': s.get('name_zh', '')
                    })
            except Exception as e: print(f"❌ 讀取產品 {uid} 失敗: {e}")
        return result

    def get_detaile(self):
        # 將 fruit 轉換為 json
        json_result = self._dict_to_json(self.fruit)
        data_json = json_result if json_result is not None else ""

        return {
            'data_original': self.data_original, # 原始檔案內容 (整個py文字檔) string
            'specification': self.specification, # 規格      使用者輸入     dict
            'fruit':         self.fruit,         # 最終結果  輸出           dict
            'data_json':     data_json,          # 最終結果  輸出   json string
            'message':       self.message,       # 錯誤訊息         string
            'is_verify':     self.is_verify,     # 檢查輸入是否合法  boolean
        }

def test1():
    uid = 'ee080167-e20e-45bf-84ce-f5516022331c'
    cc = CompanyCheck(uid)
    result = cc.get_detaile()
    # print(result)
    if result['is_verify'] is True:
        print('驗證成功')
        # print(result['data_original'])
        # print(result['data_json'])
        print(result['fruit'])

    else:
        print(result['message'])

    # result = cc._extend_products()
    # print(json.dumps(result, indent=4, ensure_ascii=False))
if __name__ == '__main__':
    test1()