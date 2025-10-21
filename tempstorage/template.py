# 此檔案為範本

# 以下註解 section system 字符不可刪除，給 re 正則比對使用
# 儲存成功後會回寫 system，與雲端相同資料
# 故 system dict 就代表上一次上傳的資訊
# 用來判斷
# 使用者不要編輯

if True: # -----section system start-----
    system = {
        'data_hash': 'test',
        'last_time': 'test',
        'edit_user': 'test',
    }
    # -----section system end-----

specification = {

}

def test1():
    print(system)

if __name__ == '__main__':
    test1()