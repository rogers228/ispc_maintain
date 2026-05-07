# 專門處理 dict 混淆及編碼

import base64
import json


class Garbler():
    def __init__(self):

        # key 混淆 mapping  需同步修改前端 decoder.js
        # 請用 tool_str.py 產生
        self.garble_key_map = {
            'data_json': 'ILllI1JJ',
            'name': 'IlJJ1LlI', # 產品名稱 admin test user 123
            'company': 'Jl1IJILl', # 所屬公司代號
            'name_en': 'lJlJILI1',
            'name_tw': 'Ill1LJIJ',
            'name_zh': 'J1lIJLIl',
            'supply_default_value': 'JllIILJ1',
            'model_item_length': 'IIJJl1lL',
            'model_items_order': 'I1llIJJL',
            'model_items': 'JlIJILl1',
            'select_way': 'IlJlL1IJ',
            'models': 'LlIl1JJI',
            'description_en': 'lJlJ1LII',
            'description_tw': 'IlJILJ1l',
            'description_zh': 'l1JJIlIL',
            'introduction_id' : 'I1lIlLJJ',
            'photo_album' : 'JIll1LJI',
            'og_image': 'LI1JIlJl',
            'keywords': 'JLIl1lJI',

            'postfix_symbol': 'LIlJ1JIl',
            'default_value': 'LIIJJll1',
            'unit': 'LlJIJI1l',
            'control_type': 'JL1IlIlJ',
            'model_item_length': 'ILllJJI1',
            'model_items_order': 'JIl1JLIl',
            'model_items': 'llLIJI1J',

            'item_name_en': 'IlILJJ1l',
            'item_name_tw': 'IIJl1LlJ',
            'item_name_zh': 'JIILll1J',
            'supply': 'J1IIlLJl',
            'models_pattern': 'lJJL1IlI',
            'runtime_pattern': 'lJJI1lIL',
            'disable': 'IlJLJ1Il',
            'display': 'JLJlII1l',

            'alias': 'IJllJI1L',
            'model_help': 'lLlIIJJ1',
            'option_item_count': 'I1JLJlIl',
            'main_model': 'IlJIJlL1',

            # company
            'company_name': 'ILlIlJ1J',
            'company_name_en': 'LIlJI1lJ',
            'company_name_tw': 'JIJIlLl1',
            'company_name_zh': 'L1lJlIJI',
            'description_en': 'lIJILJl1',
            'description_tw': 'JILI1llJ',
            'description_zh': 'LllIJ1IJ',
            'address_tw': 'JIlIl1JL',
            'address_en': 'L1IIlJJl',
            'email': 'ILlJ1IJl',
            'tel': 'lIIJ1lLJ',
            'fax': 'lJIlL1IJ',
            'sales_tw': 'llLJJI1I',
            'sales_en': 'LJlIJ1lI',
            'Facebook': 'IlIJlL1J',
            'YouTube': 'IlJLJ1lI',
            'Line': 'IlJI1JLl',
            'Instagram': 'lI1IJJlL',
            'Twitter': 'J1IlLJlI',
            'LinkedIn': 'IIJlJ1lL',
            'Reddit': 'JJ1lILlI',
            'TikTok': 'LI1IJJll',
            'website': 'Ll1IJJIl',
            'introduction_id' : 'IJLlJ1lI',
            'logo_url': 'IILJlJl1',
            'google_map_url': 'L1JlIJlI',
            'og_image': 'IIJl1lLJ',
            'products': 'lJLlJI1I',
            'articles': 'IJlLI1Jl',
            'product_quantity': 'ILIJ1Jll',
            'allowe_logo': 'JIJL1llI',
            'fast_model': 'LIl1JJIl',
            'models_pattern': 'JIl1IJlL',
        }

        # 檢查values 不可重複
        values = list(self.garble_key_map.values())
        if len(values) != len(set(values)):
            raise ValueError("garble_key_map has duplicate values")

        # 哪些 key 的 value 要 encode（全域）
        self.encode_value_keys = {'key_h'}


    # Base64 encode
    def encode_value(self, val):
        if not isinstance(val, str):
            val = json.dumps(val, separators=(',', ':'))  # 更緊湊
        return base64.b64encode(val.encode('utf-8')).decode('utf-8')

    def replace_key(self, source):

        # dict
        if isinstance(source, dict):
            new_dict = {}

            for key, value in source.items():

                # 🔹 key 混淆
                new_key = self.garble_key_map.get(key, key)

                # 🔹 value 處理（重點：判斷原始 key）
                if key in self.encode_value_keys:
                    new_value = self.encode_value(value)
                else:
                    new_value = self.replace_key(value)

                new_dict[new_key] = new_value

            return new_dict

        # list
        elif isinstance(source, list):
            return [self.replace_key(item) for item in source]

        # tuple（補強）
        elif isinstance(source, tuple):
            return tuple(self.replace_key(item) for item in source)

        # 其他型別
        else:
            return source

    def get_garble_key_reverse(self):
        reversed_dic = {v: k for k, v in self.garble_key_map.items()}
        return reversed_dic

    def secret_encode(self, text, key=6):
        # 第一步：進行位移 (ord + key)
        shifted_text = "".join(chr(ord(c) + key) for c in text)

        # 第二步：轉成 bytes 並進行 Base64 編碼
        bytes_data = shifted_text.encode('utf-8')
        base64_bytes = base64.b64encode(bytes_data)

        # 第三步：轉回字串方便傳輸
        return base64_bytes.decode('utf-8')

def test1():

    data = {
        'key_a': 1,
        'key_b': 'freedom',
        'key_c': [
            {'key_d': True},
            {
                'key_x': {
                    'key_y': [
                        {
                            'key_h': 'deep_secret_1'
                        },
                        {
                            'key_z': {
                                'key_h': 'deep_secret_2'
                            }
                        }
                    ]
                }
            },
        ],
        'key_e': {
            'key_f': {
                'key_g': 45,
                'key_h': 'passwork'
            },
            'key_i': 'safe',
        }
    }

    ga = Garbler()
    result = ga.replace_key(data)

    print("原始資料：")
    print(data)

    print("\n處理後：")
    print(result)

def test2():
    # 得到反置的 map
    # 用來貼上 api.js GarblerDecoder
    ga = Garbler()
    dic = { 'this.reverseKeyMap': ga.get_garble_key_reverse()}
    print(json.dumps(dic, indent=4, ensure_ascii=False))

def test3():
    ga = Garbler()
    my_key = 5
    raw_data = "Hello World!"
    encoded_result = ga.secret_encode(raw_data)
    print(f"原始資料: {raw_data}")
    print(f"傳輸內容: {encoded_result}")

if __name__ == '__main__':
    test3()