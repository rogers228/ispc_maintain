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
%PYTHON_EXE% us09.py test
