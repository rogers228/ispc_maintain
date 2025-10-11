@echo off
REM chcp 65001 顯示中文
chcp 65001 >nul

rem 切換到上層
cd /d "%~dp0.."

rem 讀取 config
for /f "delims=" %%a in (bat\config.txt) do set %%a
rem echo PYTHON_EXE: %PYTHON_EXE%

%PYTHON_EXE% system\tool_options.py -name pull

echo.
echo ________________________________________
echo.
echo 執行pull完畢！請按任意鍵離開。
echo.
echo ________________________________________
pause >nul
exit