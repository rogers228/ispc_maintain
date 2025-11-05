# 產品選型規則

# . 代表任何字
# + 代表1次以上
# * 代表0此以上
# ? 代表0或1次
# .{n} 代表n次  .{n}(S11|S12).+

# ZFHxgESDRiG0  V系列

# index:0  01sr   length front:0  self:1  back:23
# index:1  02dp   length front:1  self:3  back:20
# index:2  03ct   length front:4  self:3  back:17
# index:3  04pa   length front:7  self:1  back:16
# index:4  05cr   length front:8  self:1  back:15
# index:5  06dn   length front:9  self:2  back:13
# index:6  07axv  length front:11 self:3  back:10
# index:7  08vo   length front:14 self:1  back:9
# index:8  09tg   length front:15 self:2  back:7
# index:9  10th   length front:17 self:1  back:6
# index:10 11egv  length front:18 self:2  back:4
# index:11 12ln   length front:20 self:2  back:2
# index:12 13se   length front:22 self:1  back:1
# index:13 14sd   length front:23 self:1  back:0

dic_input = {
    # 主動選型規則(5個參數) (單一選項  將互相針對) ;
    'both' : [
        '02dp  [023, 025, 050, 070];           -u 03ct  [HLA, HLB]',
        '03ct  [00B, 00C, 0CG, 0CR, 00F, 0FG]; -u 10th  [C, D, E, F, I, J, K, L]',
        '03ct  [HQA, HQB, HQC, HKA, HKB, HKC]; -u 06dn  [0B, B2]',
        '04pa  [4];                            -u 02dp  [050, 070]',
        '08vo  [0];                            -s 03ct  [00A, 00G, HLA, HLB, HLC, 00B, 00C, 0CG, 0GM, 0GM, 0GA, 0LN]',
        '08vo  [A, B, C, D, E, F];             -s 03ct  [0CR, 00D, 0DG, 00E, 0EG, 00F, 0FG, 0GJ, 0GR, 0GB, 0GC, HQA, HQB, HQC, HKA, HKB, HKC]',
        '10th  [E];                            -u 02dp  [008, 010, 012, 015, 018]',
        '11egv [X1];                           -u 04pa  [3, 4]',
        '12ln  [0A, 01];                       -s 02dp  [008, 010, 012, 015, 018]',
        '12ln  [02];                           -s 02dp  [023, 025, 038, 042, 050, 070]',
        '02dp  [008, 010, 012, 015, 018];      -s 07axv [001, 00S, 0S1, 0S2]',
        '02dp  [023, 025];                     -s 07axv [002, 0S3, 0S4, 0S5]',
        '02dp  [038, 042];                     -s 07axv [003, 0S6, 0S7, 0S8]',
        '02dp  [050, 070];                     -s 07axv [004, 0S9, S10]',
        '06dn  [0B];                           -u 02dp  [008, 010, 012, 015, 018]',
        '06dn  [B2];                           -u 02dp  [008, 010, 012, 015, 018, 050, 070]',
        '06dn  [0B, B2];                       -u 03ct  [00D, 0DG, 00E, 0EG, HKA, HKB, HKC, HQA, HQB, HQC]',
    ],

    # 主動選型規則(4個參數)
    'lion': [
        # 型號表達式 ; 1:mode -u不能選|-s僅能選  2 lion_model 3 items
        '^.{8}(L).+;                                           -s 11egv [0X, X1]',
        '^.{4}(00C|0CG|0CR|00D|0DG|00E|0EG|00F|0FG).+;         -u 05cr  [L]',
        '^.{4}(00B|00C|0CG|0CR|00F|0FG).+;                     -s 10th  [0]',
        '^.{4}(HQA|HQB|HQC|HKA|HKB|HKC).+;                     -s 06dn  [01]',
        '^.{7}(3|4).+;                                         -u 11egv [X1]',
        #'^.{9}(0B).+;                      -s 02dp  [023, 025, 038, 042, 050, 070]',
        #'^.{9}(B2).+;                      -s 02dp  [023, 025, 038, 042]',
        #'^.{9}(0B|B2).+;                   -u 03ct  [00D, 0DG, 00E, 0EG, HQA, HQB, HQC, HKA, HKB, HKC]',
        # '.(008|010|012|015|018).+;        -s 07axv [001, 00S, 0S1, 0S2]',
        # '.(023|025).+;                    -s 07axv [002, 0S3, 0S4, 0S5]',
        # '.(038|042).+;                    -s 07axv [003, 0S6, 0S7, 0S8]',
        # '.(050|070).+;                    -s 07axv [004, 0S9, S10]',
        # '.(008|010|012|015|018).+;        -s 12ln  [0A, 01]',
        # '.(023|025|038|042|050|070).+;    -s 12ln  [02]',
        # '.(050|070).+;                    -u 03ct  [HLA, HLB]', # 吻合23碼(排量為50或70時) 03控制 不能選擇 HLA, HLB
        # '.(023|025).+;                    -u 03ct  [HLA, HLB]', # 吻合23碼(排量為50或70時) 03控制 不能選擇 HLA, HLB
        # '.{7})(4).+;                      -u 02dp  [050, 070]',
        # '.{14}(0).+;                      -s 03ct  [00A, 00G, HLA, HLB, HLC, 00B, 00C, 0CG, 0GM, 0GM, 0GA, 0LN]',
        # '.{14}(A|B|C|D|E|F).+;            -s 03ct  [0CR, 00D, 0DG, 00E, 0EG, 00F, 0FG, 0GJ, 0GR, 0GB, 0GC, HQA, HQB, HQC, HKA, HKB, HKC]',
        # '.{17}(E).+;                      -u 02dp  [008, 010, 012, 015, 018]',
    ],

# 碼數
# 01 02 03 04 05 06 07 08 09 10 11 12 13 14
# 1  3  3  1  1  2  3  1  2  1  2  2  1  1
# 1  4  7  8  9  11 14 15 17 18 20 22 23 24

    # 篩選規則 4個參數 (篩選後僅顯示)
    'filter': [
        '^.(050|070).+;                       07axv [004, 0S9, S10]',    # 吻合234碼(排量為50或70時) 07軸心 篩選 004, 0S9, S10 其它將不顯示
        '^.(038|042).+;                       07axv [003, 0S6, 0S7, 0S8]',
        '^.(023|025).+;                       07axv [002, 0S3, 0S4, 0S5]',
        '^.(008|010|012|015|018).+;           07axv [001, 0S1, 0S2]',
        '^.{20}(0A|01).+;                     02dp  [008, 010, 012, 015, 018]',
        '^.{20}(02).+;                        02dp  [023, 025, 038, 042, 050, 070]',
        #'^.(050|070).+;                       03ct  [00A, 00G, HLC, 00C, 0CG, 0CR, 00D, 0DG, 00E, 0EG, 00F, 0FG, 0GA, 0GM, 0GJ, 0GR, 0GB, 0GC, HQA, HQB, HQC, HKA, HKB, HKC, 0LN]',
        #'^.(050|070).+;                       04pa  [1, 2, 3]',
        #'^.{4}(00B|00C|0CG|0CR|00F|0FG).+;    10th  [0]',
        #'^.{4}(HQA|HQB|HQC|HKA|HKB|HKC).+;    06dn  [01]',
        #'^.{8}(L).+;                          11egv [0X]',
        #'^.{8}(L).+;                          03ct  [00A, 00G, HLA, HLB, HLC, 0GA, 0GM, 0GJ, 0GR, 0GB, 0GC, HQA, HQB, HQC, HKA, HKB, HKC, 0LN]',
        #'^.{14}(0).+;                         03ct  [00A, 00G, HLA, HLB, HLC, 00B, 00C, 0CG, 0GM, 0GA, 0LN]',
        #'^.{14}(A|B|C|D|E|F).+;               03ct  [0CR, 00D, 0DG, 00E, 0EG, 00F, 0FG, 0GJ, 0GR, 0GB, 0GC, HQA, HQB, HQA, HKA, HKB, HKC]',
        #'^.{17}(E).+;                         02dp  [023, 025, 038, 042, 050, 070]',
        #'^.{18}(X1).+;                        04pa  [1, 2]',
    ],

    # 別名規則 3個參數
    'alias': [
        '02dp 008 8',   # 02排量 的選型 008  將顯示別名 8
        '02dp 010 10',
        '02dp 012 12',
        '02dp 015 15',
        '02dp 018 18',
        '02dp 023 23',
        '02dp 025 25',
        '02dp 038 38',
        '02dp 042 42',
        '02dp 050 50',
        '02dp 070 70',
        '03ct 00A A',
        '03ct 00G G',
        '03ct 00B B',
        '03ct 00C C',
        '03ct 0CG CG',
        '03ct 0CR CR',
        '03ct 00D D',
        '03ct 0DG DG',
        '03ct 00E E',
        '03ct 0EG EG',
        '03ct 00F F',
        '03ct 0FG FG',
        '03ct 0GA GA',
        '03ct 0GM GM',
        '03ct 0GJ GJ',
        '03ct 0GR GR',
        '03ct 0GB GB',
        '03ct 0GC GC',
        '03ct 0LN LN',
        '06dn 01 □None',
        '06dn 0B B',
        '07axv 001 □Key',
        '07axv 002 □Key',
        '07axv 003 □Key',
        '07axv 004 □Key',
        '07axv 00S S',
        '07axv 0S1 S1',
        '07axv 0S2 S2',
        '07axv 0S3 S',
        '07axv 0S4 S1',
        '07axv 0S5 S3',
        '07axv 0S6 S',
        '07axv 0S7 S1',
        '07axv 0S8 S3',
        '07axv 0S9 S',  # 07軸心 的選型 0S9  將顯示別名 S
        '07axv S10 S1', # 07軸心 的選型 S10 將顯示別名 S1
        '08vo 0 □None',
        '10th 0 □None',
        '11egv 0X X',
        '11egv 0Z Z',
        '12ln 0A A',
        '12ln 01 □None',
        '12ln 02 □None',
        '13se 0 □None',
        '14sd 0 □None',
    ],

    # supply 指定供貨規則
    'supply': [
        '^.(023|025)(00F|0FG|00D|0DG).+;   06dn [0B, B2] n ',    # 符合規則(正則表達式)時 06 配管方向 選項 B,B2的 供貨規則 指定為n
        '^.{15}(60).+;                     03ct  [HQA, HQB, HQC, HKA, HKB, HKC] d ',
        '^(V).+;                           10th  [C,F,I,J,K,L] n ',
        '^(V).+;                           09tg  [70] n ',
        '^(V).+;                           07axv [S10] n ',
    ],

    # fast_model 快速選型  (完整型號 空格區隔 不可相連)
    'fast_model' : [
        # 系列  排量  控制  壓力  旋轉   配管  軸心    電壓   牙型  通軸   特規   連接  油封   特殊代碼
        # 01sr 02dp  03ct  04pa  05cr  06dn  07axv   08vo  09tg  10th  11egv  12ln  13se  14sd
        '   V   015   00A   1     R    01    001     0     10     0    X1     0A     0     0', #V15A1R10X1A
        '   V   015   00A   2     R    01    001     0     10     0    0X     0A     0     0', #V15A2R10XA
        '   V   015   00A   3     R    01    001     0     10     0    0X     0A     0     0', #V15A3R10XA
        '   V   015   00A   4     R    01    001     0     10     0    0X     0A     0     0', #V15A4R10XA
        '   V   015   HLC   4     R    01    001     0     40     0    0X     01     0     0', #V15HLC4R40X
        '   V   023   00A   3     R    01    002     0     10     0    0X     02     0     0', #V23A3R10X
        '   V   023   00A   4     R    01    002     0     10     0    0X     02     0     0', #V23A4R10X
        '   V   023   00F   4     R    01    002     F     10     0    0X     02     0     0', #V23F4RF10X
        '   V   023   HLC   4     R    01    002     0     40     0    0X     02     0     0', #V23HLC4R40X
        '   V   023   0CR   2     R    01    002     F     10     0    0X     02     0     0', #V23CR2RF10X
        '   V   025   00A   4     R    01    002     0     10     0    0X     02     0     0', #V25A4R10X
        '   V   025   00A   4     R    01    002     0     40     0    0X     02     0     0', #V25A4R40X
        '   V   025   00G   4     R    01    002     0     40     0    0X     02     0     0', #V25G4R40X
        '   V   038   00A   1     R    01    003     0     10     0    0X     02     0     0', #V38A1R10X
        '   V   038   00A   3     R    01    003     0     10     0    0X     02     0     0', #V38A3R10X
        '   V   038   00A   4     R    01    003     0     10     0    0X     02     0     0', #V38A4R10X
        '   V   038   00A   4     R    0B    003     0     40     0    0X     02     0     0', #V38A4RB40X
        '   V   038   HLC   4     R    01    0S6     0     40     0    0X     02     0     0', #V38HLC4RS40X
        '   V   042   00A   4     R    01    003     0     10     0    0X     02     0     0', #V42A4R10X
        '   V   042   00C   4     R    01    003     0     10     0    0X     02     0     0', #V42C4R10X
        '   V   042   HLC   4     R    01    003     0     40     0    0X     02     0     0', #V42HLC4R40X
        '   V   042   HLC   4     R    0B    003     0     40     0    0X     02     0     0', #V42HLC4RB40X
        '   V   042   0CR   3     R    01    003     F     10     0    0Z     02     0     0', #V42CR3RF10Z
        '   V   042   00A   4     R    01    0S6     0     40     D    0X     02     0     0', #V42A4RS40DX
        '   V   050   00A   3     R    01    004     0     10     0    0X     02     0     0', #V50A3R10X
        '   V   050   00C   3     R    01    004     0     10     0    0X     02     0     0', #V50C3R10X
        '   V   050   0FG   3     R    01    004     F     10     0    0X     02     0     0', #V50FG3RF10X
        '   V   070   00A   3     R    01    004     0     10     0    0X     02     0     0', #V70A3R10X
        '   V   070   00A   3     R    0B    004     0     60     0    0X     02     0     0', #V70A3RB60X
        '   V   070   HLC   3     R    01    004     0     40     0    0X     02     0     0', #V70HLC3R40X
    ],

    # 隱藏規則(尚未處理)
    'pdmodel_hide': [
        '07axv [001, 002, 003, 004]',   # 07軸心 的選型 00 無記號 將隱藏  (在最後的型號顯示時)
        '06dn 01',
        '08vo 0',
        '10th 0',
        '12ln [01, 02]',
        '13se 0',
        '14sd 0',
    ],

}
