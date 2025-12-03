# 自動更新版本號

自動更新 rec_pd.version
使用pg sql

```
-- ==========================================================
-- 步驟 1: 建立或取代 (CREATE OR REPLACE) PL/pgSQL 函式
-- 函式名稱: increment_version
-- 目的: 計算並設定 rec_pd 表格的 version 欄位
-- ==========================================================
CREATE OR REPLACE FUNCTION public.increment_version()
RETURNS trigger AS $$
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
$$ LANGUAGE plpgsql SECURITY DEFINER;
-- 使用 SECURITY DEFINER 確保函式有足夠權限執行操作

-- ==========================================================
-- 步驟 2: 建立觸發器 (CREATE TRIGGER)
-- 目的: 在 rec_pd 表的每次 INSERT 或 UPDATE 之前呼叫函式
-- ==========================================================
-- 假設您的表格名稱是 public.rec_pd
CREATE OR REPLACE TRIGGER auto_version_increment_trigger
BEFORE INSERT OR UPDATE ON public.rec_pd
FOR EACH ROW EXECUTE FUNCTION public.increment_version();
```

## 尋找觸發器
```
SELECT
    t.tgname AS trigger_name,
    c.relname AS table_name,
    pg_get_triggerdef(t.oid) AS definition
FROM
    pg_trigger t
JOIN
    pg_class c ON t.tgrelid = c.oid
WHERE
    c.relname = 'rec_pd' -- 鎖定您的目標表格
    AND t.tgisinternal = FALSE;
```