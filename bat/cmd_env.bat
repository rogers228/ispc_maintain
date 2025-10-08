@echo off
REM chcp 65001 顯示中文
chcp 65001 >nul

REM 執行 cmd視窗 切換到執行環境
REM start cmd → 開啟一個新的命令列視窗
REM /k → 表示執行完指令後「保留視窗開啟」

rem 工作目錄移動到本檔案位置
cd /d "%~dp0"

rem 讀取 config
for /f "delims=" %%a in (config.txt) do set %%a
rem echo PYTHON_EXE: %PYTHON_EXE%

rem 移動到 PYTHON_EXE 所在位置
start cmd /k cd /d "%PYTHON_EXE%\.."

rem 常用命令
rem python -m pip install --upgrade pip 更新 pip
rem python -m pip list
