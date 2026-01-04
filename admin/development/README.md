# InfoSpec（資訊規格系統）
資訊化的商品規格，縮寫：ISPC
核心價值在於解決「工業品/客製化商品」在數位轉型中，規格複雜導致難以線上自動化溝通的問題。

1. 專為商品建立詳細的商品說明
2. 專為商品賦予詳細的規格型號，做為顧客與製造商共同的商品描述語言，同時以此為基石推動後續的數位化、自動化。
3. 具有Web介面、面相使用者，提供商品敘述、規格查詢、選購。
4. 具有商家winform介面，面對製造商，提供報價、資訊維護、即時更新。使用資訊數位化帶來全世界的商機。
5. 具有專門的規格維護後台，可處理規格屬性之間的互相禁用，(例如iphone具有max功能就不能選擇air機型)

## ispc_maintain
1. 專門用來維護資料的後台，python pyqt5 winform專案。
2. 採用github專案，自動更新

## ispc_svelte 專案
1. ispc_svelte 為InfoSpec（資訊規格系統）的子專案，專門處理website介面
2. 不同於企業網站，它專注於產品型號的選擇面板介面，提供使用者一個產品選擇器面板。
3. 不同於購物平台，它不提供購買，下單服務。
4. 它只提供了選擇介面，讓使用者對商家(製造商、工廠)提出線上詢價，由系統轉發email，橋接買賣雙發，ispc_svelte不再介入買賣行為。
5. ispc_svelte 不做重複的、已經有的事情。
6. 它主要為企業提供了一般企業網站無法做到的，"正確的選擇型號繼並提出詢價"，的工具。
7. 做為一個webapp，也能授權使用iframe鑲入於介業網站。
8. ispc_svelte 主要客戶來源為，已經具有企業網站，或無網站，處於產品無法輕易銷售的困境的企業。

## data
產品資料有分生產用資料，測試資料，備份資料
生產用資料必須經過測試資料

## 工作方式規劃
gui操作 雲端產品資料下載至本地，使用者有權限管制，僅能讀取授權的資料
gui操作 使用sublime開啟編輯，儲存
gui操作 檢查 => 通過檢查
gui操作 上傳測試版 (可實際預覽)
gui操作 將測試版正式發布


# 全端規劃

## 產品資料(後端)
1. 後端採用pyqt5 gui，進行操作
2. 產品資料是spa中要讀取的資料，欄位有uuid(key)，pdno(產品編號)，content(json)，version(格式未定)
3. 產品資料分為預覽版(開發用)與正式版(生產用)，採用兩筆資料，(uuid不同，pdno相同)
4. 預覽版(開發用)的資料由後端編輯後，驗證後上傳supabase，供開發者預覽，檢查是否正確。
5. 正式版(生產用)的資料由預覽版(開發用)，驗證後正式發布(content, version 資料覆蓋)。
6. 每次正式發布後產生config.js，此內容記錄所有資料的version(包含預覽版與正式版)。
7. spa index.html的 head 更新 <script type="text/javascript" src="./config.js?version=random">
8. 更新靜態檔案，index.html, config.js，讓瀏覽器直接讀取所有正式版的version，不需要讀取supabase

## 前端
1. spa 讀取時採用url hash，例如'https://example.com/#/info?uuid=example'
2. 預覽版(開發用)的uuid與正式版(生產用)的uuid是不相同，使得兩種版本可以同時存在，用戶與開發者互不干擾。
3. 以uuid讀取本地資料的version與config.js的version，比較版本。
4. 若版本相同則使用本地indexedDB資料 (本地版本最多與雲端版本相同)
5. 若雲端版本較新，則讀取supabase資料，存入本地indexedDB。
6. 統一使用indexedDB資料來更新store
7. svelte spa 採用{@attach} 響應式系統，stroe更新後直接驅動ui。