# tool_storage.py
# 專門儲存檔案

if True:
    import sys, os
    import requests

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
    from tool_str import generate_random_char_lower

class StorageBuckets:

    def __init__(self):
        self.auth = AuthManager()

    def upload_file(self, local_file_path, title=None, summary=''):
        auth_data = self.auth.load_local_data()
        jwt = auth_data.get("jwt")
        if not jwt:
            print("❌ 錯誤: 找不到 JWT。請確認已登入。")
            return None

        user_id = self.auth.get_user_id()
        if not user_id:
            print("❌ 無法取得使用者 ID，請重新登入")
            return None

        file_name = os.path.basename(local_file_path) # 包含附檔名
        final_title = title if title else file_name # title

        extension = os.path.splitext(file_name)[1].lower() # 附檔名
        if extension == '.pdf':
            folder = "pdfs"
            content_type = "application/pdf"
        elif extension in ['.jpg', '.jpeg', '.png', '.webp']:
            folder = "images"
            content_type = "image/jpeg" # 或根據副檔名精確判斷
        else:
            folder = "others"
            content_type = "application/octet-stream"

        dest_path = f"{folder}/{generate_random_char_lower(length=16)}{extension}"

        bucket_name = "assets"
        upload_url = f"{spwr_api_url}/storage/v1/object/{bucket_name}/{dest_path}"

        headers = {
            "Authorization": f"Bearer {jwt}",
            "apikey": spwr_api_anon_key,
            "Content-Type": content_type,
            "x-upsert": "true"  # 如果檔案已存在則覆蓋，不想覆蓋可設為 false
        }

        try:
            with open(local_file_path, 'rb') as f: # 讀取二進位檔案並發送 PUT 請求
                file_data = f.read()

            print(f"🚀 正在上傳至: {dest_path} ...")
            response = requests.post(upload_url, headers=headers, data=file_data)

            if response.status_code == 200:
                print(f"檔案已存入 Storage，正在寫入資料...")

                # 準備寫入資料庫的內容
                db_url = f"{spwr_api_url}/rest/v1/rec_storage"
                db_headers = {
                    "Authorization": f"Bearer {jwt}",
                    "apikey": spwr_api_anon_key,
                    "Content-Type": "application/json",
                    "Prefer": "return=minimal" # 告訴伺服器寫入後不需要回傳完整資料
                }

                db_payload = {
                    "title": final_title,
                    "file_path": dest_path, # 這是對應 Bucket 的關鍵路徑
                    "created_by": user_id,
                    "summary" : summary,
                    "category": None,     # array
                    "file_size": len(file_data),
                    "content_type": content_type
                }

                db_res = requests.post(db_url, headers=db_headers, json=db_payload)

                if db_res.status_code in [201, 200]:
                    print("✅ 資料庫紀錄已同步建立！")
                else:
                    print(f"❌ 資料庫寫入失敗: {db_res.text}")

            else:
                print(f"❌ 上傳失敗。狀態碼: {response.status_code}")
                print(f"錯誤訊息: {response.text}")
                return None

        except Exception as e:
            print(f"💥 發生異常: {e}")
            return None

    def query_storage(self, category=None, search_title=None, search_summary=None, limit=200):
        """
        查詢 rec_storage 資料表
        :param category: 篩選分類 (text)
        :param search_title: 標題關鍵字模糊搜尋
        :param search_summary: 簡介內容關鍵字模糊搜尋
        :param limit: 回傳筆數上限
        """
        auth_data = self.auth.load_local_data()
        jwt = auth_data.get("jwt")
        if not jwt:
            print("❌ 錯誤: 找不到 JWT。")
            return []

        # 1. 構建基礎 URL (最新上傳優先)
        db_url = f"{spwr_api_url}/rest/v1/rec_storage?select=*&order=created_at.desc&limit={limit}"

        # 2. 加入分類篩選 (針對 Array 欄位)
        # if category and category != "全部": # 假設 "全部" 是你不篩選的預設值
        #     db_url += f"&category=cs.{{ {category} }}"

        # 3. 加入標題模糊搜尋 (ilike)
        if search_title:
            db_url += f"&title=ilike.*{search_title}*"

        # 4. 加入簡介模糊搜尋 (ilike)
        if search_summary:
            db_url += f"&summary=ilike.*{search_summary}*"

        headers = {
            "Authorization": f"Bearer {jwt}",
            "apikey": spwr_api_anon_key,
            "Content-Type": "application/json"
        }

        try:
            print(f"🔍 正在發送請求: {db_url}")
            response = requests.get(db_url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                print(f"✅ 成功取得 {len(data)} 筆紀錄")
                return data
            else:
                print(f"❌ 查詢失敗: {response.status_code} - {response.text}")
                return []

        except Exception as e:
            print(f"💥 查詢發生異常: {e}")
            return []
def test1():
    print('test upload_file...')
    sb = StorageBuckets()
    file = r'C:\Users\user\Desktop\temp\pump.jpg'
    result = sb.upload_file(file)
    print(result)

def test2():
    sb = StorageBuckets()
    # 測試：搜尋標題包含 "pump" 且限量 5 筆的資料
    results = sb.query_storage(search_title="", limit=5)
    print(results)
    # for item in results:
    #     print(f"ID: {item['id']} | Title: {item['title']} | Path: {item['file_path']}")

if __name__ == '__main__':
    # test1()
    test2()
