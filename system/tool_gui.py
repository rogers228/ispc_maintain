# 視窗操作
import win32gui, win32con

def hide_cmd_window(target_title='ISPC_MAINTAIN'):
    # 隱藏命令視窗
    hwnd = win32gui.FindWindow(None, target_title)
    if hwnd == 0:
        print(f"警告：找不到標題為 '{target_title}' 的視窗。")
        return False

    print(f"找到視窗HWND: {hwnd}, 將隱藏。")
    win32gui.ShowWindow(hwnd, win32con.SW_HIDE) # 隱藏視窗
    return True

def show_cmd_window(target_title='ISPC_MAINTAIN'):
    """顯示指定標題的命令視窗"""
    hwnd = win32gui.FindWindow(None, target_title)
    if hwnd == 0:
        print(f"警告：找不到標題為 '{target_title}' 的視窗。")
        return False

    print(f"找到視窗HWND: {hwnd}, 將顯示。")
    # SW_RESTORE 比 SW_SHOW 更穩定，能避免視窗最小化無法恢復的情況
    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    return True

def test1():
    hide_cmd_window()

def test2():
    show_cmd_window()

if __name__ == '__main__':
    test1()
    import time
    time.sleep(3)
    test2()