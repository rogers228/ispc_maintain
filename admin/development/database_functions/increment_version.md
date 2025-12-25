# 說明
新增或編輯資料前，自動更新版本號。


## increment_version
```sql
DECLARE
    -- 用於存放從舊版本號中解析出來的數字部分
    old_version_number INTEGER := 0;
    -- 用於存放當前日期部分 (格式 YYYYMMDD)
    current_date_str TEXT := to_char(CURRENT_TIMESTAMP, 'YYYYMMDD');
BEGIN
    -- --------------------------------------------------
    -- 處理 INSERT (新增資料)
    -- --------------------------------------------------
    IF TG_OP = 'INSERT' THEN
        -- 新增時，版本號從 1 開始
        NEW.version := '1-' || current_date_str;
    
    -- --------------------------------------------------
    -- 處理 UPDATE (更新資料)
    -- --------------------------------------------------
    ELSIF TG_OP = 'UPDATE' THEN
        -- 只有當舊版本號不為空時才嘗試解析和遞增
        IF OLD.version IS NOT NULL THEN
            BEGIN
                -- 嘗試從 OLD.version 中解析出數字部分 (在第一個 '-' 之前)
                old_version_number := split_part(OLD.version, '-', 1)::INTEGER;
            EXCEPTION
                -- 如果解析失敗 (例如: 舊版本號格式不符 'N-YYYYMMDD')，從 0 開始計算
                WHEN invalid_text_representation THEN
                    old_version_number := 0;
            END;

            -- 升級版本號並重新組合 (N+1-YYYYMMDD)
            NEW.version := (old_version_number + 1)::text || '-' || current_date_str;
        ELSE
            -- 如果舊版本號為 NULL，則從 1 開始
            NEW.version := '1-' || current_date_str;
        END IF;
    END IF;

    -- 返回 NEW 行數據，PostgreSQL 會使用這個修改後的 NEW 數據來完成操作
    RETURN NEW;
END;
```

# 說明

database functions 
名稱increment_version
用來自動更新版本號，當使用者更新資料後，會自動更新版本號。

database trigger
名稱 auto_version_increment_trigger
事件 before update, before insert

於 supabase dashboard 設定
