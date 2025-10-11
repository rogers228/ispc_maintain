import shutil

# 尋找 VS Code
vscode_path = shutil.which("code")


sublime_path = shutil.which("sublime_text.exe")


if vscode_path:
    print(f"VS Code 路徑: {vscode_path}")

if sublime_path:
    print(f"Sublime Text 路徑: {sublime_path}")

