import sys
import time
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer, Qt
from typing import Optional

# 全局變數，用於儲存 QApplication 實例
_APP_INSTANCE: Optional[QApplication] = None

def _get_or_create_qapplication() -> QApplication:
    global _APP_INSTANCE
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    _APP_INSTANCE = app
    return app

class CustomMessageBox(QMessageBox):

    def __init__(self, *args, timeout_ms: int = 0, **kwargs):
        super().__init__(*args, **kwargs)

        self.timeout_ms = timeout_ms
        if self.timeout_ms > 0:
            # 創建 QTimer 實例
            self.timer = QTimer(self)
            # 連接 timeout 信號到 accept 槽 (QMessageBox 關閉)
            self.timer.timeout.connect(self.close)

            # 開始計時
            self.timer.start(self.timeout_ms)
        else:
            self.timer = None

    def closeEvent(self, event):

        if self.timer and self.timer.isActive():
            self.timer.stop()
        super().closeEvent(event)


def _show_alert(icon_type: QMessageBox.Icon, title: str, message: str,
               detailed_text: str = "", timeout_s: int = 0) -> int:
    """
    內部通用函數：用於顯示不同類型的訊息框。

    Args:
        icon_type: 訊息框圖標類型 (e.g., QMessageBox.Critical)
        title: 視窗標題。
        message: 訊息內容 (主文本)。
        detailed_text: 詳細文本內容。
        timeout_s: 超時秒數。預設 0 (不自動關閉)。

    Returns:
        int: 使用者點擊的按鈕值 (e.g., QMessageBox.Ok)。
    """
    # 1. 確保 QApplication 存在
    _get_or_create_qapplication()

    # 將秒數轉換為毫秒
    timeout_ms = timeout_s * 1000

    # 2. 創建帶有超時功能的訊息框
    msg_box = CustomMessageBox(timeout_ms=timeout_ms)

    # 3. 配置訊息框
    msg_box.setIcon(icon_type)
    msg_box.setWindowTitle(title)

    # 設置主文本和詳細文本
    msg_box.setText(message)
    if detailed_text:
        msg_box.setDetailedText(detailed_text)

    # 4. 設置標準按鈕 (可根據需求調整，這裡使用 Ok)
    msg_box.setStandardButtons(QMessageBox.Ok)

    # 5. 執行模態視窗，程式在此處阻塞
    return msg_box.exec_()


# --- 外部呼叫函數 ---

def info(title: str, message: str, detail: str = "", timeout_s: int = 0):
    """顯示一個信息 (Information) 訊息框。"""
    _show_alert(QMessageBox.Information, title, message, detail, timeout_s)

def warning(title: str, message: str, detail: str = "", timeout_s: int = 0):
    """顯示一個警告 (Warning) 訊息框。"""
    _show_alert(QMessageBox.Warning, title, message, detail, timeout_s)

def error(title: str, message: str, detail: str = "", timeout_s: int = 0):
    """顯示一個關鍵錯誤 (Critical) 訊息框。"""
    _show_alert(QMessageBox.Critical, title, message, detail, timeout_s)

def question(title: str, message: str, detail: str = "", timeout_s: int = 0) -> int:
    """
    顯示一個詢問 (Question) 訊息框，用於要求使用者確認。
    返回使用者點擊的按鈕值 (e.g., QMessageBox.Yes, QMessageBox.No)。
    注意：Question 類型通常不設定超時，但為保持一致性保留參數。
    """
    # 對 Question 類型，我們通常使用 Yes/No 按鈕
    _get_or_create_qapplication()

    msg_box = CustomMessageBox(timeout_ms=timeout_s * 1000)
    msg_box.setIcon(QMessageBox.Question)
    msg_box.setWindowTitle(title)
    msg_box.setText(f"**{message}**")
    msg_box.setDetailedText(detail)

    # 設置 Yes 和 No 按鈕
    msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    msg_box.setDefaultButton(QMessageBox.No) # 預設選中 No

    return msg_box.exec_()


# --- 測試代碼 (當直接運行 app_notifier.py 時執行) ---
if __name__ == '__main__':
    print("--- 測試 app_notifier 模組 ---")

    # 1. 關鍵錯誤測試 (無超時)
    error("啟動錯誤", "專案啟動失敗，請查看詳情。",
          detail="原因是您的主機名稱無法解析，請檢查網路設定或 /etc/hosts 文件。")
    print("錯誤訊息框已關閉。")

    # 2. 警告測試 (5 秒後自動關閉)
    warning("文件過期警告", "設定文件已過期，將使用備份值。",
            detail="系統偵測到 config.ini 的時間戳超過 30 天。",
            timeout_s=5)
    print("警告訊息框已關閉。")

    # 3. 信息測試 (3 秒後自動關閉)
    info("操作成功", "文件已保存到雲端。", timeout_s=3)

    # 4. 詢問測試 (需要手動點擊)
    reply = question("確認操作", "您確定要清除所有快取數據嗎？\n此操作不可逆。",
                     detail="清除快取將需要重新下載所有遠端資源，可能耗時較長。")

    if reply == QMessageBox.Yes:
        print("使用者選擇了 YES。")
    else:
        print("使用者選擇了 NO。")

    # 如果應用程式已創建但沒有主視窗，且需要等待事件處理完成，可能需要 app.exec_()
    if _APP_INSTANCE:
        print("應用程式事件循環結束。")
        # 如果需要保持運行，則使用 sys.exit(_APP_INSTANCE.exec_())

# 應使用cmd視窗執行，才會正常顯示