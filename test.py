import os
import re

def replace_system_section(new_data: dict):
    # 替換 section
    # bool: True 代表修改成功並寫入檔案。
    # None: 代表未修改或修改失敗 (例如找不到檔案)。

    file = os.path.join(os.path.dirname(__file__), 'tempstorage', 'template.py')

    # 構建要替換的新 system 字典字串
    system_dict_lines = []
    system_dict_lines.append("    system = {")
    for key, value in new_data.items():
        system_dict_lines.append(f"        '{key}': '{value}',")
    system_dict_lines.append("    }")
    system_dict_str = "\n".join(system_dict_lines)
    replacement_content = (
        f"if True: # -----section system start-----\n" # 區塊開頭 (無縮排)
        f"{system_dict_str}\n"                          # 字典內容 (已包含正確的 4/8 縮排)
        f"    # -----section system end-----\n"           # 區塊結尾 (4 個空格縮排)
    )

    pattern = re.compile(r'if True:\s*#\s*-{5}section system start-{5}.*?#\s*-{5}section system end-{5}', re.DOTALL)

    try:
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"❌ 錯誤: 找不到檔案 {file}，請檢查路徑。")
        return None
    except Exception as e:
        print(f"❌ 讀取檔案 {file} 時發生錯誤: {e}")
        return None

    new_content = pattern.sub(replacement_content, content)
    if new_content == content:
        # 如果內容沒有變動，避免寫入
        print(f"⚠️ 檔案 {file} 內容未變動，跳過寫入。")
        return None

    # 寫回檔案
    try:
        with open(file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"✅ 檔案 {file} 已成功更新。")
        return True
    except Exception as e:
        print(f"❌ 寫入檔案 {file} 時發生錯誤: {e}")
        return None

def test1():
    new_data = {
        'test': 'template',
        'version': '9-20251020',
    }
    result = replace_system_section(new_data)

    # 根據返回值列印結果
    if result is True:
        print("主程式呼叫: 配置更新成功。")
    else:
        print("主程式呼叫: 配置更新失敗或未操作。")

if __name__ == '__main__':
    test1()