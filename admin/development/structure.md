# 資料結構

## rec_option

|名稱    |類型   |說明  |
|id      |uuid  |     |
|options |jsonb |     |


## rec_pd

| 名稱        |類型   |說明  |
| id          |uuid   | pk    |
| name        |varchar| 產品名稱 |
| pdno        |varchar|     |
| type        |int2   | 0未設定 1預覽版 2正式版  |
| data_input  |text   | 輸入資料 |
| data_json   |jsonb  | 轉換資料 |
| data_hash   |varchar| data_input的 hash 用來檢查dirty     |
| last_time   |timestamp | 最後時間                         |
| edit_user   |varchar   | 最後編輯者                       |
| release_id  |uuid   | 發布資料  預覽版發布至正式版的id    |

