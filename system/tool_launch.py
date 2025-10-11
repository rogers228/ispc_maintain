# 首次啟動程序

if True:
    import sys, os
    import json
    import win32com.client

    print("Python executable:", sys.executable, '\n') # 目前執行的python路徑 用來判斷是否是虛擬環境python 或 本機python

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
    PRIVATE_JSON = os.path.join(ROOT_DIR, "system", "private.json")

    sys.path.append(os.path.join(ROOT_DIR, "system"))
    from tool_gui import hide_cmd_window

def create_file():
    # 建立必要檔案
    print('建立必要檔案...')
    if not os.path.exists(PRIVATE_JSON):
        default = {}
        for key in ['email', 'password', 'full_name', 'ROOT_DIR']:
            default.setdefault(key, None)

        os.makedirs(os.path.dirname(PRIVATE_JSON), exist_ok=True)
        with open(PRIVATE_JSON, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=2)
        print('cteate private.json')

def create_shortcut():
    # 建立捷徑
    print('建立捷徑...')
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    shortcut_paths = [os.path.join(desktop, "ISPC.lnk"), os.path.join(ROOT_DIR, "ISPC.lnk")]
    for shortcut_path in shortcut_paths:
        if not os.path.exists(shortcut_path):
            print('create_shortcut...')
            target = os.path.join(ROOT_DIR, "bat", "main.bat")
            working_dir = ROOT_DIR
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortcut(shortcut_path)
            shortcut.TargetPath = target
            shortcut.WorkingDirectory = working_dir
            icon = os.path.join(ROOT_DIR, "system", "icons", "ispc.ico")  # 可選
            if os.path.exists(icon):
                shortcut.IconLocation = icon
            shortcut.save()
            print('create shortcut finished')

def init(): # 首次啟動程序
    print('主程式首次啟動 launch program...')
    create_file()     # 建立必要檔案
    create_shortcut() # 建立捷徑
    print('✅ 主程式啟動完成 launch finished')

def production_env_hide_cmd():
    # 若為生產環境 將隱藏命令視窗
    is_dev = True
    if not is_dev: # 若非開發環境則隱藏命令視窗
        hide_cmd_window()

if __name__ == '__main__':
    init()