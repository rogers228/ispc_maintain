@echo off
REM chcp 65001 顯示中文
chcp 65001 >nul

rem 切換到 root
cd /d "%~dp0..\.."

rem 讀取 config
for /f "delims=" %%a in (bat\config.txt) do set %%a
rem echo PYTHON_EXE: %PYTHON_EXE%

rem 切換到本檔案位置
cd /d "%~dp0"

rem 使用命令視窗，方便除錯 可帶引數執行
rem %PYTHON_EXE% us07.py product 4b87a39d-a0e4-4f73-8945-ebc54994e112

%PYTHON_EXE% us07.py company ee080167-e20e-45bf-84ce-f5516022331c