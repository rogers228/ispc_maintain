@echo off
REM chcp 65001 顯示中文
chcp 65001 >nul

REM 切換到上層  為root  路徑才會正確
cd /d "%~dp0.."

REM 以執行環境 安裝 所需套件
C:\python_green\python-3.12.9\python.exe -m pip install -r requirements.txt

echo.
echo ________________________________________
echo.
echo 安裝套件完畢！請按任意鍵離開。
echo.
echo ________________________________________
pause >nul
exit