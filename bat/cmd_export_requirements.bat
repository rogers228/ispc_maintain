@echo off
REM chcp 65001 顯示中文
chcp 65001 >nul

REM 切換到上層  為root  路徑才會正確
cd /d "%~dp0.."

REM 以執行環境導出所需套件 requirements.txt 至最上層 root
C:\python_green\python-3.12.9\python.exe -m pip freeze > requirements.txt

echo.
echo ________________________________________
echo.
echo 導出 requirements.txt 完畢！請按任意鍵離開。
echo.
echo ________________________________________
pause >nul
exit