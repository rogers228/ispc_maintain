@echo off
REM chcp 65001 顯示中文
chcp 65001 >nul

REM 切換到上層  為root  路徑才會正確
cd /d "%~dp0"

rem 讀取 config
for /f "delims=" %%a in (config.txt) do set %%a
echo PYTHON_EXE: %PYTHON_EXE%

REM 以執行環境 更新 pip
%PYTHON_EXE% -m pip install --upgrade pip

echo.
echo ________________________________________
echo.
echo 更新 pip 完畢！請按任意鍵離開。
echo.
echo ________________________________________
pause >nul
exit