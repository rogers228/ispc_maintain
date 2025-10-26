specification = {
    'name': 'pump pa10vo', # 產品名稱
    'name_en': 'PA10VO Series axial piston pump', # 產品名稱 英文
    'name_tw': 'PA10VO系列柱塞泵', # 產品名稱 繁體中文
    'name_zh': 'PA10VO系列柱塞泵', # 產品名稱 簡體中文
    'supply_default_value': 's',  # 供貨狀態 若為空白 則採用此作為預設值預設值
    'option_item_count': 12,  # 選項數量 int
    'models_order': [  # 選項順序
        '01un',    # 單元
        '02md',    # 工作模式
        '03dp',    # 排量
        '04ct',    # 控制
        '05sr',    # 系列
        '06cr',    # 旋轉
        '07se',    # 油封
        '08axv',   # 軸心型式
        '09ln',    # 安裝法蘭
        '10dn',    # 油路口
        '11th',    # 通軸驅動
        '12sd',    # 特殊規格
    ],
    'main_model': '04ct',   # 主要代表屬性
    'select_way': 1,  # 選型方式 1. 標準(可點擊選項，可快速選型) 2. 僅快速選型
    'models': {   # 選項
        '01un': {
            'name_en': 'Axial piston unit',
            'name_tw': '軸向柱塞單元',
            'name_zh': '轴向柱塞单元',
            'postfix_symbol': '',
            'default_value': 'PA10V',
            # 'model_item_length': 5,
            # 'model_items_order': ['PA10V'],
            # 'model_items': {
            #     'PA10V' :{
            #         'item_name_en': 'Swashplate design, variable',
            #         'item_name_tw': '斜盤設計，變量泵',
            #         'item_name_zh': '斜盘设计，变量泵',
            #         'supply': 's',
            #     },
            # }
        },
        '02md':{
            'name_en': 'Mounting',
            'name_tw': '裝配方式',
            'name_zh': '装配方式',
            'postfix_symbol': '',
            'default_value' : 'O',
            # 'model_item_length': 1,
            # 'model_items_order': ['O'],
            # 'model_items':{
            #     'O': {
            #          'item_name_en': 'Pump, open circuit',
            #          'item_name_tw': '泵，開式回路',
            #          'item_name_zh': '泵，开式回路',
            #          'supply': 's',
            #     },
            # }
        },
    }
}
