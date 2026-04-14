# tool_db_snapshot.py
# 資檔案為副本，來源是 ispc_core/toolchain/snapshots/tool_db_snapshot.py
# 請同時修改，須注意此專案的引用方式有所不同，致使 __init__ 方式不同

# 快照管理員 專門建立快照，供 ssr 爬蟲讀取
# 資料結構產參閱 ispc_blueprint cloudflare_database

if True:
    import sys, os
    import requests
    from datetime import datetime
    import json
    import boto3
    from botocore.client import Config

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
    from config_web import SPECIC_DOMAIN, D1_CLOUD_ACCOUNT_ID, D1_ISPC_MAIN_DB, D1_ISPC_API_TOKEN, R2_ISPC_SNAP_ENDPOINT_URL, R2_ISPC_SNAP_ACCESS_KEY_ID, R2_ISPC_SNAP_SECRET_ACCESS_KEY

class SnapshotManager:
    """
    ispc_snap 快照管理員
    負責與 Cloudflare D1 溝通，管理網頁路徑的快照狀態與 Sitemap 元數據。
    """
    def __init__(self):
        # --- D1 配置 ---
        self.account_id = D1_CLOUD_ACCOUNT_ID
        self.database_id = D1_ISPC_MAIN_DB
        self.api_token = D1_ISPC_API_TOKEN
        self.api_url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/d1/database/{self.database_id}/query"

        # --- R2 配置 ---
        self.r2_bucket = "ispc-r2-db"
        self.s3_client = boto3.client(
            's3',
            endpoint_url = R2_ISPC_SNAP_ENDPOINT_URL,
            aws_access_key_id = R2_ISPC_SNAP_ACCESS_KEY_ID,
            aws_secret_access_key = R2_ISPC_SNAP_SECRET_ACCESS_KEY,
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

    def _path_to_key(self, path, device='desktop'):
        """將路徑轉換為 R2 Key，格式：snapshots/{device}/{path}.html"""
        path = self._format_path(path)
        clean_path = path.strip('/')
        if not clean_path:
            return f"snapshots/{device}/index.html"
        return f"snapshots/{device}/{clean_path}.html"

    def put_object(self, path, html_content, device='desktop'):
        """上傳 HTML 到 R2 指定裝置目錄"""
        path = self._format_path(path)
        r2_key = self._path_to_key(path, device)
        try:
            self.s3_client.put_object(
                Bucket=self.r2_bucket,
                Key=r2_key,
                Body=html_content,
                ContentType='text/html'
            )
            print(f"🚀 [R2] 上傳成功 ({device}): {r2_key}")
            return r2_key
        except Exception as e:
            print(f"❌ [R2] 上傳失敗 ({device}): {str(e)}")
            return None

    def get_object(self, path, device='desktop'):
        """從 R2 取得指定裝置的快照"""
        path = self._format_path(path)
        r2_key = self._path_to_key(path, device)
        try:
            response = self.s3_client.get_object(Bucket=self.r2_bucket, Key=r2_key)
            return response['Body'].read().decode('utf-8')
        except self.s3_client.exceptions.NoSuchKey:
            print(f"⚠️ [R2] 找不到檔案 ({device}): {r2_key}")
            return None
        except Exception as e:
            print(f"❌ [R2] 讀取失敗 ({device}): {str(e)}")
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

    # 註：建議 D1 table `rec_snapshot` 的 PRIMARY KEY 改為 (path, device)
    def upsert_path(self, path, full_url, device='desktop'):
        """標記特定裝置的路徑需要更新快照"""
        path = self._format_path(path)
        sql = """
        INSERT INTO rec_snapshot (path, full_url, device, data_updated_at, is_active)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP, 1)
        ON CONFLICT(path, device) DO UPDATE SET
            full_url = excluded.full_url,
            data_updated_at = CURRENT_TIMESTAMP,
            is_active = 1;
        """
        result = self._execute_sql(sql, [path, full_url, device])
        if result.get("success"):
            print(f"✅ [Upsert] 成功標記 ({device}): {path}")
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

    def mark_snapshot_complete(self, path, r2_key, status=200, device='desktop'):
        """回報特定裝置的快照任務完成"""
        path = self._format_path(path)
        sql = """
        UPDATE rec_snapshot
        SET last_snapshot_at = CURRENT_TIMESTAMP,
            r2_key = ?,
            status = ?
        WHERE path = ? AND device = ?
        """
        result = self._execute_sql(sql, [r2_key, status, path, device])
        if result.get("success"):
            print(f"🎯 [Complete] 快照已同步 ({device}): {path}")
        return result

    def delete_snapshot(self, path, device=None):
        """刪除快照。若 device 為 None，則刪除該路徑下所有裝置版本。"""
        path = self._format_path(path)
        devices_to_delete = [device] if device else ['desktop', 'mobile']
        results = {"d1": True, "r2": True}

        for d in devices_to_delete:
            r2_key = self._path_to_key(path, d)
            # 刪 R2
            try:
                self.s3_client.delete_object(Bucket=self.r2_bucket, Key=r2_key)
                print(f"🗑️ [R2] 已刪除 ({d}): {r2_key}")
            except Exception: pass

            # 刪 D1
            sql = "DELETE FROM rec_snapshot WHERE path = ? AND device = ?"
            res = self._execute_sql(sql, [path, d])
            if not res.get("success"): results["d1"] = False

        return results

    def get_pending_tasks(self):
        """獲取所有裝置版本中需要重拍的路徑"""
        sql = """
        SELECT path, full_url, device FROM rec_snapshot
        WHERE is_active = 1
          AND (last_snapshot_at IS NULL OR data_updated_at > last_snapshot_at);
        """
        result = self._execute_sql(sql)
        if result.get("success") and result.get("result"):
            # 注意：這裡會回傳包含 'device' 的 dict 列表
            return result["result"][0].get("results", [])
        return []

    def raw_query(self, sql, params=None):
        result = self._execute_sql(sql, params)
        if result.get("success"):
            return result.get("result", [{}])[0].get("results", [])
        return []

    def danger_wipe_all(self):
        # [危險操作] 刪除 R2 上的所有快照檔案並清空 D1 快照資料表。
        print("⚠️  正在啟動全面清理流程...")

        # 1. 清理 R2 (分批刪除 snapshots/ 下的所有物件)
        try:
            paginator = self.s3_client.get_paginator('list_objects_v2')
            # 僅鎖定 snapshots/ 目錄，避免誤刪其他資源
            pages = paginator.paginate(Bucket=self.r2_bucket, Prefix='snapshots/')

            delete_count = 0
            for page in pages:
                if 'Contents' in page:
                    objects_to_delete = [{'Key': obj['Key']} for obj in page['Contents']]
                    self.s3_client.delete_objects(
                        Bucket=self.r2_bucket,
                        Delete={'Objects': objects_to_delete}
                    )
                    delete_count += len(objects_to_delete)
            print(f"🗑️  [R2] 已從 Bucket 移除 {delete_count} 個快照檔案。")
        except Exception as e:
            print(f"❌ [R2] 清理失敗: {str(e)}")

        # 2. 清理 D1
        # 使用 DELETE 而非 TRUNCATE，因為 D1 主要是 SQLite 語法
        sql = "DELETE FROM rec_snapshot;"
        result = self._execute_sql(sql)

        if result.get("success"):
            print("✅ [D1] 快照紀錄資料表已清空。")
        else:
            print(f"❌ [D1] 清理失敗: {result.get('errors')}")

        return result


def test1():
    sn = SnapshotManager()
    pdno = 'e4eurcohcmyn'
    cono = 'yeoshe'
    for lang in ['en', 'zh-TW']:
        path = f'/{lang}/app/v/{cono}/p/{pdno}'
        target_path = sn._format_path(path)
        # print('target_path:', target_path)
        full_url = f'{SPECIC_DOMAIN}{target_path}'
        # print('full_url:', full_url)
        sn.upsert_path(target_path, full_url) # 標記後端 需要更新快照
        print('成功標記後端 需要更新快照:', target_path)

if __name__ == '__main__':
    test1()



