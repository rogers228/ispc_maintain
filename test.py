if True:
    import sys, os
    sys.path.append(os.path.join(ROOT_DIR, "system"))
    from config import spwr_api_url, spwr_api_anon_key
    print(spwr_api_url)

def test1():
    lis_index = lambda count: [f'index_{i}' for i in range(5)]
    print(lis_index(5))

if __name__ == '__main__':
    test1()