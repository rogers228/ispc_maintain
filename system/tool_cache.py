# tool_cache.py
# 以本地快取檔案 來 做檢查

if True:
    import sys, os
    import json

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
    from config import ISPC_MAINTAIN_CACHE_DIR

class Cache_article:

    def __init__(self):
        article_cache_file = os.path.join(ISPC_MAINTAIN_CACHE_DIR, "last_article_query.json") # 本地 article 查詢結果

        if not os.path.exists(article_cache_file):
            raise FileNotFoundError(f"找不到 {article_cache_file}")

        try:
            with open(article_cache_file, 'r', encoding='utf-8') as f:
                self.article_cache = json.load(f).get("results", []) # record
        except Exception as e:
            print(f"❌ 解析文章快取失敗: {e}")

        # 轉 map
        # dict  {
        #     custom_index: {},
        #     custom_index {},
        # }
        # 比較好檢查
        self.article_cache_map = {e.get('custom_index'): e for e in self.article_cache if e.get('custom_index')}

    def get_article_cache(self):
        # list record  [{},{},...]
        return self.article_cache

    def get_article_cache_map(self):
        return self.article_cache_map

    def get_article(self, custom_index):
        return self.article_cache_map.get(custom_index, None)

    def is_article_verify(self, custom_index):
        # 是否驗證通過
        # 是否在快取資料中 找的到文章
        return custom_index in self.article_cache_map


class Cache_file:

    def __init__(self):

        cache_file = os.path.join(ISPC_MAINTAIN_CACHE_DIR, "last_query.json") # 本地 article 查詢結果

        if not os.path.exists(cache_file):
            raise FileNotFoundError(f"找不到 {cache_file}")

        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                self.file_cache = json.load(f).get("results", []) # record
        except Exception as e:
            print(f"❌ 解析文章快取失敗: {e}")

        # 比較好檢查
        self.file_cache_map = {e.get('file_path'): e for e in self.file_cache if e.get('file_path')}

    def get_file_cache(self):
        # list record  [{},{},...]
        return self.file_cache

    def get_file_cache_map(self):
        return self.file_cache_map

    def get_file(self, file_path):
        return self.file_cache_map.get(file_path, None)

    def is_file_verify(self, file_path):
        # 是否驗證通過
        # 是否在快取資料中 找的到檔案
        return file_path in self.file_cache_map


def test1():
    cha = Cache_article()
    # article_cache_map = cc.get_article_cache_map()
    # print(json.dumps(article_cache_map, indent=4, ensure_ascii=False))

    target_id = 'ys_0023'
    if cha.is_article_verify(target_id):
        print(f'{target_id} 有文章')
        print(cha.get_article(target_id))
    else:
        print(f'{target_id} 無此文章')


def test2():
    chf = Cache_file()
    # files = chf.get_file_cache_map()
    # print(json.dumps(files, indent=4, ensure_ascii=False))

    file_path = "images/to2ojedgbhbguewr.jpg"

    if chf.is_file_verify(file_path):
        print(f'{file_path} 有檔案')
        print(chf.get_file(file_path))
    else:
        print(f'{file_path} 無此檔案')


if __name__ == '__main__':
    test2()
