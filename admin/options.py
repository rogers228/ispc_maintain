if True:
    import sys
    import os
    import json
    import click

    def find_project_root(start_path=None, project_name="ispc_maintain"):
        """從指定路徑往上找，直到找到名稱為 project_name 的資料夾"""
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

    ROOT_DIR = find_project_root() # 專案 root
    sys.path.append(os.path.join(ROOT_DIR, "system"))
    # from tool_auth import AuthManager
    from tool_options import Options
    opt = Options()

def pull_options():
    opt.pull_options()
    print('pull temp_options.json success.')

def push_options():
    try:
        with open(opt.OPTIONS_PATH, encoding='utf-8') as f:
            data = json.loads(f.read())

    except json.JSONDecodeError as e:
        error_line = getattr(e, 'lineno', '未知')
        error_col = getattr(e, 'colno', '未知')
        error_msg = f"❌ JSON 格式不合法 (JSONDecodeError): {e.msg}。"
        error_detail = f"發生在第 {error_line} 行，第 {error_col} 欄。"
        print(f"{error_msg} {error_detail}")
        return

    except Exception as e:
        print(f"⚠️ 讀取檔案時發生意外錯誤: {e}")
        return

    opt.update_options(data)
    print('push temp_options.json success.')

FUNCTION_MAP = {
    'pull': pull_options,
    'push': push_options,
}

@click.command() # 命令行入口
@click.option('-name', help='your name', required=True) # required 必要的
def main(name):
    target_func = FUNCTION_MAP.get(name)
    if target_func:
        target_func()
    else:
        error_msg = f"錯誤：找不到對應的操作 '{name}'。"
        click.echo(error_msg, err=True)
        click.echo(f"請使用以下任一選項: {', '.join(FUNCTION_MAP.keys())}", err=True)
        sys.exit(1) # 設置返回碼，讓 shell 知道程式執行失敗

if __name__ == '__main__':
    main()

# cmd
# python options.py -name pull