import tempfile
import subprocess
import os


def test1():
    # 檔案內容
    # 未來讀取 db
    content_file = '''
test line1
test line2
'''
    # 將內容存成暫存檔
    # 使用sublime text 開啟暫存檔

    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8") as tmp_file:
        tmp_file.write(content_file)
        temp_path = tmp_file.name

    print(f"暫存檔已建立: {temp_path}")

    # 嘗試使用 Sublime Text 開啟
    try:
        subprocess.Popen(["subl", temp_path], shell=True)  # 假設已把 `subl` 加入 PATH
    except FileNotFoundError:
        print("找不到 Sublime Text，請確認 `subl` 指令已加入環境變數。")





if __name__ == '__main__':
    test1()