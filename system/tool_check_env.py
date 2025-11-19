# 檢查環境，確保依賴套件正確

if True:
    import sys, os
    from importlib.metadata import distributions
    from packaging.requirements import Requirement
    from packaging.version import parse as parse_version
    from typing import List, Dict, Tuple

    # print("🚀 Python executable:", sys.executable) # 目前執行的python路徑 用來判斷是否是虛擬環境python 或 本機python

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
    REQUIREMENTS_FILE = os.path.join(ROOT_DIR, "bat", "requirements.txt")

def get_installed_packages_versions() -> Dict[str, str]:
    """
    使用 importlib.metadata 獲取當前環境中所有已安裝套件的 {名稱: 版本}。
    """
    installed = {}
    for dist in distributions():
        # 注意：使用 dist.metadata['Name'].lower() 確保名稱比較不區分大小寫
        installed[dist.metadata['Name'].lower()] = dist.version
    return installed

def parse_requirements(file_path: str) -> List[Requirement]:
    """
    解析 requirements.txt 檔案，返回套件要求物件列表。
    """
    # 使用 os.path.join 確保路徑組合的正確性
    full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_path)

    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            # 使用 packaging.requirements.Requirement 處理每一行
            return [
                Requirement(line.strip())
                for line in f
                if line.strip() and not line.strip().startswith('#') # 過濾註解和空行
            ]
    except FileNotFoundError:
        # 這裡必須使用 sys.exit(1) 以便 main.py 中的 subprocess 捕獲錯誤
        print(f"🔴 錯誤：找不到 requirements 檔案於路徑: {full_path}")
        sys.exit(1)

def check_environment_status(
    required: List[Requirement],
    installed: Dict[str, str]
) -> Tuple[List[str], List[str]]:
    """
    比對 requirements.txt 與已安裝套件，找出需要更新和缺少的套件。

    回傳：(需要更新的套件列表, 缺少的套件列表)
    """
    to_update = []
    missing = []

    for req in required:
        pkg_name = req.name.lower()

        if pkg_name not in installed:
            # 1. 套件不存在，需要安裝
            missing.append(str(req))
        else:
            # 2. 套件存在，檢查版本是否符合要求
            installed_version = parse_version(installed[pkg_name])

            # req.specifier 是版本限定符集合
            if req.specifier and installed_version not in req.specifier:
                # 版本不符合要求，需要更新
                required_spec = str(req.specifier)
                current_version = installed[pkg_name]

                to_update.append(f"{str(req)} (已安裝版本: {current_version} 不符合要求: {required_spec})")

    return to_update, missing

def run_environment_check():
    # 依照執行環境 檢查套件
    # print("🚀 run_environment_check...")
    # print(f" 目前檢查的的解釋器：{sys.executable}")

    required_packages = parse_requirements(REQUIREMENTS_FILE)
    installed_packages = get_installed_packages_versions()

    to_update, missing = check_environment_status(required_packages, installed_packages)

    if not to_update and not missing:
        # print("✅ 環境檢查通過！所有依賴套件都已安裝且版本符合 requirements.txt 的要求。")
        print("✅ 環境套件已是最新版本。")
        return True # 檢查成功，正常返回

    # --- 顯示檢查結果 ---

    print("\n⚠️ 環境檢查發現問題：")

    if missing:
        print(f"### 缺少 (Missing) 套件 ({len(missing)} 個) ###")
        for pkg in missing:
            print(f" - ❗ {pkg}")

    if to_update:
        print(f"\n### 版本不符 (Outdated/Incorrect) 套件 ({len(to_update)} 個) ###")
        for pkg in to_update:
            print(f" - 🔄 {pkg}")

    # 檢查失敗，使用 sys.exit(1) 觸發 main.py 中的 subprocess.CalledProcessError
    sys.exit(1)

if __name__ == "__main__":
    run_environment_check()
