@echo off
REM chcp 65001 顯示中文
chcp 65001 >nul

rem 工作目錄移動到本檔案位置
cd /d "%~dp0"

rem 讀取 config
for /f "delims=" %%a in (config.txt) do set %%a
rem echo PYTHON_EXE: %PYTHON_EXE%

REM 切換標題 以利尋找隱藏
title ISPC_MAINTAIN

REM 切換到上層  為root  路徑才會正確
cd /d "%~dp0.."

rem 主程式的主表單
%PYTHON_EXE% system\tool_startup.py
