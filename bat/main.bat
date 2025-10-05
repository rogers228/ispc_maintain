@echo off

REM 切換標題 以利尋找隱藏
title ISPC_MAINTAIN

REM 切換到上層  為root  路徑才會正確
cd /d "%~dp0.."

rem 主表單
C:\python_green\python-3.12.9\python.exe gui\us01\us01.py
