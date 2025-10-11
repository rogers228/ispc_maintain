@echo off
REM chcp 65001 顯示中文
chcp 65001 >nul

rem 切換到上層
cd /d "%~dp0.."


rem 讀取 config
for /f "delims=" %%a in (bat\config.txt) do set %%a
echo PYTHON_EXE: %PYTHON_EXE%


pause >nul
exit