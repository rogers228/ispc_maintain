# 正常啟動程序

if True:
    import sys, os
    from git import Repo, GitCommandError
    import subprocess
    import multiprocessing

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
    CONFIG = os.path.join(ROOT_DIR, "bat", "config.txt")

    def config_to_dict(file_path = CONFIG):
        config = {}
        if not os.path.exists(file_path):
            print(f"🔴 錯誤：找不到設定檔於路徑: {file_path}")
            return config # 返回空字典

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip() # 移除行首行尾空白，並檢查是否為空行
                    if not line:
                        continue

                    # 檢查行中是否包含分隔符 '='
                    if '=' in line:
                        # 使用 partition('=') 確保只以第一個等號分隔，
                        # 這樣值中如果包含等號（例如密碼或路徑），也能正確處理。
                        key, separator, value = line.partition('=')
                        key = key.strip()
                        value = value.strip()
                        # 確保鍵不為空，然後加入字典
                        if key:
                            config[key] = value

        except IOError as e:
            print(f"🔴 讀取檔案時發生 I/O 錯誤: {e}")
        except Exception as e:
            print(f"🔴 讀取設定檔時發生未預期錯誤: {e}")

        return config

    dic_config = config_to_dict()
    PYTHON_EXECUTABLE = dic_config.get("PYTHON_EXE")
    CHECK_SCRIPT_PATH = os.path.join(ROOT_DIR, "system", "tool_check_env.py")
    MAIN_FORM = os.path.join(ROOT_DIR, "gui", "us01","us01.py")

    sys.path.append(os.path.join(ROOT_DIR, "system"))
    # from share_qt5 import *
    from tool_gui import hide_cmd_window
    from tool_auth import AuthManager
    from tool_msgbox import error

def update_modules():
    # 檢查 套件
    # print('update_modules...')
    try:
        command = [PYTHON_EXECUTABLE, CHECK_SCRIPT_PATH]
        # print(f"🚀 檢查執行環境檢查: {PYTHON_EXECUTABLE}")
        result = subprocess.run(command,
            capture_output=False, # 讓 check_env.py 的 print 輸出直接顯示
            check=True,           # ⬅️ 關鍵：如果 check_env.py 退出碼非 0，會拋出 CalledProcessError
            text=True, encoding='utf-8')           # 確保輸出編碼正確 (UTF-8)

        # 如果執行到這裡，且 check=True 沒有拋出錯誤，表示 check_env.py 成功退出 (退出碼 0)
        return True

    except subprocess.CalledProcessError as e:
        # 捕獲到非零退出碼，表示 check_env.py 檢查失敗
        # print("\n🔴 環境檢查失敗。")
        # print("請根據上方 check_env.py 腳本的輸出，執行更新指令。")
        print("🚫 請聯繫系統管理員，或手動更新環境。")
        return False

    except FileNotFoundError:
        print(f"\n🔴 錯誤：找不到指定的 Python 執行檔於：{PYTHON_EXECUTABLE}")
        print("請檢查您的路徑設定是否正確。")
        sys.exit(1) # 啟動失敗
    except Exception as e:
        print(f"\n🔴 執行檢查腳本時發生未預期的錯誤: {e}")
        return False

def update_repo():
    # 更新主程序
    if os.path.exists(os.path.join(ROOT_DIR, ".git")):
        try:
            repo = Repo(ROOT_DIR)
            origin = repo.remotes.origin
            origin.fetch()
            local_commit = repo.head.commit.hexsha
            remote_commit = origin.refs[repo.active_branch.name].commit.hexsha
            if local_commit == remote_commit:
                print("✅ 主程式已是最新版本。")
            else:
                print("🔍 發現新版本，執行更新中...")
                origin.pull()
                print("✅ 更新完成！")

                # 重新啟動
                print("🔄 正在重新啟動程式以載入新版本...")
                # 以 os 作業系統執行重啟 sys.executable，並將 sys.executable 作為 argv[0]，其餘參數為 *sys.argv
                os.execl(sys.executable, sys.executable, *sys.argv)

        except GitCommandError as e:
            print("❌ 更新過程發生錯誤：", e)

def production_env_hide_cmd():
    # 若為生產環境 將隱藏命令視窗
    auth = AuthManager()
    data = auth.load_local_data()
    is_show_cmd_window = data.get("show_cmd_window", False)
    if not is_show_cmd_window: # 隱藏命令視窗
        hide_cmd_window(delay=4)

def main_form():
    try:
        command = [PYTHON_EXECUTABLE, MAIN_FORM]
        subprocess.run(command,
                capture_output=False,
                check=True,text=True, encoding='utf-8')

    except Exception as e:
        print(f"\n🔴 執行檢查腳本時發生未預期的錯誤: {e}")

def main():
    # 檢查套件
    result = update_modules()
    if result is False:
        error("啟動錯誤", "請聯繫系統管理員，或手動更新環境。",
          detail=f"原因是您的python環境套件，與 requirements.txt 文件內容不符\n🚀 Python executable: {sys.executable}")
        return

    # 更新主程序
    update_repo()

    # 啟動獨立進程異步執行 不阻塞主視窗 將隱藏命令視窗
    p = multiprocessing.Process(target=production_env_hide_cmd)
    p.start()

    # 開啟主表單
    main_form()

if __name__ == '__main__':
    main()