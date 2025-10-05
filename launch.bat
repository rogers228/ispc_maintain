@echo off
REM chcp 65001 顯示中文
chcp 65001 >nul

REM 設定python解釋器執行環境
set pyapp=C:\python_green\python-3.12.9\python.exe

REM 以執行環境 更新 pip
%pyapp% -m pip install --upgrade pip

REM 以執行環境 安裝 所需套件
%pyapp% -m pip install -r requirements.txt

REM 執行啟動程序
%pyapp% system\tool_launch.py

echo ________________________________________
echo.
echo 啟動及更新完畢！請按任意鍵離開。
echo.
echo 請由桌面ISPC捷徑開啟進入，謝謝。
echo.
echo ________________________________________
pause >nul
exit