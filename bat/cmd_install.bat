@echo off
REM chcp 65001 顯示中文
chcp 65001 >nul

rem 工作目錄移動到本檔案位置
cd /d "%~dp0"

rem 讀取 config
for /f "delims=" %%a in (config.txt) do set %%a
echo PYTHON_EXE: %PYTHON_EXE%

REM 以執行環境 安裝 所需套件
%PYTHON_EXE% -m pip install -r requirements.txt

echo.
echo ________________________________________
echo.
echo 安裝套件完畢！請按任意鍵離開。
echo.
echo ________________________________________
pause >nul
exit