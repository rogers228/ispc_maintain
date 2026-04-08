# tool_db_snapshot.py
# 資檔案為副本，來源是 ispc_core/toolchain/snapshots/tool_db_snapshot.py
# 請同時修改


# 快照管理員 專門建立快照，供 ssr 爬蟲讀取
# 資料結構產參閱 ispc_blueprint cloudflare_database

import sys, os
import requests
from datetime import datetime
import json
import boto3
from botocore.client import Config

sys.path.append(os.getenv('GRST_PATH'))
from global_config import OPTION, current_base_path

class SnapshotManager:
    """
    ispc_snap 快照管理員
    負責與 Cloudflare D1 溝通，管理網頁路徑的快照狀態與 Sitemap 元數據。
    """
    def __init__(self):
        # --- D1 配置 ---
        self.account_id = OPTION.get('cloud_account_id')
        self.database_id = OPTION.get('ispc_main_db')
        self.api_token = OPTION.get('ispc_span_api_token')
        self.api_url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/d1/database/{self.database_id}/query"

        # --- R2 配置 ---
        self.r2_bucket = "ispc-r2-db"
        self.s3_client = boto3.client(
            's3',
            endpoint_url = OPTION.get('ispc_snap_r2_endpoint_url'),
            aws_access_key_id = OPTION.get('ispc_snap_r2_access_key_id'),
            aws_secret_access_key = OPTION.get('ispc_snap_r2_secret_access_key'),
            config=Config(signature_version='s3v4'),
            region_name='auto'
        )

        self.headers = {
            "Authorization": f"Bearer {self.api_token.strip()}",
            "Content-Type": "application/json"
        }

    def _format_path(self, path):
        """統一路徑格式為 /example/path (開頭有斜線，結尾沒斜線)"""
        if not path:
            return "/"
        # strip('/') 會去掉 " /zh/about/ " 前後的空格與所有斜線
        # 然後我們在前面補上一個標準的 /
        return "/" + path.strip().strip("/")

    def _path_to_key(self, path):
        """將網頁路徑轉換為 R2 的物件 Key"""
        path = self._format_path(path)
        clean_path = path.strip('/')
        if not clean_path: return "snapshots/index.html"
        return f"snapshots/{clean_path}.html"

    def put_object(self, path, html_content):
        """上傳 HTML 字串到 R2"""
        path = self._format_path(path)
        r2_key = self._path_to_key(path)
        try:
            self.s3_client.put_object(
                Bucket=self.r2_bucket,
                Key=r2_key,
                Body=html_content,
                ContentType='text/html'
            )
            print(f"🚀 [R2] 上傳成功: {r2_key}")
            return r2_key
        except Exception as e:
            print(f"❌ [R2] 上傳失敗: {str(e)}")
            return None

    def get_object(self, path):
        """依路徑從 R2 取得 HTML 字串"""
        path = self._format_path(path)
        r2_key = self._path_to_key(path)
        try:
            response = self.s3_client.get_object(Bucket=self.r2_bucket, Key=r2_key)
            # 將 StreamingBody 轉換為字串
            return response['Body'].read().decode('utf-8')
        except self.s3_client.exceptions.NoSuchKey:
            print(f"⚠️ [R2] 找不到檔案: {r2_key}")
            return None
        except Exception as e:
            print(f"❌ [R2] 讀取失敗: {str(e)}")
            return None

    # --- D1 原有方法 ---
    def _execute_sql(self, sql, params=None):
        """內部的 SQL 執行工具"""
        payload = {"sql": sql, "params": params or []}
        try:
            response = requests.post(self.api_url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"success": False, "errors": [str(e)]}

    def upsert_path(self, path, full_url):
        """
        [內容更新]：新增或標記路徑需要更新快照。
        會更新 data_updated_at，從而觸發快照工廠。
        """
        path = self._format_path(path)
        sql = """
        INSERT INTO rec_snapshot (path, full_url, data_updated_at, is_active)
        VALUES (?, ?, CURRENT_TIMESTAMP, 1)
        ON CONFLICT(path) DO UPDATE SET
            full_url = excluded.full_url,
            data_updated_at = CURRENT_TIMESTAMP,
            is_active = 1;
        """
        result = self._execute_sql(sql, [path, full_url])
        if result.get("success"):
            print(f"✅ [Upsert] 成功標記需快照路徑: {path}")
        else:
            print(f"❌ [Upsert] 失敗: {result.get('errors')}")
        return result

    def update_metadata(self, path, priority=None, changefreq=None, is_active=None):
        """
        [SEO 維護]：僅更新權重、頻率或開關，不觸發快照更新。
        """
        updates = []
        params = []

        if priority is not None:
            updates.append("priority = ?"), params.append(priority)
        if changefreq is not None:
            updates.append("changefreq = ?"), params.append(changefreq)
        if is_active is not None:
            updates.append("is_active = ?"), params.append(is_active)

        if not updates:
            return None

        sql = f"UPDATE rec_snapshot SET {', '.join(updates)} WHERE path = ?;"
        path = self._format_path(path)
        params.append(path)

        result = self._execute_sql(sql, params)
        if result.get("success"):
            print(f"✅ [Metadata] 成功更新元數據: {path}")
        return result

    def mark_snapshot_complete(self, path, r2_key, status=200):
        """
        [任務回報]：快照工廠拍完照後調用，同步時間戳以消掉待辦。
        """
        path = self._format_path(path)
        sql = """
        UPDATE rec_snapshot
        SET last_snapshot_at = CURRENT_TIMESTAMP,
            r2_key = ?,
            status = ?
        WHERE path = ?
        """
        result = self._execute_sql(sql, [r2_key, status, path])
        if result.get("success"):
            print(f"🎯 [Complete] 路徑快照已完成並同步: {path}")
        return result

    def get_pending_tasks(self):
        """
        [工廠取貨]：獲取所有資料已變動、但快照尚未更新的路徑清單。
        """
        sql = """
        SELECT path, full_url FROM rec_snapshot
        WHERE is_active = 1
          AND (last_snapshot_at IS NULL OR data_updated_at > last_snapshot_at);
        """
        result = self._execute_sql(sql)
        if result.get("success") and result.get("result"):
            return result["result"][0].get("results", [])
        return []

    def raw_query(self, sql, params=None):
        """
        [萬用查詢]：直接傳入 SQL 字串與參數進行查詢。
        回傳原始的結果列表。
        """
        result = self._execute_sql(sql, params)
        if result.get("success"):
            # D1 的回傳結構通常在 result[0]['results']
            return result.get("result", [{}])[0].get("results", [])
        else:
            print(f"❌ SQL 執行出錯: {result.get('errors')}")
            return []

def test1():
    sn = SnapshotManager()
    sn.upsert_path("/zh/about", "https://yourdomain.com/zh/about")

def test2():
    # 2. 調整 SEO 參數 (不重拍)
    sn = SnapshotManager()
    sn.update_metadata("/zh/about", priority=0.8)

def test3():
    sn = SnapshotManager()
    # 取得待處理任務清單 (這是一個 list of dictionaries)
    pending_tasks = sn.get_pending_tasks()

    print(f"📊 偵測到 {len(pending_tasks)} 個待處理任務")

    for task in pending_tasks:
        # 這裡的 key 對應 D1 資料表的欄位名稱
        path = task.get('path')
        url = task.get('full_url')

        print(f"---")
        print(f"📍 待處理路徑: {path}")
        print(f"🔗 目標網址: {url}")

        # 💡 這裡就是你之後要呼叫 Playwright 拍照的地方

def test4():
    sn = SnapshotManager()
    custom_sql = """
        SELECT id, path, full_url, priority, changefreq, data_updated_at, last_snapshot_at, status
        FROM rec_snapshot
        WHERE is_active = 1 AND
            (last_snapshot_at IS NULL OR data_updated_at > last_snapshot_at)
        ORDER BY id DESC"""
    rows = sn.raw_query(custom_sql)
    if not rows:
        print("no data!")
        return
    print(f"找到 {len(rows)} 筆符合條件的資料：")
    print("=" * 60)

    # 遍歷結果並印出
    for row in rows:
        # 印出一行簡短的資訊
        print(f"ID: {row.get('id')} | Path: {row.get('path')}")
        print(f"  - full_url: {row.get('full_url')}")
        print(f"  - priority: {row.get('priority')}")
        print(f"  - changefreq: {row.get('changefreq')}")
        print(f"  - data_updated_at: {row.get('data_updated_at')}")
        print(f"  - status: {row.get('status')}")
        print(f"  - last_snapshot_at: {row.get('last_snapshot_at')}")
        print("-" * 60)

def test5():
    # 上傳 R2 與 D1
    sn = SnapshotManager()
    path = "/zh/test-page"
    full_url = "https://yourdomain.com/zh/test-page" # 模擬原始網址
    content = "<html><body><h1>Hello World</h1><p>測試 R2 存取</p></body></html>"

    print(f"--- 開始測試路徑: {path} ---")

    # 1. 重要：先在 D1 建立/確保有這條路徑的紀錄 (Upsert)
    # 如果沒這步，後面的 mark_snapshot_complete 就會更新失敗
    print("1. 正在 D1 建立路徑紀錄...")
    upsert_res = sn.upsert_path(path, full_url)

    if not upsert_res.get("success"):
        print(f"❌ D1 建立紀錄失敗: {upsert_res.get('errors')}")
        return

    # 2. 嘗試上傳到 R2
    print("2. 正在嘗試上傳至 R2...")
    r2_key = sn.put_object(path, content)

    if r2_key:
        # 3. 嘗試從 R2 讀取回傳以驗證檔案存在
        print("3. 正在從 R2 驗證讀取...")
        fetched_content = sn.get_object(path)
        if fetched_content:
            print(f"✅ R2 讀取成功，內容長度: {len(fetched_content)}")

        # 4. 最關鍵：更新 D1 狀態 (填入 r2_key)
        # status 讀取網頁的狀態碼，用來判斷快照是否健康
        print("4. 正在更新 D1 狀態為 '已完成'...")
        complete_res = sn.mark_snapshot_complete(path, r2_key, status=200)

        if complete_res.get("success"):
            print(f"🎉 [成功] {path} 已經完整同步至 D1 與 R2！")
        else:
            print(f"❌ D1 更新狀態失敗: {complete_res.get('errors')}")
    else:
        print("❌ R2 上傳失敗，流程中斷。")

def test6():
    # 直接讀取 path 的內容
    sn = SnapshotManager()
    path = "/zh/test-page"
    html_content = sn.get_object(path)
    if html_content:
        print(f"📖 成功讀取快照內容！")
        print("-" * 30)
        print(html_content)  # 這就會印出 <html>...</html>
        print("-" * 30)
    else:
        print("📭 R2 中找不到該路徑的快照。")

def test7():
    # 查詢是否有快照 讀取 path 的快照內容
    # path = "/zh/test-page"
    sn = SnapshotManager()
    path = "zh/test-page" # 就算前方沒給斜線也沒關係
    target_path = sn._format_path(path)

    sql = "SELECT r2_key, last_snapshot_at, status FROM rec_snapshot WHERE path = ?"
    rows = sn.raw_query(sql, [target_path])

    if not rows:
        print(f"❌ D1 找不到任何關於 {path} 的紀錄。")
        return None

    # 檢查是否有 r2_key
    record = rows[0]
    if not record.get('r2_key'):
        print(f"⚠️ 找到紀錄，但 r2_key 是空的 (尚未拍照)。資料更新於: {record.get('data_updated_at')}")
        return None

    print(f"✅ 找到快照紀錄 (日期: {record['last_snapshot_at']}, 狀態: {record['status']})")
    html_content = sn.get_object(path)

    if html_content:
        print(f"📄 內容預覽 (前 50 字): {html_content[:50]}...")
    return html_content

def test8():
    # debug_show_all
    sn = SnapshotManager()
    # 抓出目前資料庫裡所有的路徑
    rows = sn.raw_query("SELECT id, path, r2_key FROM rec_snapshot")

    if not rows:
        print("📭 資料庫是空的！怪不得 test7 找不到。請先跑 test5。")
        return

    print(f"📊 目前資料庫共有 {len(rows)} 筆紀錄：")
    print("-" * 50)
    for row in rows:
        # 使用引號包起來，可以看出有沒有多餘的空格或斜線
        print(f"ID: {row['id']} | Path: [{row['path']}] | R2_Key: {row['r2_key']}")
    print("-" * 50)

if __name__ == '__main__':
    # test5()
    # test7()
    test8()


