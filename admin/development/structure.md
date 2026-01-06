# supabase_資料結構

## rec_option

| 名稱          |類型        |說明               |
| --            | --        |--                 |
| id            | uuid      |                   |
| options       | jsonb     | 轉為json前端讀取用  |
| original      | text      | 原始檔編輯用       |
| original_hash | varchar   | 原始檔hash值       |
| last_time     | timestamp | 最後時間           | 

## rec_pd
產品工作預覽版，具有gui介面

| 名稱          |類型        | 說明                                      |
| --            | --        |--                                         |
| id            | uuid      | pk                                        |
| pdno          | varchar   | 自訂的產品編號，系統管理者識別用 不做連結用途 |
| name          | varchar   | 產品名稱，系統管理者識別用                  |
| data_original | text      | 產品資料 輸入 (僅工作預覽版會有original)    |
| data_json     | jsonb     | 產品資料 轉換                              |
| data_hash     | varchar   | 用來檢查dirty (僅工作預覽版有data_hash)     |
| last_time     | timestamp | 最後時間 用來記錄最後更新的時間，所有版都有   |
| edit_user     | varchar   | 最後上傳者，發布者                          |
| version       | varchar   | 版本，PL/pgSQL 自動產生，固定格式 1-20251002 用來識別，只要有更新即往上升版|

### 注意事項
version 由 supabase database functions 觸發before 事件，自動更新

## rec_pd_release
產品發布，無gui介面

| id            | uuid      | pk   同 rec_pd.id                            |
| release_user  | varchar    |  發布者                                      |
| release_time  | timestamptz | 發布時間                                   |
| data_json     | jsonb       | 產品資料                             |
| version       | varchar     | 版本                                 |
| build_state   | int2      | netlify-ssg 雲端編譯為靜態js檔案  狀態碼   0或不需要 1需要部屬 2部屬完畢 3 ssg編譯中 7部屬失敗 ，netlify-ssg編譯後更新為2   |
| build_time    | timestamptz | netlify-ssg 雲端編譯為靜態js檔案的完成時間    |

### 注意事項
1. 由 ispc_maintain 後台使用者選擇產品後，按下發布按鈕，寫入更新 rec_pd_release.id, release_user, release_time，及 build_state=1
2. database functions 設定 befure update 自動更新複製 data_json, version 來源是table rec_pd 相同id的data_json, version
3. 資料寫入成功後，由ispc_maintain 向 netlify build hook 發起請求執行 build
4. netlify build 將執行netlify-ssg.py 讀取rec_pd_release.build_state=1 的資料進行ssg，新更新build_state=3最後更新 build_state=2, build_time


## rec_storage
| id                  | uuid default gen_random_uuid() primary key |
| title               | text not null        | 顯示的標題 |
| file_path           | text not null unique | Bucket 裡的完整路徑 (例如: pdfs/test.pdf) |
| summary             | text                 | 摘要
| category            | text                 | 分類 :報表、小說   |
| file_size           | bigint,              | 檔案大小 (bytes) |
| content_type        | text,                | MIME 類型        |
| created_by          | uuid references auth.users(id)   | -- 紀錄是哪個使用者上傳的
| created_at          | timestamptz default now()        |
| updated_at          | timestamptz default now()        |

## buckets assets 
目前是僅允許驗證過才能讀取
是因為要使用 Cloudflare Workers (CFW) 作為代理，然後就能讓所有人查看