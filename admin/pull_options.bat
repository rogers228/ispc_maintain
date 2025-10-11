@echo off
REM chcp 65001 顯示中文
chcp 65001 >nul

rem 切換到上層
cd /d "%~dp0.."


echo ________________________________________
echo.

C:\python_green\python-3.12.9\python.exe system\tool_options.py -name pull

echo.
echo 執行pull完畢！請按任意鍵離開。
echo.
echo ________________________________________
pause >nul
exit