# 產品基本資料
dic_prodect = {
    'pdid': '1Ny2tq87Pviz', # 產品id
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
            'model_item_length': 5,
            'model_items_order': ['PA10V'],
            'model_items': {
                'PA10V' :{
                    'item_name_en': 'Swashplate design, variable',
                    'item_name_tw': '斜盤設計，變量泵',
                    'item_name_zh': '斜盘设计，变量泵',
                    'supply': 's',
                },         
            }
            },
        '02md':{
            'name_en': 'Mounting',
            'name_tw': '裝配方式',
            'name_zh': '装配方式',
            'postfix_symbol': '',
            'default_value' : 'O',
            'model_item_length': 1,
            'model_items_order': ['O'],
            'model_items':{
                'O': {
                     'item_name_en': 'Pump, open circuit',
                     'item_name_tw': '泵，開式回路',
                     'item_name_zh': '泵，开式回路',
                     'supply': 's',
                },
            }
            },   
        '03dp': {
            'name_en': 'Size',
            'name_tw': '排量規格',
            'name_zh': '排量规格',
            'postfix_symbol': '',
            'default_value' : '',
            'model_item_length': 3,
            'model_items_order': ['010', '018', '028', '045', '060', '063', '085', '100'],
            'model_items':{
                '010': {
                     'item_name_en': '10cm³/rev',
                     'item_name_tw': '10cm³/rev',
                     'item_name_zh': '10cm³/rev',
                     'supply': 's',
                },
                '018': {
                     'item_name_en': '18cm³/rev',
                     'item_name_tw': '18cm³/rev',
                     'item_name_zh': '18cm³/rev',
                     'supply': 'n',
                },
                '028': {
                     'item_name_en': '28cm³/rev',
                     'item_name_tw': '28cm³/rev',
                     'item_name_zh': '28cm³/rev',
                     'supply': 'n',
                },
                '045': {
                     'item_name_en': '45cm³/rev',
                     'item_name_tw': '45cm³/rev',
                     'item_name_zh': '45cm³/rev',
                     'supply': 'n',
                },
                '060': {
                     'item_name_en': '60cm³/rev',
                     'item_name_tw': '60cm³/rev',
                     'item_name_zh': '60cm³/rev',
                     'supply': 's',
                },
                '063': {
                     'item_name_en': '63cm³/rev',
                     'item_name_tw': '63cm³/rev',
                     'item_name_zh': '63cm³/rev',
                     'supply': 's',
                },
                '085': {
                     'item_name_en': '85cm³/rev',
                     'item_name_tw': '85cm³/rev',
                     'item_name_zh': '85cm³/rev',
                     'supply': 'n',
                },
                '100': {
                     'item_name_en': '100cm³/rev',
                     'item_name_tw': '100cm³/rev',
                     'item_name_zh': '100cm³/rev',
                     'supply': 'n',
                },
            }
            },   
        '04ct': {
            'name_en': 'Control device',
            'name_tw': '控制方式',
            'name_zh': '控制方式',
            'postfix_symbol': '/',
            'default_value': '',
            'model_item_length': 5,
            'model_items_order': ['000DR', '00DRL', '00DRG', '0DRGL', '00DFR', '00DRF', '0DFR1', '00DRS', 'EF.D.', '0ED71', '0ED72', '0ER71', '0ER72', '0LA5D', '0LA6D', '0LA7D', '0LA8D', '0LA9D', 'LA.DG', 'LA.DS', '0LA.S'],
            'model_items': {
                '000DR':{
                    'item_name_en': 'Pressure control',
                    'item_name_tw': '標準型壓力控制',
                    'item_name_zh': '标准型压力控制',
                    'supply': 's',
                },
                '00DRL':{
                    'item_name_en': 'Pressure control',
                    'item_name_tw': '標準型壓力控制+電控流量卸載',
                    'item_name_zh': '标准型压力控制',
                    'supply': 's',
                },
                '00DRG':{
                    'item_name_en': 'Pressure control, remotely operated, hydraulic',
                    'item_name_tw': '遙控型壓力控制',
                    'item_name_zh': '遥控型压力控制',
                    'supply': 's',
                },
                '0DRGL':{
                    'item_name_en': 'Pressure control, remotely operated, electrical flow unloading',
                    'item_name_tw': '遙控型壓力控制+電控流量卸載',
                    'item_name_zh': '遥控型压力控制+电控流量卸载',
                    'supply': 's',
                },
                '00DFR':{
                    'item_name_en': 'Pressure and flow control, hydraulic (X-T open)',
                    'item_name_tw': '壓力控制+液壓流量控制(X-T開啟)',
                    'item_name_zh': '压力控制+液压流量控制(X-T开启)',
                    'supply': 's',
                },
                '00DRF':{
                    'item_name_en': 'Pressure and flow control, hydraulic (X-T open)',
                    'item_name_tw': '壓力控制+液壓流量控制(X-T開啟)',
                    'item_name_zh': '压力控制+液压流量控制(X-T开启)',
                    'supply': 's',
                },
                '0DFR1':{
                    'item_name_en': 'Pressure and flow control, hydraulic (X-T closed)',
                    'item_name_tw': '壓力控制+液壓流量控制(X-T關閉)',
                    'item_name_zh': '压力控制+液压流量控制(X-T关闭)',
                    'supply': 'n',
                },
                '00DRS':{
                    'item_name_en': 'Pressure and floe control, hydraulic (X-T closed)',
                    'item_name_tw': '壓力控制+液壓流量控制(X-T關閉)',
                    'item_name_zh': '压力控制+液压流量控制(X-T关闭)',
                    'supply': 'n',
                },
                'EF.D.':{
                    'item_name_en': 'Pressure and flow control, hydraulic, Electrically overridable (negative characteristic)',
                    'item_name_tw': '壓力控制+液壓流量控制，可電覆蓋(負極特性)',
                    'item_name_zh': '压力控制+液压流量控制，可电覆盖(负极特性)',
                    'supply': 'n',
                },
                '0ED71':{
                    'item_name_en': 'Electro-hydrualic pressure control, electrical negative characteristic 12V',
                    'item_name_tw': '電動液壓壓力控制 負極特性 12V',
                    'item_name_zh': '电动液压压力控制 负极特性 12V',
                    'supply': 's',
                },
                '0ED72':{
                    'item_name_en': 'Electro-hydrualic pressure control, electrical negative characteristic 24V',
                    'item_name_tw': '電動液壓壓力控制 負極特性 24V',
                    'item_name_zh': '电动液压压力控制 负极特性 24V',
                    'supply': 's',
                },
                '0ER71':{
                    'item_name_en': 'Electro-hydrualic pressure control, electrical positive characteristic 12V',
                    'item_name_tw': '電動液壓壓力控制 正極特性 12V',
                    'item_name_zh': '电动液压压力控制 正极特性 12V',
                    'supply': 's',
                },
                '0ER72':{
                    'item_name_en': 'Electro-hydrualic pressure control, electrical positive charaacteristic 24V',
                    'item_name_tw': '電動液壓壓力控制 正極特性 24V',
                    'item_name_zh': '电动液压压力控制 正极特性 24V',
                    'supply': 's',
                },
                '0LA5D':{
                    'item_name_en': 'Pressure, flow and power control, Start of control 10 to 35 bar',
                    'item_name_tw': '壓力控制+流量控制+功率控制，控制初始值10~35bar',
                    'item_name_zh': '压力控制+流量控制+功率控制，控制初始值10~35bar',
                    'supply': 's',
                },
                '0LA6D':{
                    'item_name_en': 'Pressure, flow and power control, Start of control 36 to 70 bar',
                    'item_name_tw': '壓力控制+流量控制+功率控制，控制初始值36~70bar',
                    'item_name_zh': '压力控制+流量控制+功率控制，控制初始值36~70bar',
                    'supply': 's',
                },
                '0LA7D':{
                    'item_name_en': 'Pressure, flow and power control, Start of control 71 to 105 bar',
                    'item_name_tw': '壓力控制+流量控制+功率控制，控制初始值71~105bar',
                    'item_name_zh': '压力控制+流量控制+功率控制，控制初始值71~105bar',
                    'supply': 's',
                },
                '0LA8D':{
                    'item_name_en': 'Pressure, flow and power control, Start of control 106 to 140 bar',
                    'item_name_tw': '壓力控制+流量控制+功率控制，控制初始值106~140bar',
                    'item_name_zh': '压力控制+流量控制+功率控制，控制初始值106~140bar',
                    'supply': 's',
                },
                '0LA9D':{
                    'item_name_en': 'Pressure, flow and power control, Start of control 141 to 230 bar',
                    'item_name_tw': '壓力控制+流量控制+功率控制，控制初始值141~230bar',
                    'item_name_zh': '压力控制+流量控制+功率控制，控制初始值141~230bar',
                    'supply': 's',
                },
                'LA.DG':{
                    'item_name_en': 'Pressure, flow and power control with pressure cut-off, remotely operated, Start of control see "LA.D"',
                    'item_name_tw': '，控制初始值參見LA.D',
                    'item_name_zh': '，控制初始值参见LA.D',
                    'supply': 'n',
                },
                'LA.DS':{
                    'item_name_en': 'Pressure, flow and power control with pressure and flow control',
                    'item_name_tw': ' ，X-T關閉，控制初始值參見LA.D',
                    'item_name_zh': ' ，X-T关闭，控制初始值参见LA.D',
                    'supply': 'n',
                },
                '0LA.S':{
                    'item_name_en': 'Pressure, flow and power control with ',
                    'item_name_tw': '功率控制帶壓力切斷閥+流量控制，可電覆蓋(負極特性)，X-T關閉，控制初始值參見LA.D',
                    'item_name_zh': '功率控制带压力切断阀+流量控制，可电覆盖(负极特性)，X-T关闭，控制初始值参见LA.D',
                    'supply': 'n',
                },
            }
            },
        '05sr': {
            'name_en': 'Series',
            'name_tw': '系列',
            'name_zh': '系列',
            'postfix_symbol': '',
            'default_value' : '53',
            'model_item_length': 2,
            'model_items_order': ['52', '53'],
            'model_items':{
                '52': {
                     'item_name_en': 'Series 5, Index 2',
                     'item_name_tw': '系列5，索引號2',
                     'item_name_zh': '系列5，索引号2',
                     'supply': 's',
                },
                '53': {
                     'item_name_en': 'Series 5, Index 3',
                     'item_name_tw': '系列5，索引號3',
                     'item_name_zh': '系列5，索引号3',
                     'supply': 's',
                },
            }
            },
        '06cr': {
            'name_en': 'Direction of rotation',
            'name_tw': '旋轉方向',
            'name_zh': '旋转方向',
            'postfix_symbol': '-',
            'default_value' : '',
            'model_item_length': 1,
            'model_items_order': ['R', 'L'],
            'model_items': {
                'R': {
                     'item_name_en': 'Clockwise',
                     'item_name_tw': '順時針方向',
                     'item_name_zh': '顺时针方向',
                     'supply': 's',
                },
                'L': {
                     'item_name_en': 'Counter clockwise',
                     'item_name_tw': '逆時針方向',
                     'item_name_zh': '逆时针方向',
                     'supply': 's',
                },
              }
            },  
        '07se': {
            'name_en': 'Seals',
            'name_tw': '油封',
            'name_zh': '油封',
            'postfix_symbol': '',
            'default_value' : 'V',
            'model_item_length': 1,
            'model_items_order': ['V'],
            'model_items':{
                'V': {
                     'item_name_en': 'FKM (VITON)',
                     'item_name_tw': '氟橡膠 (FKM)',
                     'item_name_zh': '氟橡胶 (FKM)',
                     'supply': 's',
                },
            }
            },
        '08axv': {
            'name_en': 'Drive shaft',
            'name_tw': '傳動軸',
            'name_zh': '传动轴',
            'postfix_symbol': '',
            'default_value' : '',
            'model_item_length': 2,
            'model_items_order': ['S1', 'U1', 'P1', 'S2', 'R2', 'U2', 'P2', 'S3', 'R3', 'S4', 'R4', 'U4', 'W4', 'S5', 'R5', 'U5', 'W5', 'S6', 'U6', 'W6'],
            'model_items': {
                'S1': {   #10
                     'item_name_en': 'Splined shaft 3/4 in  11T 16/32DP (SAE J744)',
                     'item_name_tw': '花鍵軸 3/4 in  11T 16/32DP (SAE J744)',
                     'item_name_zh': '花键轴 3/4 in  11T 16/32DP (SAE J744)',
                     'supply': 's',
                },
                'U1': {
                     'item_name_en': 'Splined shaft 5/8 in  9T 16/32DP (SAE J744)',
                     'item_name_tw': '花鍵軸 5/8 in  9T 16/32DP (SAE J744)',
                     'item_name_zh': '花键轴 5/8 in  9T 16/32DP (SAE J744)',
                     'supply': 's',
                },
                'P1': {
                     'item_name_en': 'Parallel shaft key 6*6*18 (DIN 6885)',
                     'item_name_tw': '公制 平鍵軸 6*6*18 (DIN 6885)',
                     'item_name_zh': '公制 平键轴 6*6*18 (DIN 6885)',
                     'supply': 's',
                },
                'S2': {   #18
                     'item_name_en': 'Splined shaft 3/4 in  11T 16/32DP (SAE J744)',
                     'item_name_tw': '花鍵軸 3/4 in  11T 16/32DP (SAE J744)',
                     'item_name_zh': '花键轴 3/4 in  11T 16/32DP (SAE J744)',
                     'supply': 's',
                },
                'R2': {
                     'item_name_en': 'Splined shaft 3/4 in  11T 16/32DP (SAE J744) Higher torque',
                     'item_name_tw': '花鍵軸 3/4 in  11T 16/32DP (SAE J744) 較高扭矩',
                     'item_name_zh': '花键轴 3/4 in  11T 16/32DP (SAE J744) 较高扭矩',
                     'supply': 's',
                },
                'U2': {
                     'item_name_en': 'Splined shaft 5/8 in  9T 16/32DP (SAE J744)',
                     'item_name_tw': '花鍵軸 5/8 in  9T 16/32DP (SAE J744)',
                     'item_name_zh': '花键轴 5/8 in  9T 16/32DP (SAE J744)',
                     'supply': 's',
                },
                'P2': {
                     'item_name_en': 'Parallel shaft key 6*6*18 (DIN 6885)',
                     'item_name_tw': '公制 平鍵軸 6*6*18 (DIN 6885)',
                     'item_name_zh': '公制 平键轴 6*6*18 (DIN 6885)',
                     'supply': 's',
                },
                'S3': {   #28
                     'item_name_en': 'Splined shaft 7/8 in  13T 16/32DP (SAE J744)',
                     'item_name_tw': '花鍵軸 7/8 in  13T 16/32DP (SAE J744)',
                     'item_name_zh': '花键轴 7/8 in  13T 16/32DP (SAE J744)',
                     'supply': 's',
                },
                'R3': {
                     'item_name_en': 'Splined shaft 7/8 in  13T 16/32DP (SAE J744) Higher torque',
                     'item_name_tw': '花鍵軸 7/8 in  13T 16/32DP (SAE J744) 較高扭矩',
                     'item_name_zh': '花键轴 7/8 in  13T 16/32DP (SAE J744) 较高扭矩',
                     'supply': 's',
                },
                'S4': {   #45
                     'item_name_en': 'Splined shaft 1 in  15T 16/32DP (SAE J744)',
                     'item_name_tw': '花鍵軸 1 in  15T 16/32DP (SAE J744)',
                     'item_name_zh': '花键轴 1 in  15T 16/32DP (SAE J744)',
                     'supply': 's',
                },
                'R4': {
                     'item_name_en': 'Splined shaft 1 in  15T 16/32DP (SAE J744) Higher torque',
                     'item_name_tw': '花鍵軸 1 in  15T 16/32DP (SAE J744) 較高扭矩',
                     'item_name_zh': '花键轴 1 in  15T 16/32DP (SAE J744) 较高扭矩',
                     'supply': 's',
                },
                'U4': {
                     'item_name_en': 'Splined shaft 7/8 in  13T 16/32DP (SAE J744)',
                     'item_name_tw': '花鍵軸 7/8 in  13T 16/32DP (SAE J744)',
                     'item_name_zh': '花键轴 7/8 in  13T 16/32DP (SAE J744)',
                     'supply': 's',
                },
                'W4': {
                     'item_name_en': 'Splined shaft 7/8 in  13T 16/32DP (SAE J744) Higher torque',
                     'item_name_tw': '花鍵軸 7/8 in  13T 16/32DP (SAE J744) 較高扭矩',
                     'item_name_zh': '花键轴 7/8 in  13T 16/32DP (SAE J744) 较高扭矩',
                     'supply': 's',
                },
                'S5': {   #60、63
                     'item_name_en': 'Splined shaft 1 1/4 in  14T 12/24DP (SAE J744)',
                     'item_name_tw': '花鍵軸 1 1/4 in  14T 12/24DP (SAE J744)',
                     'item_name_zh': '花键轴 1 1/4 in  14T 12/24DP (SAE J744)',
                     'supply': 's',
                },
                'R5': {
                     'item_name_en': 'Splined shaft 1 1/4 in  14T 12/24DP (SAE J744) Higher torque',
                     'item_name_tw': '花鍵軸 1 1/4 in  14T 12/24DP (SAE J744) 較高扭矩',
                     'item_name_zh': '花键轴 1 1/4 in  14T 12/24DP (SAE J744) 较高扭矩',
                     'supply': 's',
                },
                'U5': {
                     'item_name_en': 'Splined shaft 1 in  15T 16/32DP (SAE J744)',
                     'item_name_tw': '花鍵軸 1 in  15T 16/32DP (SAE J744)',
                     'item_name_zh': '花键轴 1 in  15T 16/32DP (SAE J744)',
                     'supply': 's',
                },
                'W5': {
                     'item_name_en': 'Splined shaft 1 in  15T 16/32DP (SAE J744) Higher torque',
                     'item_name_tw': '花鍵軸 1 in  15T 16/32DP (SAE J744) 較高扭矩',
                     'item_name_zh': '花键轴 1 in  15T 16/32DP (SAE J744) 较高扭矩',
                     'supply': 's',
                },
                'S6': {   #85、100
                     'item_name_en': 'Splined shaft 1 1/2 in  17T 12/24DP (SAE J744)',
                     'item_name_tw': '花鍵軸 1 1/2 in  17T 12/24DP (SAE J744)',
                     'item_name_zh': '花键轴 1 1/2 in  17T 12/24DP (SAE J744)',
                     'supply': 's',
                },
                'U6': {
                     'item_name_en': 'Splined shaft 1 1/4 in  14T 12/24DP (SAE J744)',
                     'item_name_tw': '花鍵軸 1 1/4 in  14T 12/24DP (SAE J744)',
                     'item_name_zh': '花键轴 1 1/4 in  14T 12/24DP (SAE J744)',
                     'supply': 's',
                },
                'W6': {
                     'item_name_en': 'Splined shaft 1 1/4 in  14T 12/24DP (SAE J744) Higher torque',
                     'item_name_tw': '花鍵軸 1 1/4 in  14T 12/24DP (SAE J744) 較高扭矩',
                     'item_name_zh': '花键轴 1 1/4 in  14T 12/24DP (SAE J744) 较高扭矩',
                     'supply': 's',
                },
              }
            },
        '09ln': {
            'name_en': 'Mounting flange',
            'name_tw': '安裝法蘭',
            'name_zh': '安装法兰',
            'postfix_symbol': '',
            'default_value' : '',
            'model_item_length': 1,
            'model_items_order': ['A', 'C', 'D'],
            'model_items':{
                'A': {
                    'item_name_en': 'ISO 3019-2 (Metric) 2-hole',
                    'item_name_tw': 'ISO 3019-2 (Metric) 2孔型',
                    'item_name_zh': 'ISO 3019-2 (Metric) 2孔型',
                    'supply': 's',
                },
                'C': {
                    'item_name_en': 'ISO 3019-1 (SAE) 2-hole',
                    'item_name_tw': 'ISO 3019-1 (SAE) 2孔型',
                    'item_name_zh': 'ISO 3019-1 (SAE) 2孔型',
                    'supply': 's',
                },
                'D': {
                    'item_name_en': 'ISO 3019-1 (SAE) 4-hole',
                    'item_name_tw': 'ISO 3019-1 (SAE) 4孔型',
                    'item_name_zh': 'ISO 3019-1 (SAE) 4孔型',
                    'supply': 's',
                },
              }  
            },
        '10dn': {
            'name_en': 'Service line port',
            'name_tw': '工作管路油口',
            'name_zh': '工作管路油口',
            'postfix_symbol': '',
            'default_value' : '',
            'model_item_length': 2,
            'model_items_order': ['11', '12', '13', '14'],
            'model_items':{
                '11': {
                    'item_name_en': 'SAE flange port at rear, metric-fastening thread (not for through drive)',
                    'item_name_tw': 'SAE法蘭油口在後方，公制緊固螺紋(不用於通軸驅動)',
                    'item_name_zh': 'SAE法兰油口在后方，公制紧固螺纹(不用于通轴驱动)',
                    'supply': 'n',
                },
                '12': {
                    'item_name_en': 'SAE flange port on opposite side, metric-fastening thread (for through drive)',
                    'item_name_tw': 'SAE法蘭油口在相對側，公制緊固螺紋(用於通軸驅動)',
                    'item_name_zh': 'SAE法兰油口在相对侧，公制紧固螺纹(用于通轴驱动)',
                    'supply': 's',
                },
                '13': {
                    'item_name_en': 'SAE flange port on side, 90°, metric-fastening thread (not for through drive)',
                    'item_name_tw': 'SAE法蘭油口在側面，90°偏置，公制緊固螺紋(不用於通軸驅動)',
                    'item_name_zh': 'SAE法兰油口在侧面，90°偏置，公制紧固螺纹(不用于通轴驱动)',
                    'supply': 'n',
                },
                '14': {
                    'item_name_en': 'UNF threaded ports at rear (not for through drive)',
                    'item_name_tw': '公制螺紋油口在後方(不用於通軸驅動)',
                    'item_name_zh': '公制螺纹油口在后方(不用于通轴驱动)',
                    'supply': 's',
                },
              }  
            },
        '11th': {
            'name_en': 'Through drive',
            'name_tw': '通軸驅動',
            'name_zh': '通轴驱动',
            'postfix_symbol': '',
            'default_value' : '',
            'model_item_length': 3,
            'model_items_order': ['N00', 'K01', 'K52', 'K68', 'K04', 'K15', 'K16', 'K07', 'K24'],
            'model_items':{
                'N00': {
                    'item_name_en': 'Without thought drive',
                    'item_name_tw': '無通軸驅動',
                    'item_name_zh': '无通轴驱动',
                    'supply': 's',
                },
                'K01': {
                    'item_name_en': 'SAE J744 Flange φ82-2 (A), coupling for splined shaft diameter 5/8" 9T 16/32DP',
                    'item_name_tw': 'SAE J744 法蘭 φ82-2 (A) 花鍵軸聯軸器 直徑5/8" 9T 16/32DP',
                    'item_name_zh': 'SAE J744 法兰 φ82-2 (A) 花键轴联轴器 直径5/8" 9T 16/32DP',
                    'supply': 'n',
                },
                'K52': {
                    'item_name_en': 'SAE J744 Flange φ82-2 (A), coupling for splined shaft diameter 5/8" 9T 16/32DP',
                    'item_name_tw': 'SAE J744 法蘭 φ82-2 (A) 花鍵軸聯軸器 直徑3/4" 11T 16/32DP',
                    'item_name_zh': 'SAE J744 法兰 φ82-2 (A) 花键轴联轴器 直径3/4" 11T 16/32DP',
                    'supply': 'n',
                },
                'K68': {
                    'item_name_en': 'SAE J744 Flange φ101-2 (B), coupling for splined shaft diameter 7/8" 13T 16/32DP',
                    'item_name_tw': 'SAE J744 法蘭 φ101-2 (B) 花鍵軸連軸器 直徑7/8" 13T 16/32DP',
                    'item_name_zh': 'SAE J744 法兰 φ101-2 (B) 花键轴联轴器 直径7/8" 13T 16/32DP',
                    'supply': 'n',
                },
                'K04': {
                    'item_name_en': 'SAE J744 Flange φ101-2 (B), coupling for splined shaft diameter 1" 15T 16/32DP',
                    'item_name_tw': 'SAE J744 法蘭 φ101-2 (B) 花鍵軸聯軸器 直徑1" 15T 16/32DP',
                    'item_name_zh': 'SAE J744 法兰 φ101-2 (B) 花键轴联轴器 直径1" 15T 16/32DP',
                    'supply': 'n',
                },
                'K15': {
                    'item_name_en': 'SAE J744 Flange φ127 (C), coupling for splined shaft diameter 1 1/4" 14T 12/24DP',
                    'item_name_tw': 'SAE J744 法蘭 φ127-4 (C) 花鍵軸耦合器 直徑1 1/4" 14T 12/24DP',
                    'item_name_zh': 'SAE J744 法兰 φ127-4 (C) 花键轴联轴器 直径1 1/4" 14T 12/24DP',
                    'supply': 'n',
                },
                'K16': {
                    'item_name_en': 'SAE J744 Flange φ127 (C), coupling for splined shaft diameter 1 1/2" 17T 12/24DP',
                    'item_name_tw': 'SAE J744 法蘭 φ127 (C) 花鍵軸耦合器 1 1/2" 17T 12/24DP',
                    'item_name_zh': 'SAE J744 法兰 φ127 (C) 花键轴联轴器 直径1 1/2" 17T 12/24DP',
                    'supply': 'n',
                },
                'K07': {
                    'item_name_en': 'SAE J744 Flange φ127 (C), coupling for splined shaft diameter 1 1/4" 14T 12/24DP',
                    'item_name_tw': 'SAE J744 法蘭 φ127 (C) 花鍵軸耦合器 1 1/4" 14T 12/24DP',
                    'item_name_zh': 'SAE J744 法兰 φ127 (C) 花键轴联轴器 直径1 1/4" 14T 12/24DP',
                    'supply': 'n',
                },
                'K24': {
                    'item_name_en': 'SAE J744 Flange φ127 (C), coupling for splined shaft diameter 1 1/2" 17T 12/24DP',
                    'item_name_tw': 'SAE J744 法蘭 φ127 (C) 花鍵軸耦合器 1 1/2" 17T 12/24DP',
                    'item_name_zh': 'SAE J744 法兰 φ127 (C) 花键轴联轴器 直径1 1/2" 17T 12/24DP',
                    'supply': 'n',
                },
              }  
            },
        '12sd': {
            'name_en': 'Design No.',
            'name_tw': '特殊代碼',
            'name_zh': '特殊代码',
            'postfix_symbol': '',
            'default_value' : '0',
            'model_item_length': 1,
            'model_items_order': ['0'],
            'model_items':{
                '0': {    # □None
                    'item_name_en': 'None Design No.',
                    'item_name_tw': '無特殊設計',
                    'item_name_zh': '无特殊设计',
                    'supply': 's',
                },
              }  
            },
    }
}
