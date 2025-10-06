@echo off
REM chcp 65001 顯示中文
chcp 65001 >nul

echo ________________________________________
echo.

C:\python_green\python-3.12.9\python.exe options.py -name push

echo.
echo 執行完畢！請按任意鍵離開。
echo.
echo ________________________________________
pause >nul
exit