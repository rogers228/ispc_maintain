import os
ISPC_MAINTAIN_VERSION = '0.85' # 供識別的大版號
ISPC_MAINTAIN_CACHE_DIR = os.path.abspath(os.path.join(os.getenv('LOCALAPPDATA'), "ISPC_Maintain", "cache"))

def test1():
    print(ISPC_MAINTAIN_VERSION)
    print(ISPC_MAINTAIN_CACHE_DIR)

if __name__ == '__main__':
    test1()