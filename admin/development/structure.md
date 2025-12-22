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
產品工作預覽版

| 名稱          |類型        | 說明                                      |
| --            | --        |--                                         |
| id            | uuid      | pk                                        |
| pdno          | varchar   | 自訂的產品編號，系統管理者識別用 不做連結用途 |
| name          | varchar   | 產品名稱，系統管理者識別用                  |
| use_type      | int2      | 使用用途 0未設定 1預覽版 2正式版            |
| data_original | text      | 產品資料 輸入 (僅工作預覽版會有original)    |
| data_json     | jsonb     | 產品資料 轉換                              |
| data_hash     | varchar   | 用來檢查dirty (僅工作預覽版有data_hash)     |
| last_time     | timestamp | 最後時間 用來記錄最後更新的時間，所有版都有   |
| edit_user     | varchar   | 最後上傳者，發布者                          |
| version       | varchar   | 版本，PL/pgSQL 自動產生，固定格式 1-20251002 用來識別，只要有更新即往上升版|
| source_id     | uuid      | 來源id  工作預覽版的部屬為正式版的目標id | 正式版的發布來源id |

## 預計廢除欄位 use_type, source_id

## rec_pd_release
產品正式發布版，由rec_pd min壓縮而來
| id            | uuid      | pk   同 rec_pd                            |
| data_json     | jsonb     | 產品資料 轉換 mis                          |
| version       | varchar   | 版本                                      |
| build_state   | int2      | 0無或不需要  1需要SSG部屬版本  給SSG查詢用   |
