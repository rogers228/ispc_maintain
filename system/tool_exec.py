if True:
    import sys, os

    def find_project_root(start_path=None, project_name="ispc_maintain"):
        if start_path is None:
            start_path = os.path.dirname(os.path.abspath(sys.argv[0]))
        current = start_path
        while True:
            if os.path.basename(current) == project_name:
                return current
            parent = os.path.dirname(current)
            if parent == current:
                raise FileNotFoundError(f"找不到專案 root (資料夾名稱 {project_name})")
            current = parent

    ROOT_DIR = find_project_root()

def exec_python(content):
    # 嘗試執行 Python 程式碼字串，並捕捉語法或其他運行時錯誤。
    # 若成功，返回包含執行結果的 local_vars 字典；若失敗，列印錯誤訊息並返回 None。
    local_vars = {}
    try:
        exec(content, {}, local_vars)
        return local_vars

    except SyntaxError as e: # 專門處理語法錯誤，這是配置檔案最常見的錯誤
        print(f"❌ 語法錯誤: {e}")
        return None

    except Exception as e: # 處理其他運行時錯誤 (例如 NameError, TypeError 等)
        print(f"⚠️ 警告：運行時錯誤: {e}")
        return None

def test1():
    print('test1')
    file = os.path.join(ROOT_DIR, 'admin', 'temp_options.py')
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()

    local_vars = exec_python(content)
    if local_vars is None:
        return
    else:
        print(local_vars)

if __name__ == '__main__':
    test1()