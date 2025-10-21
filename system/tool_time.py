from datetime import datetime, timezone

def get_local_time():
    # 適用 Supabase timestamp Data and time(not time zone) 不含時區資訊
    # 有時候顯示出來的格式會有所不同，是因為不同裝置，不同程式的處理方式不同
    # 但是儲存時接受的格式是統一的
    now_local = datetime.now() # 取得本地電腦的現在時間（沒有時區資訊）

    # 格式化為 PostgreSQL 接受的 YYYY-MM-DD HH:MI:SS 格式
    timestamp_str = now_local.strftime('%Y-%m-%d %H:%M:%S')
    return timestamp_str

def get_mod_time(file_path):
    # 取得指定檔案的最後修改時間 (Mtime)，並格式化為 'YYYY-MM-DD HH:MI:SS' 字串。
    # 適用於 Supabase/PostgreSQL timestamp without time zone。
    # param file_path: 檔案的完整路徑。
    # return: 格式化後的時間字串，如果檔案不存在則返回 None。

    try:
        # 1. 取得檔案的最後修改時間戳 (秒數)。
        # 這個時間戳是基於本地時區的。
        timestamp = os.path.getmtime(file_path)

        # 2. 將時間戳轉換為 datetime 物件（fromtimestamp 預設使用本地時區）。
        mtime_local = datetime.fromtimestamp(timestamp)

        # 3. 格式化為 PostgreSQL 接受的 YYYY-MM-DD HH:MI:SS 格式
        timestamp_str = mtime_local.strftime('%Y-%m-%d %H:%M:%S')
        return timestamp_str

    except FileNotFoundError:
        print(f"錯誤：找不到檔案 {file_path}")
        return None
    except Exception as e:
        print(f"取得檔案修改時間時發生錯誤: {e}")
        return None

def get_local_time_tz():
    # 適用 timestamptz Data and time inclouding time zone 包含時區資訊
    now_utc = datetime.now(timezone.utc)

    # 將 datetime 物件格式化為 ISO 8601 字串
    # .isoformat() 會自動包含微秒和時區資訊 (+00:00) 秒級精度
    timestamp_str = now_utc.strftime('%Y-%m-%dT%H:%M:%S+00:00')
    return timestamp_str

def test1():
    print(get_local_time())
    # print(get_local_time_tz())

if __name__ == '__main__':
    test1()