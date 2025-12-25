# 說明
同步更新 data_json, version

```sql

BEGIN
    -- 只有當 build_state 為 1 (需要編譯) 時才執行搬運，節省效能
    IF NEW.build_state = 1 THEN
        -- 從原始產品表抓取資料並直接賦值給 NEW 物件
        SELECT data_json, version 
        INTO NEW.data_json, NEW.version
        FROM rec_pd
        WHERE id = NEW.id;

        -- 防呆機制：如果 rec_pd 找不到這筆資料
        IF NOT FOUND THEN
            RAISE EXCEPTION '找不到原始產品資料 (ID: %)，無法發布', NEW.id;
        END IF;
    END IF;

    RETURN NEW;
END;

```

事件
BEFORE UPDATE
BEFORE INSERT