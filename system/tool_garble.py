# 將 source 混淆為自執行檔

import base64
import textwrap
import random
import string

def encode_base64(input_string):
    utf8_bytes = input_string.encode('utf-8')
    base64_bytes = base64.b64encode(utf8_bytes)
    base64_string = base64_bytes.decode('utf-8')
    return base64_string

def decode_base64(base64_string):
    base64_bytes = base64_string.encode('utf-8')
    utf8_bytes = base64.b64decode(base64_bytes)
    original_string = utf8_bytes.decode('utf-8')
    return original_string

def generate_snippet(source, target, line_len = 80):
    # 將 source 混淆為自執行檔
    head = textwrap.fill(''.join(random.choice(string.ascii_letters + string.digits) for _ in range(8*line_len -6)),
        width=line_len, initial_indent='"""')+ '"""'

    dummy = "\n".join(
    ["# " + "".join(random.choices(string.ascii_letters + string.digits, k=60-2)) for _ in range(9)])

    with open(source, "r", encoding="utf-8") as f:
        content = f.read().strip()

    code = f'{content}\n{dummy}'
    b64 = encode_base64(code)
    b64_wrapped = textwrap.fill(b64, width=line_len, initial_indent='"""') + '"""'

    lines = b64_wrapped.splitlines()
    last_line_len = len(lines[-1]) if lines else 0
    foot = "#"+"".join(random.choices(string.ascii_letters + string.digits, k=line_len-last_line_len-1))

    script_lines = ["import inspect,sys,base64;exec(",
        "base64.b64decode(inspect.getsource(",
        "sys.modules[__name__]).split('\"\"\"')[-2]))"]

    script = "\n".join([f'{e}#{(
        ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(line_len-len(e)-1))
        )}'  for e in script_lines])

    payload = f'{head}\n{script}\n{b64_wrapped}{foot}'
    with open(target, "w", encoding="utf-8") as f:
        f.write(payload)

    return target

def test1():
    out = generate_snippet("config_web_local.py", "config_web.py")
    print("輸出完成:", out)

if __name__ == '__main__':
    test1()