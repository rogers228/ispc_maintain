@echo off
rem 首次啟動程序

REM chcp 65001 顯示中文
chcp 65001 >nul

REM 工作目錄切換到批次檔本身所在的目錄
cd /d "%~dp0"

rem 讀取 config
for /f "delims=" %%a in (config.txt) do set %%a
echo PYTHON_EXE: %PYTHON_EXE%

REM 以執行環境 更新 pip
%PYTHON_EXE% -m pip install --upgrade pip

REM 以執行環境 安裝 所需套件
%PYTHON_EXE% -m pip install -r requirements.txt

REM 切換到上層  為root  路徑才會正確
cd /d "%~dp0.."

REM 執行啟動程序
%PYTHON_EXE% system\tool_launch.py

echo ________________________________________
echo.
echo  安裝完畢！請按任意鍵離開。
echo.
echo ________________________________________
pause >nul
exit