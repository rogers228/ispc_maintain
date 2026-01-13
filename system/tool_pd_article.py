# tool_pd_article.py
# 專門處理 table rec_article

if True:
    import sys, os
    import requests
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
    from config_web import spwr_api_url, spwr_api_anon_key
    from tool_auth import AuthManager

class ProductArticle:

    def __init__(self):
        self.auth = AuthManager()
        self.table_url = f"{spwr_api_url}/rest/v1/rec_article"

    def _get_headers(self):
        if not self.auth.is_token_valid():
            print("Token 已過期，嘗試自動刷新...")
            self.auth.refresh_session()

        local_data = self.auth.load_local_data()
        jwt_token = local_data.get("jwt")

        return {
            "apikey": spwr_api_anon_key,
            "Authorization": f"Bearer {jwt_token}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"  # 讓 Insert/Update 回傳存檔後的資料
        }

    def select_multiple(self, query_params=None):
        """
        查詢多筆資料
        query_params: dict, 例如 {'custom_index': 'eq.manual-001'}
        """
        try:
            headers = self._get_headers()
            # select=* 代表抓取所有欄位
            res = requests.get(self.table_url, headers=headers, params=query_params)
            if res.status_code == 200:
                return res.json()
            else:
                print(f"Select Error: {res.status_code}, {res.text}")
                return []
        except Exception as e:
            print(f"Select Exception: {e}")
            return []

    def insert(self, custom_index, title, content, html_snapshot=None, category=None):
        """插入新文章"""
        user_id = self.auth.get_user_id()
        if not user_id:
            print("無法新增：找不到 User ID")
            return None

        payload = {
            "custom_index": custom_index,
            "title": title,
            "content": content,
            "html_snapshot": html_snapshot,
            "category": category,
            "author_id": user_id  # 必須對應當前登入者
        }

        try:
            headers = self._get_headers()
            res = requests.post(self.table_url, headers=headers, json=payload)
            if res.status_code in [201, 200]:
                return res.json()
            else:
                print(f"Insert Error: {res.status_code}, {res.text}")
                return None
        except Exception as e:
            print(f"Insert Exception: {e}")
            return None

    def update(self, custom_index, update_data):
        """
        更新文章
        custom_index: 標記要更新哪一筆
        update_data: dict, 例如 {"title": "新標題", "content": "新內容"}
        """
        try:
            headers = self._get_headers()
            # 使用 custom_index 作為過濾器
            params = {"custom_index": f"eq.{custom_index}"}
            res = requests.patch(self.table_url, headers=headers, params=params, json=update_data)
            if res.status_code in [200, 204]:
                return True
            else:
                print(f"Update Error: {res.status_code}, {res.text}")
                return False
        except Exception as e:
            print(f"Update Exception: {e}")
            return False

    def delete(self, custom_index):
        """刪除文章 (受 RLS 保護，只能刪除自己的)"""
        try:
            headers = self._get_headers()
            params = {"custom_index": f"eq.{custom_index}"}
            res = requests.delete(self.table_url, headers=headers, params=params)
            if res.status_code in [200, 204]:
                print(f"Delete Success: {custom_index}")
                return True
            else:
                # 如果 RLS 擋住，通常會回傳 204 但實際沒刪掉，或是報錯
                print(f"Delete Error/Denied: {res.status_code}, {res.text}")
                return False
        except Exception as e:
            print(f"Delete Exception: {e}")
            return False

def test1():
    print('test1')
    pa = ProductArticle()
    articles = pa.select_multiple()
    print("文章列表:", json.dumps(articles, indent=2, ensure_ascii=False))

def test2():
    pa = ProductArticle()
    res = pa.insert(
        custom_index="test-002",
        title="測試文章2",
        content="# Hello Markdown 2",
        html_snapshot="<h1>Hello Markdown</h1>",
        category="Maintenance"
    )
    if res:
        print("新增成功:", res)

def test3():
    pa = ProductArticle()
    success = pa.update("test-001", {"title": "修改後的標題"})
    if success:
        print("更新成功", success)

def test4():
    pa = ProductArticle()
    success = pa.delete("test-001")
    if success:
        print("刪除完成")
if __name__ == '__main__':
    test2()

