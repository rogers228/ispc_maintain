@echo off
REM 執行虛擬環境 cmd視窗
REM start cmd → 開啟一個新的命令列視窗
REM /k → 表示執行完指令後「保留視窗開啟」
start cmd /k "cd /d "%~dp0" && venv\Scripts\activate.bat"