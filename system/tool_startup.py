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
    REQUIREMENTS_FILE_PATH = os.path.join(ROOT_DIR, "bat", "requirements.txt")

    sys.path.append(os.path.join(ROOT_DIR, "system"))
    # from share_qt5 import *
    from tool_gui import hide_cmd_window
    from tool_auth import AuthManager
    from tool_msgbox import error, info

def install_modules():
    # 使用指定的 PYTHON_EXECUTABLE 執行 pip install -r requirements.txt 進行更新。
    update_command = [
        PYTHON_EXECUTABLE,
        "-m",
        "pip",
        "install",
        "-r",
        REQUIREMENTS_FILE_PATH # 使用新的 REQUIREMENTS_FILE_PATH
    ]

    print("\n\n🛠️ 正在嘗試自動更新環境套件...")
    print(f"   使用的解釋器：{PYTHON_EXECUTABLE}")
    print(f"   執行指令：{' '.join(update_command)}")

    # 隱藏 CMD 視窗，如果使用者選擇隱藏
    hide_cmd_window_if_hidden() # 在執行外部程式前，確保CMD視窗的狀態

    try:
        # 執行更新指令，並將輸出導向標準輸出
        subprocess.run(
            update_command,
            check=True,  # 確保如果安裝失敗會報錯
            capture_output=False
        )
        print("\n✅ 環境已成功更新！")
        return True
    except subprocess.CalledProcessError as e:
        # 如果 pip install 失敗，則彈出錯誤訊息
        error("更新失敗", "自動更新環境套件失敗，請手動檢查網路或執行指令。",
              detail=f"指令：{' '.join(update_command)}\n退出碼: {e.returncode}")
        return False
    except FileNotFoundError:
        error("更新失敗", f"找不到指定的 Python 執行檔：{PYTHON_EXECUTABLE}。",
              detail="請檢查 config.txt 中的 PYTHON_EXE 路徑是否正確。")
        sys.exit(1) # 無法找到 Python 執行檔，啟動失敗
    except Exception as e:
        error("更新失敗", "執行更新時發生未預期錯誤。", detail=str(e))
        return False

def update_modules():
    # 檢查 套件
    # print('update_modules...')
    try:
        command = [PYTHON_EXECUTABLE, CHECK_SCRIPT_PATH]
        print(f"🚀 檢查執行環境檢查: {PYTHON_EXECUTABLE}")

        result = subprocess.run(command,
            capture_output=False, # 讓 check_env.py 的 print 輸出直接顯示
            check=True,           # ⬅️ 關鍵：如果 check_env.py 退出碼非 0，會拋出 CalledProcessError
            text=True, encoding='utf-8')           # 確保輸出編碼正確 (UTF-8)

        return True # 檢查通過 (退出碼 0)

    except subprocess.CalledProcessError as e:
        # 捕獲到非零退出碼，表示 check_env.py 檢查失敗
        print("⚠️ 環境檢查發現不符合要求，需要更新。")
        return False

    except FileNotFoundError:
        error("啟動錯誤", f"找不到指定的 Python 執行檔或檢查腳本。",
              detail=f"Python 路徑: {PYTHON_EXECUTABLE}\n檢查腳本路徑: {CHECK_SCRIPT_PATH}")
        sys.exit(1)
    except Exception as e:
        error("啟動錯誤", "執行環境檢查時發生未預期錯誤。", detail=str(e))
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

def hide_cmd_window_if_hidden():
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
    # 1. 更新 github 專案 包含 requirements.txt
    update_repo()

    # 2. 檢查套件
    result = update_modules()

    if result is False:
        # 環境不符，自動更新套件
        print("\n🔄 正在嘗試自動修復環境...")
        if not install_modules():
            sys.exit(1)

        # 成功安裝後，再次檢查以確認修復
        print("\n✅ 修復完成，正在重新檢查環境...")
        if not update_modules():
            error("啟動錯誤", "自動修復後再次檢查失敗。",
                  detail="請手動確認 requirements.txt 和 Python 環境。")
            sys.exit(1)
        else:
            # 確保修復成功後，給予使用者一個明確的成功提示 (可選)
            print("環境修復完成", "所有所需套件已更新並通過檢查。")


    # 3. 啟動獨立進程異步執行 隱藏命令視窗
    p = multiprocessing.Process(target=hide_cmd_window_if_hidden)
    p.start()

    # 4. 開啟主表單
    main_form()

if __name__ == '__main__':
    main()