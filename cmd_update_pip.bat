@echo off
REM chcp 65001 顯示中文
chcp 65001 >nul

REM 以執行環境 更新 pip
C:\python_green\python-3.12.9\python.exe -m pip install --upgrade pip

echo.
echo ________________________________________
echo.
echo 更新 pip 完畢！請按任意鍵離開。
echo.
echo ________________________________________
pause >nul
exit