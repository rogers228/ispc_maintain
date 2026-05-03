# tool_storage.py
# 專門儲存檔案

if True:
    import sys, os
    import urllib.parse
    import requests
    from datetime import datetime, timezone

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

        # --- 擴充資料夾與 Content-Type 對應邏輯 ---
        if extension in ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.ico']:
            folder = "images"
            # 針對不同圖片格式給予精確 MIME Type
            mime_map = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
                        '.webp': 'image/webp', '.gif': 'image/gif', '.ico': 'image/x-icon'}
            content_type = mime_map.get(extension, "image/jpeg")

        elif extension == '.pdf':
            folder = "pdfs"
            content_type = "application/pdf"

        elif extension == '.md':
            folder = "markdowns"
            content_type = "text/markdown"

        elif extension == '.css':
            folder = "css"
            content_type = "text/css"

        elif extension == '.js':
            folder = "js"
            content_type = "text/javascript"

        elif extension == '.svg':
            folder = "images" # SVG 通常歸類在圖片
            content_type = "image/svg+xml"

        # --- 新增 PWA Manifest 支援 ---
        elif extension in ['.json', '.webmanifest']:
            # 如果檔名包含 manifest，使用專用 MIME Type
            if 'manifest' in file_name.lower():
                folder = "configs"
                content_type = "application/manifest+json"
            else:
                folder = "data"
                content_type = "application/json"

        elif extension in ['.woff', '.woff2', '.ttf', '.otf']:
            folder = "fonts"
            mime_map = {'.woff': 'font/woff', '.woff2': 'font/woff2',
                        '.ttf': 'font/ttf', '.otf': 'font/otf'}
            content_type = mime_map.get(extension, "font/woff2")

        elif extension in ['.zip', '.rar', '.7z']:
            folder = "archives"
            content_type = "application/zip"

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

    def query_storage(self, category=None, search_title=None, search_summary=None, content_type=None, limit=200):
        """
        查詢 rec_storage 資料表
        :param category: 篩選分類 (text)
        :param search_title: 標題關鍵字模糊搜尋
        :param search_summary: 簡介內容關鍵字模糊搜尋
        :param content_type: 可傳入字串 (單一篩選) 或 串列 (群組篩選)
        :param limit: 回傳筆數上限
        """
        auth_data = self.auth.load_local_data()
        jwt = auth_data.get("jwt")
        if not jwt:
            print("❌ 錯誤: 找不到 JWT。")
            return []

        # 1. 構建基礎 URL (最新上傳優先)
        fields = "id,title,file_path,content_type,file_size,summary,created_at"
        db_url = f"{spwr_api_url}/rest/v1/rec_storage?select={fields}&order=created_at.desc&limit={limit}"

        # 加入 content_type 精確篩選
        if content_type:
            if isinstance(content_type, list):
                # 如果是列表，轉成 Supabase 的 in.(item1,item2) 格式
                # 注意：如果 MIME 包含特殊字元，建議使用 urllib.parse.quote
                mimes_str = ",".join([f'"{m}"' for m in content_type]) # 加上雙引號處理特殊字元
                db_url += f"&content_type=in.({mimes_str})"
            else:
                # 原本的單一精確篩選
                db_url += f"&content_type=eq.{content_type}"

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

    def update_storage(self, db_id, data):
        """
        更新 rec_storage 表格內容
        :param db_id: UUID
        :param data: dict, 例如 {"title": "新標題", "summary": "新摘要"}
        """
        auth_data = self.auth.load_local_data()
        jwt = auth_data.get("jwt")
        if not jwt:
            print("❌ 錯誤: 找不到 JWT。請確認已登入。")
            return None

        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        headers = {
            "Authorization": f"Bearer {jwt}",
            "apikey": spwr_api_anon_key,
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }

        try:
            # 建立 PATCH 請求
            # headers 應包含你的 API Key 與 Auth Token (假設你類別內已有定義)
            url = f"{spwr_api_url}/rest/v1/rec_storage?id=eq.{db_id}"
            response = requests.patch(url, headers=headers, json=data)

            if response.status_code in [200, 201, 204]:
                print(f"✅ 資料庫更新成功: {db_id}")
                return True
            else:
                print(f"❌ 更新失敗: {response.status_code}, {response.text}")
                return False
        except Exception as e:
            print(f"🔥 update_storage 發生異常: {e}")
            return False

    def delete_storage(self, db_id):
        """
        連動刪除：1. 先取得路徑 2. 刪除資料庫紀錄 3. 呼叫獨立函數刪除雲端檔案
        """
        # 獲取 Auth 資訊
        auth_data = self.auth.load_local_data()
        jwt = auth_data.get("jwt")
        headers = {
            "Authorization": f"Bearer {jwt}",
            "apikey": spwr_api_anon_key,
            "Content-Type": "application/json"
        }

        try:
            # Step 1: 先查出該 ID 對應的 file_path
            query_url = f"{spwr_api_url}/rest/v1/rec_storage?select=file_path&id=eq.{db_id}"
            get_res = requests.get(query_url, headers=headers)

            if get_res.status_code != 200 or not get_res.json():
                print(f"❌ 找不到該筆資料 (ID: {db_id})，刪除終止")
                return False

            file_path = get_res.json()[0].get('file_path')
            print('file_path:', file_path)
            # Step 2: 刪除資料庫紀錄 (Table 'rec_storage')
            del_db_url = f"{spwr_api_url}/rest/v1/rec_storage?id=eq.{db_id}"
            db_res = requests.delete(del_db_url, headers=headers)

            if db_res.status_code not in [200, 204]:
                print(f"❌ 資料庫紀錄刪除失敗: {db_res.text}")
                return False

            # Step 3: 呼叫剛才測試成功的獨立函數刪除雲端檔案
            # 即使雲端刪除失敗，因為 DB 已經刪了，我們通常還是對 UI 回傳 True
            cloud_success = self.delete_assets_file(file_path)

            if cloud_success:
                print(f"🗑️ 資料庫與雲端檔案皆已刪除成功")
            else:
                print(f"⚠️ 資料庫已刪除，但雲端檔案實體刪除失敗 (請檢查後台)")

            return True

        except Exception as e:
            print(f"🔥 delete_storage 發生異常: {e}")
            return False

    def delete_assets_file(self, file_path):
        auth_data = self.auth.load_local_data()
        jwt = auth_data.get("jwt")

        # 刪除 API 的 Endpoint 是 bucket 名稱結尾
        url = f"{spwr_api_url}/storage/v1/object/assets"

        headers = {
            "Authorization": f"Bearer {jwt}",
            "apikey": spwr_api_anon_key,
            "Content-Type": "application/json" # 必須加這行
        }

        # 將路徑放入 prefixes 列表中
        payload = {"prefixes": [file_path]}

        try:
            # print(f"📡 正在請求批次刪除: {file_path}")
            res = requests.delete(url, headers=headers, json=payload)

            if res.status_code in [200, 204]:
                print(f"✅ 雲端檔案刪除成功: {file_path}")
                return True
            else:
                print(f"❌ 錯誤內容: {res.json()}")
                return False
        except Exception as e:
            print(f"🔥 異常: {e}")
            return False

def test1():
    print('test upload_file...')
    sb = StorageBuckets()
    # file = r'C:\Users\user\Desktop\temp\pump.jpg'
    file = r'C:\Users\USER\Documents\ispc_portal\web_lab\public\mock\test.md'
    result = sb.upload_file(file)
    print(result)

def test2():
    sb = StorageBuckets()
    # 測試：搜尋標題包含 "pump" 且限量 5 筆的資料
    results = sb.query_storage(search_title="", limit=100)
    print(results)
    # for item in results:
    #     print(f"ID: {item['id']} | Title: {item['title']} | Path: {item['file_path']}")

def test3():
    print('test_update...')
    sb = StorageBuckets()
    uid = '3c1d0b29-7ecd-47e8-9616-69f033452255'
    sb.update_storage(uid, {"title": "測試更新標題", "summary": "這是新的摘要"})

def test4():
    print('test_delete...')
    sb = StorageBuckets()
    uid = '6cecf5e2-aa6e-43c1-8827-2c92024edb26'
    # images/zhyrebdn2icoobpk.jpg
    sb.delete_storage(uid)

def test5():
    print('test_delete...')
    sb = StorageBuckets()
    test_path = "images/8awqy8gepnc2bily.jpg"
    result = sb.delete_assets_file(test_path)
    print(result)
    print(f"測試結果: {'成功' if result else '失敗'}")

if __name__ == '__main__':
    test1()
    # test4()
