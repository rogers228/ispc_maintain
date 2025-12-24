# supabase_資料結構

## rec_option

| 名稱          |類型        |說明               |
| --            | --        |--                 |
| id            | uuid      |                   |
| options       | jsonb     | 轉為json前端讀取用     |
| original      | text      | 原始檔編輯用       |
| original_hash | varchar   | 原始檔hash值 |
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
產品正式發布版，無gui介面

可發起請求 netlify build ssg
| id            | uuid      | pk   同 rec_pd.id                            |
| data_json     | jsonb     | 產品資料 轉換 mis                             |
| version       | varchar   | 版本  跟隨預覽版                              |
| build_state   | int2      | netlify-ssg 雲端編譯為靜態js檔案  狀態碼   0或不需要 1需要部屬 2部屬完畢 7部屬失敗 ，netlify-ssg編譯後更新為2   |
| build_time    | timestamp | netlify-ssg 雲端編譯為靜態js檔案的完成時間    |

### 注意事項
data_json 由rec_pd.data_json min壓縮而來，
version 跟隨預覽版
build_state 由 ispc_maintain 寫入0或1 由 netlify-ssg寫入2或7
build_time 由 netlify-ssg寫入
