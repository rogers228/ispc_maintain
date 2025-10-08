@echo off
REM chcp 65001 顯示中文
chcp 65001 >nul

rem 工作目錄移動到本檔案位置
cd /d "%~dp0"

rem 讀取 config
for /f "delims=" %%a in (config.txt) do set %%a

echo AUTHER: %AUTHER%
echo PYTHON_EXE: %PYTHON_EXE%
echo ROOT: %ROOT%

echo 執行完畢，請按任意鍵離開
pause >nul
exit