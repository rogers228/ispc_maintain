if True:
    import sys, os
    import re
    import csv
    import json
    import pandas as pd
    from io import StringIO
    from collections import defaultdict

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


class LineParser:
    # 解析多行文字，轉換為 records list[dict]
    # 每行是以空白符作為分隔
    # 內容的直自動轉換類型，# text_fields 強制指定為 text 的欄位
    def __init__(self, lines, columns, text_fields = None):
        self.lines = lines
        self.columns = columns
        self.text_fields = text_fields if text_fields is not None else set()
        self.data = self._parse_lines()  # 初始化時就直接解析

        # 型別檢查
        # is_error, message = self._is_error_types(self.data)
        # if is_error:
        #     print(message)
        #     raise TypeError("欄位型別錯誤!")
        # else:
        #     pass
        #     # print("✅ 型別檢查通過")

    def _parse_list(self, key, raw):
        """處理中括號包裹的 list，去除空白，並自動轉換"""
        if not (raw.startswith("[") and raw.endswith("]")):
            return raw

        content = raw[1:-1].strip()
        if not content:
            return []

        # 處理引號和空白
        items = [x.strip(" '\"") for x in content.split(",")]

        def auto_cast(val):
            """內部自動轉換，支援 int, float, str"""
            if key in self.text_fields:
                return val
            try:
                # 優先判斷是否為浮點數
                if "." in val and val.replace(".", "", 1).isdigit():
                    return float(val)
                # 接著判斷是否為整數
                if val.isdigit() or (val.startswith('-') and val[1:].isdigit()):
                    return int(val)
                return val # 預設回傳字串
            except ValueError:
                return val

        return [auto_cast(x) for x in items]

    def _auto_cast_value(self, key, value):
        """根據 key 嘗試自動轉換型別 (布林, 數字, 字串)"""

        # 如果欄位名稱在 text_fields 集合中，則直接回傳字串，不進行數字轉換
        if key in self.text_fields:
            return value

        # 1. 處理布林值
        if value.lower() in {"true", "yes", "1"}:
            return True
        if value.lower() in {"false", "no", "0"}:
            return False

        # 2. 處理數字
        try:
            if "." in value:
                return float(value)
            return int(value)
        except ValueError:
            # 3. 預設回傳字串
            return value

    def _is_error_types(self, data, check_all=True):
        """檢查 list[dict] 每個欄位的型別 (內部方法)"""
        field_types = {}
        # 僅檢查第一筆資料以判斷型別，除非 check_all=True
        rows = data if check_all else data[:1]

        for record in rows:
            for key, value in record.items():
                field_types.setdefault(key, set()).add(type(value).__name__)

        # 判斷是否有欄位包含超過一種型別
        is_error = any(len(types) > 1 for types in field_types.values())
        details = {
            field: {"types": sorted(list(types)), "is_error": len(types) > 1}
            for field, types in field_types.items()
        }

        message = "⚠️ 欄位型別不一致檢查結果：\n"
        for field, info in details.items():
            types = ", ".join(info["types"])
            flag = "⚠️" if info["is_error"] else "✅"
            message += f"{flag} {field:<10} → {types}\n"

        return is_error, message

    def _preprocess_line(self, line):
        """將 line 中的 [list] 預先處理，去掉內部空白 (內部方法)"""
        # 找到所有 [list] 結構
        def replacer(match):
            # 對匹配到的 [list] 內容，去掉內部所有空白
            # 這樣 csv.reader 就不會誤判 list 內部的元素間隔
            return re.sub(r"\s+", "", match.group(0))

        # 應用替換，只針對中括號內容進行
        return re.sub(r"\[.*?\]", replacer, line)

    def _parse_lines(self):
        """解析多行文字，根據 schema 輸出 dict 列表 (內部方法)"""
        data = []
        for raw in self.lines.strip().split("\n"):
            # 1. 預先處理 list 內容，防止 csv.reader 錯誤分割
            line = self._preprocess_line(raw)

            # 2. 使用 csv.reader 解析，以空格為分隔符，並處理單引號
            reader = csv.reader(
                StringIO(line),
                delimiter=" ",
                skipinitialspace=True, # 忽略多餘空白
                quotechar="'"          # 處理 '單引號字串'
            )
            try:
                row = next(reader)
            except StopIteration:
                # 處理空行
                continue

            record = {}
            # 3. 根據欄位名稱和值進行自動轉換
            for key, value in zip(self.columns, row):
                if value.startswith("[") and value.endswith("]"):
                    # 這是 list 欄位，呼叫專門的 list 解析器
                    record[key] = self._parse_list(key, value)
                else:
                    # 這是普通欄位，呼叫自動轉換器
                    record[key] = self._auto_cast_value(key, value)
            data.append(record)
        return data

    def parse_info(self):
        # 解析狀況

        result = {'is_error': False, 'message': ''}
        # 型別檢查
        is_error, message = self._is_error_types(self.data)
        if is_error:
            return {'is_error': True, 'message': message}

        # print("✅ 檢查通過")
        return result

    def to_dict(self):
        """回傳 list of dict"""
        return self.data

    def to_dataframe(self, index=None):
        """轉換成 DataFrame"""
        df = pd.DataFrame(self.data)
        if index and index in df.columns:
            df.set_index(index, inplace=True)
        return df

    def to_json(self, **kwargs):
        """轉換成 JSON"""
        # 確保中文不會變成 \uXXXX
        return json.dumps(self.data, indent=4, ensure_ascii=False, **kwargs)

class BuildingWorker():
    # 以資料來源 records 建構一個 結構化的資料
    # records 是由 LineParser 解析而來的
    # 作為合併前的準備
    # 請參閱範例 test2()

    def __init__(self):
        pass

    def is_records(self, records):
        # 檢查輸入的 records 列表是否符合以下格式規範：
        # 1. 必須是 list 類型。
        # 2. 列表中必須包含至少一個元素。
        # 3. 每個元素都必須是 dict 類型。
        # 4. 每個 dict 都必須是單層結構 (值不能是 list 或 dict)。
        # 5. 所有 dict 的鍵集合必須完全相同。

        # --- 1. 檢查是否為非空列表 ---
        if not isinstance(records, list) or not records:
            print("❌ 檢查失敗: 輸入不是一個非空列表 (list)。")
            return False

        # 取得標準鍵集合 (以第一筆記錄為準)
        # 由於前面已檢查列表非空，records[0] 必定存在
        if not isinstance(records[0], dict):
            print("❌ 檢查失敗: 列表的第一個元素不是字典 (dict)。")
            return False

        standard_keys = set(records[0].keys())

        # --- 2. 檢查所有記錄 ---
        for i, record in enumerate(records):
            # 2a. 檢查元素是否為字典
            if not isinstance(record, dict):
                print(f"❌ 檢查失敗: 第 {i+1} 筆記錄不是字典 (dict)。")
                return False

            # 2b. 檢查鍵集合是否相同
            current_keys = set(record.keys())
            if current_keys != standard_keys:
                print(f"❌ 檢查失敗: 第 {i+1} 筆記錄的鍵集合與標準不符。")
                return False

            # 2c. 檢查是否為單層結構 (值不能是 list 或 dict)
            for key, value in record.items():
                if isinstance(value, (list, dict)):
                    print(f"❌ 檢查失敗: 第 {i+1} 筆記錄的欄位 '{key}' 不是單層結構 (值為 {type(value).__name__})。")
                    return False

        # 所有檢查通過
        # print("✅ 格式檢查通過: 結構正確。")
        return True

    def build_alias(self, records):

        alias_structure = defaultdict(lambda: {"model_items": defaultdict(dict)})

        for record in records:
            model = record["model"]
            item = record["item"]
            alias = record["alias"]
            alias_structure[model]['model_items'][item]['alias'] = alias

        final_models = {}
        for model_key, model_value in alias_structure.items():
            model_value['model_items'] = dict(model_value['model_items'])
            final_models[model_key] = model_value

        return {"models": final_models}

    def build_supply(self, records):

        supply_structure = defaultdict(lambda: {"model_items": defaultdict(dict)})

        for record in records:
            model = record["model"]
            pattern = record["pattern"]
            items = record["items"]
            supply = record["supply"]
            supply_data = {"supply": supply}

            for item in items:
                item_data = supply_structure[model]['model_items'][item]
                if "runtime_pattern" not in item_data:
                    item_data["runtime_pattern"] = {}

                item_data["runtime_pattern"][pattern] = supply_data

        final_models = {}
        for model_key, model_value in supply_structure.items():
            model_items_dict = dict(model_value['model_items'])
            final_models[model_key] = {'model_items': model_items_dict}

        return {"models": final_models}

    def build_filter(self, records):

        filter_structure = defaultdict(lambda: {"model_items": defaultdict(dict)})
        display_mapping = {
            "-s": True,
            "-u": False
        }

        for record in records:
            model = record["model"]
            pattern = record["pattern"]
            items = record["items"]
            method = record["method"]

            display_value = display_mapping.get(method, True)
            display_data = {"display": display_value}
            for item in items:
                item_data = filter_structure[model]['model_items'][item]
                if "runtime_pattern" not in item_data:
                    item_data["runtime_pattern"] = {}
                item_data["runtime_pattern"][pattern] = display_data

        final_models = {}
        for model_key, model_value in filter_structure.items():
            model_items_dict = dict(model_value['model_items'])
            final_models[model_key] = {'model_items': model_items_dict}

        return {"models": final_models}

    def build_disable(self, records):

        filter_structure = defaultdict(lambda: {"model_items": defaultdict(dict)})
        disable_mapping = {
            "-s": False,
            "-u": True
        }

        for record in records:
            model = record["model"]
            pattern = record["pattern"]
            items = record["items"]
            method = record["method"]

            disable_value = disable_mapping.get(method, True)
            display_data = {"disable": disable_value}
            for item in items:
                item_data = filter_structure[model]['model_items'][item]
                if "runtime_pattern" not in item_data:
                    item_data["runtime_pattern"] = {}
                item_data["runtime_pattern"][pattern] = display_data

        final_models = {}
        for model_key, model_value in filter_structure.items():
            model_items_dict = dict(model_value['model_items'])
            final_models[model_key] = {'model_items': model_items_dict}

        return {"models": final_models}

    def build_fast_model(self, records):
        return [''.join(e.values()) for e in records] if records else []


    def build_button_image(self, records):
        # // 1. 使用 defaultdict 建立巢狀結構
        from collections import defaultdict
        image_structure = defaultdict(lambda: {"model_items": defaultdict(dict)})

        # // 2. 遍歷 records 進行重組
        for record in records:
            model = record["model"]
            item = record["item"]
            # // 使用 str() 確保賦值為獨立字串而非引用
            image_path = str(record["image_path"])

            # // 寫入對應的 button_image 欄位
            image_structure[model]['model_items'][item]['button_image'] = image_path

        # // 3. 將 defaultdict 轉換回普通 dict 以符合 JSON 序列化要求
        final_models = {}
        for model_key, model_value in image_structure.items():
            # // 轉換內層的 model_items
            model_value['model_items'] = dict(model_value['model_items'])
            final_models[model_key] = model_value

        return {"models": final_models}

    def build_model_help(self, records):
        # // 1. 檢查格式 (確保輸入合法)
        if not self.is_records(records):
            return {"models": {}}

        from collections import defaultdict

        # // 2. 建立初步結構，外層使用 dict 即可，因為這層不涉及 deeply nested 資料
        final_models = {}

        for record in records:
            model = record["model"]
            custom_index = record["custom_index"]

            # // 將 custom_index 寫入 model_help 欄位
            # // 結構為 models -> {model_id} -> model_help
            final_models[model] = {
                "model_help": str(custom_index)
            }

        # // 3. 返回符合要求的 dict 結構
        return {"models": final_models}

def test1(): # 以文字行 解析為 records
    # 測試

    # columns = [
    #     "id", "name", "age", "score", "active", "friends", "food", "hobbies", "regex", "username" ]
    # lines = '''
    #     awwww allen   18    95.5      true  [joe,andy]                'Curry Rice' ['singing','music']      ^.{18}(028|045).+  al_123
    #     byy   roger   20    88.0      false [jay]                      Steak       ['movies','drinking']    ^.{18}(063|071).+  roger_01
    #     ccc   andy    25    72.5      yes   [amy,bob, tom, 100, 88.5] 'Salad Bowl' [reading, 'coding']      ^.{18}(085|100).+  kateX
    # '''
    # data = LineParser(lines, columns)

    # columns = [
    #     "model", "item", "alias"]
    # lines = '''
    #     03dp   010   10
    # '''
    # data = LineParser(lines, columns, text_fields=("item", "alias")) # 強制數字轉文字

    # columns = [
    #     "id", "age", "code", "codes", "friends"]
    # lines = '''
    #     awwww   18   200  [200, 201, 202]  [joe,andy]
    #     byy     20   300  [300, 301, 302]  [jay]
    #     ccc     25   400  [400, 401, 402]  [amy,bob, tom, 100, 88.5]
    # '''
    # data = LineParser(lines, columns, text_fields=("code", "codes"))

    columns = [
        "pattern", "model", "items", "supply"]
    lines = '''
        ^.{15}(10).+  ;     03dp  [018, 028]  d
        ^.{15}(60).+       03dp  [045, 071]  d
        ^.{15}(80).+       05sr  [52 ]  n
    '''
    data = LineParser(lines, columns, text_fields=("pattern", "model", "items", "supply"))

    result = data.parse_info()
    if result['is_error'] is True:
        print('解析錯誤!', result['message'])
        return

    print("\n📌 DICT 格式：")
    print(data.to_dict())

    print("\n📌 JSON 格式：")
    print(data.to_json())

    print("\n📌 DataFrame：")
    df = data.to_dataframe(index="id")
    print(df)

# def build_alias(records):

#     alias_structure = defaultdict(lambda: {"model_items": defaultdict(dict)})

#     for record in records:
#         model = record["model"]
#         item = record["item"]
#         alias = record["alias"]
#         alias_structure[model]['model_items'][item]['alias'] = alias

#     final_models = {}
#     for model_key, model_value in alias_structure.items():
#         model_value['model_items'] = dict(model_value['model_items'])
#         final_models[model_key] = model_value

#     return {"models": final_models}

def test51(): # 以 records 建構 dict
    bw = BuildingWorker()
    records = [
        {
            "model": "03dp",
            "item": "010",
            "alias": "10"
        },
        {
            "model": "03dp",
            "item": "018",
            "alias": "18"
        },
        {
            "model": "05tt",
            "item": "ah007",
            "alias": "ah7"
        }
    ]
    result = bw.build_alias(records)
    print(json.dumps(result, indent=4, ensure_ascii=False))
    # {
    #     "models": {
    #         "03dp": {
    #             "model_items": {
    #                 "010": {
    #                     "alias": "10"
    #                 },
    #                 "018": {
    #                     "alias": "18"
    #                 }
    #             }
    #         },
    #         "05tt": {
    #             "model_items": {
    #                 "ah007": {
    #                     "alias": "ah7"
    #                 }
    #             }
    #         }
    #     }
    # }

def test52():
    bw = BuildingWorker()
    records =[
        {
            "pattern": "^.{15}(10).+",
            "model": "03dp",
            "items": [
                "018",
                "028"
            ],
            "supply": "d"
        },
        {
            "pattern": "^.{15}(60).+",
            "model": "03dp",
            "items": [
                "045",
                "085"
            ],
            "supply": "d"
        },
        {
            "pattern": "^.{15}(80).+",
            "model": "05sr",
            "items": [
                "52"
            ],
            "supply": "n"
        }
    ]

    result = bw.build_supply(records) # 由 records 建構 runtime_supply
    print(json.dumps(result, indent=4, ensure_ascii=False))
    # {
    #     "models": {
    #         "03dp": {
    #             "model_items": {
    #                 "018": {
    #                     "runtime_pattern": {
    #                         "^.{15}(10).+": {
    #                             "supply": "d"
    #                         }
    #                     }
    #                 },
    #                 "028": {
    #                     "runtime_pattern": {
    #                         "^.{15}(10).+": {
    #                             "supply": "d"
    #                         }
    #                     }
    #                 },
    #                 "045": {
    #                     "runtime_pattern": {
    #                         "^.{15}(60).+": {
    #                             "supply": "d"
    #                         }
    #                     }
    #                 },
    #                 "085": {
    #                     "runtime_pattern": {
    #                         "^.{15}(60).+": {
    #                             "supply": "d"
    #                         }
    #                     }
    #                 }
    #             }
    #         },
    #         "05sr": {
    #             "model_items": {
    #                 "52": {
    #                     "runtime_pattern": {
    #                         "^.{15}(80).+": {
    #                             "supply": "n"
    #                         }
    #                     }
    #                 }
    #             }
    #         }
    #     }
    # }

def test53():
    bw = BuildingWorker()
    records = [
        {
            "pattern": "^.(010|018).+",
            "model": "03dp",
            "items": [
                "010",
                "018"
            ],
            "method": "-s"
        },
        {
            "pattern": "^.(050|070).+",
            "model": "08axv",
            "items": [
                "S1",
                "U1"
            ],
            "method": "-s"
        },
        {
            "pattern": "^.(038|042).+",
            "model": "08axv",
            "items": [
                "S2",
                "U2"
            ],
            "method": "-u"
        },
    ]

    result = bw.build_filter(records) # 由 records 建構 runtime_filter
    print(json.dumps(result, indent=4, ensure_ascii=False))
    # {
    #     "models": {
    #         "03dp": {
    #             "model_items": {
    #                 "015": {
    #                     "runtime_pattern": {
    #                         "^.(015|018).+": {
    #                             "display": true
    #                         }
    #                     }
    #                 },
    #                 "018": {
    #                     "runtime_pattern": {
    #                         "^.(015|018).+": {
    #                             "display": true
    #                         }
    #                     }
    #                 }
    #             }
    #         },
    #         "08axv": {
    #             "model_items": {
    #                 "S1": {
    #                     "runtime_pattern": {
    #                         "^.(050|070).+": {
    #                             "display": true
    #                         }
    #                     }
    #                 },
    #                 "U1": {
    #                     "runtime_pattern": {
    #                         "^.(050|070).+": {
    #                             "display": true
    #                         }
    #                     }
    #                 },
    #                 "S2": {
    #                     "runtime_pattern": {
    #                         "^.(038|042).+": {
    #                             "display": false
    #                         }
    #                     }
    #                 },
    #                 "U2": {
    #                     "runtime_pattern": {
    #                         "^.(038|042).+": {
    #                             "display": false
    #                         }
    #                     }
    #                 }
    #             }
    #         }
    #     }
    # }

def test54():
    bw = BuildingWorker()
    records =[
        {
            "index_0": "PA10V",
            "index_1": "O",
            "index_2": "018",
            "index_3": "00DRG",
            "index_4": "53",
            "index_5": "R",
            "index_6": "V",
            "index_7": "S2",
            "index_8": "A",
            "index_9": "12",
            "index_10": "N00",
            "index_11": "0"
        },
        {
            "index_0": "PA10V",
            "index_1": "O",
            "index_2": "028",
            "index_3": "00DRG",
            "index_4": "53",
            "index_5": "R",
            "index_6": "V",
            "index_7": "S3",
            "index_8": "A",
            "index_9": "12",
            "index_10": "N00",
            "index_11": "0"
        }
    ]

    result = bw.build_fast_model(records)
    print(result)

def test55():
    bw = BuildingWorker()
    records = [
        {
            "pattern": "^.{6}(010).+",
            "model": "08axv",
            "items": [
                "S1",
                "U1",
                "P1"
            ],
            "method": "-s"
        },
        {
            "pattern": "^.{6}(010).+",
            "model": "08axv",
            "items": [
                "S4",
                "U2",
                "S2",
                "R2",
                "U4",
                "W4",
                "R3",
                "S6",
                "W5",
                "S5",
                "R4",
                "W6",
                "U5",
                "U6",
                "S3",
                "P2",
                "R5"
            ],
            "method": "-u"
        }
    ]
    result = bw.build_disable(records)
    print(json.dumps(result, indent=4, ensure_ascii=False))

def test56():
    bw = BuildingWorker()
    records = [
        {'model': '05cr', 'item': 'R', 'image_path': 'images/moyb8typz89utpi8.jpg'},
        {'model': '05cr', 'item': 'L', 'image_path': 'images/3z41v0kuexyc5t9a.jpg'}
        ]
    result = bw.build_button_image(records)
    print(json.dumps(result, indent=4, ensure_ascii=False))
    # {
    #     "models": {
    #         "05cr": {
    #             "model_items": {
    #                 "R": {
    #                     "button_image": "images/moyb8typz89utpi8.jpg"
    #                 },
    #                 "L": {
    #                     "button_image": "images/3z41v0kuexyc5t9a.jpg"
    #                 }
    #             }
    #         }
    #     }
    # }

def test57():
    bw = BuildingWorker()
    records = [
        {'model': '03ct', 'custom_index': 'test_article'},
        {'model': '05cr', 'custom_index': 'yeoshe_article_rotation'},
        ]

    result = bw.build_model_help(records)
    print(json.dumps(result, indent=4, ensure_ascii=False))
    # {
    #     "models": {
    #         "03ct": {
    #             "model_help": "test_article"
    #         },
    #         "05cr": {
    #             "model_help": "yeoshe_article_rotation"
    #         }
    #     }
    # }

if __name__ == "__main__":
    test57()