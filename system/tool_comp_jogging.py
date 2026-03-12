# tool_comp_jogging.py
if True:
    import sys, os
    import json

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
    from config_web import SPECIC_DOMAIN, WEB_SPECIC_ASSETS_URL
    from tool_auth import AuthManager
    from tool_options import Options
    from tool_list import is_all_include, other_itmes
    from tool_msgbox import error
    from tool_cache import Cache_article, Cache_file

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

        self.cha = Cache_article() # 本地快取 檢查 article
        self.chf = Cache_file()    # 本地快取 檢查 file

        self.lis_safe_origin = ['https://assets.specic.store'] # 合法靜態資源主機
        self.placeholder = 'images/hu5vyx6ge2k9sv5q.jpg'; # 佔位圖片 無圖檔時使用

        self.auth = AuthManager()
        data = self.auth.load_local_data()
        self.email = data.get("email", "") # 使用者 email
        # print(self.email)
        self.opt = Options()
        self.options = self.opt.get_options_auto()
        # print(json.dumps(self.options, indent=4, ensure_ascii=False))
        self.option_comp = None # 後續取得
        self._load_content()                # 動態讀取 python content

        if self.is_verify is True:
            self._add_specification_required()  # 添加 specification 必需的

        if self.is_verify is True:
            self._check_root()    # 檢查 specification 根層

        if self.is_verify is True:              # 添加 head_part
            self._insert_head_part()
            self._insert_json_ld()

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

    def _find_comp_by_uid_option(self, garden_user, target_uid):
        # 從 option 獲取公司資料
        # garden_user 是 self.option[garden][email]
        for item in garden_user:
            # 每個 item 是一個只有一個 key 的 dict，例如 {"ys_v_dev": {...}}
            for key_company, value_dic in item.items():
                # info 就是內層 dict
                if value_dic.get("uid") == target_uid:
                    return value_dic
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

        self.option_comp = self._find_comp_by_uid_option(self.options['garden'][self.email], self.uid)
        self.is_verify = True

    def _add_specification_required(self): # 添加 specification 必需的
        dic_default = { # 預設值
            'uid': self.uid,
            'cono': self.option_comp.get('cono', ''),
        }
        self.specification.update(dic_default)

    def _is_img_verify(self, target_url):
        print('target_url:', target_url)
        # 若為空字串，視為合法 (由 _check_root 的邏輯決定是否跳過)
        if not target_url: return True

        img_exts = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.ico'}
        # 取得副檔名 (含點，轉小寫)
        ext = os.path.splitext(target_url.split('?')[0])[1].lower()
        if ext not in img_exts: return False

        # 情況 A: 完整 URL 檢查
        if target_url.startswith('http'):
            return any(target_url.startswith(origin) for origin in self.lis_safe_origin)

        # 情況 B: 相對路徑檢查 (必須以 images/ 開頭)
        # 使用 regex 確保格式為 images/檔名.副檔名
        return bool(re.match(r'^images/[\w\.-]+$', target_url))

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
            'logo_url': {'type': 'string', 'required': True},
            'google_map_url': {'type': 'string', 'required': True},
            'og_image': {'type': 'string', 'required': True},
            'products': {'type': 'list', 'required': True, 'schema': {'type': 'string'}},
            'articles': {'type': 'list', 'required': True, 'schema': {'type': 'string'}},
        }

        vr = Validator(schema)
        target = self.specification
        if not vr.validate(target):
            # print(f"❌ 第一層檢查失敗： {vr.errors}")
            self.is_verify = False
            self.message = f"❌ 第一層檢查失敗： {vr.errors}"
            return

        # 針對圖片欄位進行深度檢查
        files = []
        og_image = self.specification.get('og_image', '') # 公司介紹
        if og_image:
            files.append(og_image)

        logo_url = self.specification.get('logo_url', '')
        if logo_url:
            files.append(logo_url)

        for file_path in files:

            if not self.chf.is_file_verify(file_path): # 檢查是否存在
                self.is_verify = False
                self.message = f"❌ 找不到 {file_path} 不存在，或請重新讀取檔案。"
                return

            if not self._is_img_verify(val):
                self.is_verify = False
                self.message = f"❌ {field} 格式錯誤或來源不合法"
                return

        # 針對文章 進行檢查 是否有本地 文章
        cono = self.option_comp.get('cono', '')

        all_articles = [] # 所有文章
        introduction_id = self.specification.get('introduction_id', '') # 公司介紹
        articles = self.specification.get('articles', []) # 精選文章

        all_articles = [*articles, introduction_id]

        # 暫無zh
        langs = ['en', 'tw']
        for lang in langs:
            for idx in all_articles: # 檢查所有文章
                custom_index = f"{cono}_article_{idx}_{lang}"
                if not self.cha.is_article_verify(custom_index): # 檢查是否存在
                    self.is_verify = False
                    self.message = f"❌ 文章 {custom_index} 不存在!"
                    return

        # print("首層 檢查通過")
        self.is_verify = True
        self.message = ''



    def _merge_fruit(self):
        # 將 specification, friendly 合併為最終的結果 fruit
        fruit = copy.deepcopy(self.specification)

        dic_products = {'extend_products': self._extend_products()}
        dic_articles = {'extend_articles': self._extend_articles()}
        # print(json.dumps(dic_products, indent=4, ensure_ascii=False))

        self.merger.merge(fruit, dic_products) # 合併至 fruit
        self.merger.merge(fruit, dic_articles)
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
            if not os.path.exists(path):
                self.is_verify = False
                self.message = f"❌ {uid}.py 不存在，請先下載"
                return

            try:
                # 讀取並執行產品配置檔
                with open(path, 'r', encoding='utf-8') as f:
                    local_v = {}
                    exec(f.read(), {}, local_v)
                    s = local_v.get('specification', {})
            except Exception as e:
                self.is_verify = False
                self.message = f"❌ 讀取產品 {uid} 失敗: {e}"

            # check images
            name = s.get('name', '')
            photo_album = s.get('photo_album', [])
            for file_path in photo_album:
                if not self.chf.is_file_verify(file_path):
                    self.is_verify = False
                    self.message = f"❌ {name} 的欄位 photo_album 資料 '{file_path}'，找不到實際檔案"

            # 組裝結果
            result.append({
                'pdno': pdno,
                'name_en': s.get('name_en', ''),
                'name_tw': s.get('name_tw', ''),
                'name_zh': s.get('name_zh', ''),
                'description_en': s.get('description_en', ''),
                'description_tw': s.get('description_tw', ''),
                'description_zh': s.get('description_zh', ''),
                'introduction_id': s.get('introduction_id', ''),
                'photo_album': photo_album,
            })

        return result

    def _find_html_title(self, content):
        # 尋找第一個 <h1> 或 <h2> 標籤內的文字
        match = re.search(r'<(h1|h2)[^>]*>(.*?)</\1>', content, re.IGNORECASE | re.DOTALL)
        return match.group(2).strip() if match else ""

    def _extend_articles(self):
        # 暫無zh
        cono = self.option_comp.get('cono', '')
        result = {'articles_en': [], 'articles_tw': []}
        langs = ['en', 'tw']
        for lang in langs:
            for idx in self.specification.get('articles', []):
                custom_index = f"{cono}_article_{idx}_{lang}"
                art = self.cha.get_article(custom_index)
                result[f'articles_{lang}'].append({
                    "custom_index": art.get("custom_index"),
                    "title": self._find_html_title(art.get("html_snapshot", "")),
                })

        return result

    def _insert_head_part(self): # 添加seo head 屬性部分
        spec = self.specification
        vendor_path = self.option_comp.get('vendor_path', '')
        # print(self.option_comp)

        dic_langs = {
            'en': {'url_path': 'en', 'hreflang': 'en'},
            'tw': {'url_path': 'zh-TW', 'hreflang': 'zh-Hant'},
            'zh': {'url_path': 'zh-TW', 'hreflang': 'zh-Hans'} # // 若 zh 指向簡體，建議改為 zh-Hans
        }

        dic_s = {}
        for lang, info in dic_langs.items():
            name = spec.get(f"company_name_{lang}", "")
            description = spec.get(f"description_{lang}", "")
            f_lang = info['url_path'] # 前端語系
            current_url = f"{SPECIC_DOMAIN}/{f_lang}/app/v/{vendor_path}"

            og_image_path = spec.get("og_image") or self.placeholder
            og_image = f"{WEB_SPECIC_ASSETS_URL}/{og_image_path}"

           # 基礎 Meta 標籤
            lines = [
                f"<title>{name}</title>",
                f"<meta property='og:type' content='product'>",
                f"<meta property='og:title' content='{name}'>",
                f"<meta property='og:description' content='{description}'>",
                f"<meta property='og:url' content='{current_url}'>",
                f"<meta property='og:image' content='{og_image}'>",
                f"<meta property='og:site_name' content='Specic'>",
                f"<link rel='canonical' href='{current_url}'>",
            ]

            # 注入所有語系的 alternate 連結 (包含自己)
            for alt_lang, alt_info in dic_langs.items():
                alt_url = f"{SPECIC_DOMAIN}/{alt_info['url_path']}/app/v/{vendor_path}"
                lines.append(f"<link rel='alternate' hreflang='{alt_info['hreflang']}' href='{alt_url}'>")

            # 添加 x-default (通常指向英文版作為預設語系)
            default_url = f"{SPECIC_DOMAIN}/en/app/v/{vendor_path}"
            lines.append(f"<link rel='alternate' hreflang='x-default' href='{default_url}'>")

            dic_s[lang] = '\n'.join(lines)
        spec['head_part'] = dic_s

    def _insert_json_ld(self): # 添加 seo json_ld 部分
        spec = self.specification
        vendor_path = self.option_comp.get('vendor_path', '')

        # // 語系定義（與 head_part 保持一致，用於構造網址）
        dic_langs = {
            'en': 'en',
            'tw': 'zh-TW',
            'zh': 'zh-TW'
        }

        dic_ld = {} # dict

        for lang, f_lang in dic_langs.items():
            # 構造基本產品資料
            current_url = f"{SPECIC_DOMAIN}/{f_lang}/app/v/{vendor_path}"
            brand = spec.get("company_name", "Specic") # 品牌
            name = spec.get(f"company_name_{lang}", "")
            description = spec.get(f"description_{lang}", "")

            # 建立 JSON-LD 結構
            ld_data = {
                "@context": "https://schema.org/",
                "@type": "Product",
                "name": name,
                "description": description,
                "url": current_url,
                "brand": {
                    "@type": "Brand",
                    "name": brand, # 品牌
                }
            }
            dic_ld[lang] = ld_data # 最後才會序列畫

        spec['json_ld'] = dic_ld

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
        # print(result['fruit'])

        print(json.dumps(result['fruit'], indent=4, ensure_ascii=False))
    else:
        print(result['message'])

if __name__ == '__main__':
    test1()