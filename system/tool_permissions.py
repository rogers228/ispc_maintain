# 以權限為基礎，獲取 產品資料選項 或 公司資料選項

if True:
    import sys, os
    import json

    def find_project_root(start_path=None, project_name="ispc_maintain"):
        if start_path is None:
            start_path = os.path.dirname(os.path.abspath(sys.argv[0]))
        current = start_path
        while True:
            if os.path.basename(current) == project_name:
                return current
            parent = os.path.dirname(current)
            if parent == current:
                raise FileNotFoundError(f"找不到專案 root (資料夾名稱 {project_name})")
            current = parent

    ROOT_DIR = find_project_root()
    sys.path.append(os.path.join(ROOT_DIR, "system"))
    from tool_options import Options
    from tool_auth import AuthManager

class PermissionsAdministrator:
    def __init__(self):
        self.auth = AuthManager()
        data = self.auth.load_local_data()
        self.email = data.get("email", "") # 使用者 email
        self.opt = Options()
        self.options = self.opt.get_options_auto()

    def show_options(self):
        print(json.dumps(self.options, indent=4, ensure_ascii=False))

    def get_product_by_product_uid(self, target_uid):
        permissions_product = self.options['permissions'][self.email]
        for item in permissions_product:
            for key, info in item.items():
                if info.get("uid") == target_uid:
                    dic = info.copy()
                    dic['product_key'] = key
                    return dic

    def get_company_by_company_uid(self, target_uid):
        permissions_vendor = self.options['garden'][self.email]
        for item in permissions_vendor:
            for key, info in item.items():
                if info.get("uid") == target_uid:
                    dic = info.copy()
                    dic['vendor_key'] = key
                    return dic

    def get_company_by_product_uid(self, target_uid):
        dic_product = self.get_product_by_product_uid(target_uid)
        company = dic_product.get('company')
        if not company:
            raise KeyError('lost company!')

        permissions_vendor = self.options['garden'][self.email]
        for item in permissions_vendor:
            for key, info in item.items():
                if key == company:
                    dic = info.copy()
                    dic['vendor_key'] = key
                    return dic

def test1():
    pa = PermissionsAdministrator()
    pa.show_options()

    product_uid = 'fec8abcc-db26-4c0f-9464-a07535091e0d'
    info_product = pa.get_product_by_product_uid(product_uid)
    print(json.dumps(info_product, indent=4, ensure_ascii=False))

    info_company = pa.get_company_by_product_uid(product_uid)
    print(json.dumps(info_company, indent=4, ensure_ascii=False))

    company_uid = 'ee080167-e20e-45bf-84ce-f5516022331c'
    info_company = pa.get_company_by_company_uid(company_uid)
    print(json.dumps(info_company, indent=4, ensure_ascii=False))

def test2():
    # 共有三種提取方式
    pa = PermissionsAdministrator()
    product_uid = 'fec8abcc-db26-4c0f-9464-a07535091e0d'
    pdno = pa.get_product_by_product_uid(product_uid).get('pdno')
    print(pdno)

    product_uid = 'fec8abcc-db26-4c0f-9464-a07535091e0d'
    vendor_path = pa.get_company_by_product_uid(product_uid).get('vendor_path')
    print(vendor_path)

    company_uid = 'ee080167-e20e-45bf-84ce-f5516022331c'
    vendor_path = pa.get_company_by_company_uid(company_uid).get('vendor_path')
    print(vendor_path)

if __name__ == '__main__':
    test1()
