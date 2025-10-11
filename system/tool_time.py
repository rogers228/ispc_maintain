from datetime import datetime, timezone

def get_local_time():
    # 適用 Supabase timestamp Data and time(not time zone) 不含時區資訊
    # 有時候顯示出來的格式會有所不同，是因為不同裝置，不同程式的處理方式不同
    # 但是儲存時接受的格式是統一的
    now_local = datetime.now() # 取得本地電腦的現在時間（沒有時區資訊）

    # 格式化為 PostgreSQL 接受的 YYYY-MM-DD HH:MI:SS 格式
    timestamp_str = now_local.strftime('%Y-%m-%d %H:%M:%S')
    return timestamp_str

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