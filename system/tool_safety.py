# 專門處理 dict 混淆及編碼

import base64
import json


class Garbler():
    def __init__(self):

        # key 混淆 mapping  需同步修改前端 decoder.js
        # 請用 tool_str.py 產生
        self.garble_key_map = {
            'key_d': 'lJL1JlII',
            'key_h': 'ILJ1lIlJ',
            'product_quantity': 'ILIJ1Jll',
            'allowe_logo': 'JIJL1llI',
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

if __name__ == '__main__':
    test1()