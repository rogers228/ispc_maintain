@echo off
REM 啟用虛擬環境並執行

REM 切換到 root
cd /d "%~dp0.."

REM 啟動虛擬環境並執行 Python 程式
call venv\Scripts\activate.bat

python gui\us05\us05.py

