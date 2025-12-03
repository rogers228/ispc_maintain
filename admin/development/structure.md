# 資料結構

## rec_option

| 名稱          |類型        |說明               |
| --            | --        |--                 |
| id            | uuid      |                   |
| options       | jsonb     | 轉為json前端讀取用     |
| original      | text      | 原始檔編輯用       |
| original_hash | varchar   | 原始檔hash值 |
| last_time     | timestamp | 最後時間           | 

## rec_pd

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
| source_id     | uuid      | 來源id  工作預覽版無來源，   正式版的來源為預覽版， target紀錄在options |

## use_type

工作預覽版 > 正式版 < 備份副本版(可復原正式版)

1. 工作預覽版 非正式上線，僅供內部預覽，為資料的第一層確認保護
2. 正式版，由預覽版發布，data_json覆蓋過來 last_time，edit_user

