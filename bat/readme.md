# 說明

此資料夾為bat執行檔集中於此。

## config.txt

config.txt  是安裝程式自動建立的，勿編輯


## requirements.txt

requirements.txt  是更新使用者套件的，若有新增套件，
請執行 cmd_export_requirements.bat 來更新 requirements.txt


## cmd_launch.bat

首次啟動時，會觸發此程序，並執行 tool_launch.py，觸發相關程序及建立桌面捷徑。


## main.bat

正常主入口，桌面捷徑會執行 main.bat，會執行此檔案。