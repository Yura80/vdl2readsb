import re

parsedefs = [
    {
        # POSN38578W076083,JAY01,033904,195,HED01,034016,ESSSO,M11,321026,89677A
        'pos_re': re.compile(r'^POS([NS]\d{5,6})([EW]\d{5,6}),[^,]*,\d{6},'),
        'pos_format': 'dm',
        'alt_re': re.compile(r'^POS[NS]\d{5,6}[EW]\d{5,6},[^,]*,\d{6},(\d+),'),
        'alt_mul': 100
    },
    {
        # POSN 380202W 754933,-------,0409,3358,,- 43,29132  70,FOB  221,ETA 0710,KPHL,TJSJ,
        'pos_re': re.compile(r'^POS([NS][ 0-9]{6})\d([EW][ 0-9]{6})\d,'),
        'pos_format': 'dm',
        'dep_re': re.compile(r'^POS.*,ETA ?\d{4,6},([0-9A-Z]{4}),[0-9A-Z]{4},'),
        'dst_re': re.compile(r'^POS.*,ETA ?\d{4,6},[0-9A-Z]{4},([0-9A-Z]{4}),'),
        'eta_re': re.compile(r'^POS.*,ETA ?(\d{4}),'),
    },
    {
        # 3N01 POSRPT 0073/18 EHAM/KATL .N503DN
        # /POS N39176W077051/ALT 380/MCH 853/FOB 0384
        # /TME 1609/WND 273 027/OAT -050/TAS 0496/ETA 1726
        #
        # 3701 INRANG 0404/20 MMMX/KJFK .XA-MAT
        # 3A01 OPSCTL 3642/20 KBWI/KAUS .N5179A
        'label': '80',
        'pos_re': re.compile(r'/POS ([NS]\d{5,6})([EW]\d{5,6})/'),
        'pos_format': 'dm',
        'dep_re': re.compile(r'\d [A-Z]{6} +\d+/\d+ ([0-9A-Z]{4})/[0-9A-Z]{4} '),
        'dst_re': re.compile(r'\d [A-Z]{6} +\d+/\d+ [0-9A-Z]{4}/([0-9A-Z]{4}) '),
        'eta_re': re.compile(r'/ETA (\d{4})'),
        'alt_re': re.compile(r'/ALT +(\d{1,3})'),
        'alt_mul': 100,
    },
    {
        # /FB 0087/AD KBOS/N3857.6,W07558.6,3P01 POSRPT  0892/20 KTPA/KBOS .N3062J
        # /UTC 190820/POS N3857.6 W07558.6/ALT 35024
        # /SPD 462/FOB 0087/ETA 1957
        'label': '80',
        'pos_re': re.compile(r'/POS ([NS]\d{4,5}\.\d) ([EW]\d{4,5}\.\d)/'),
        'pos_format': 'dm',
        'alt_re': re.compile(r'/ALT +(\d{4,5})')
    },
    {
        # 3C01 POS N37468W077231  ,,225556,               ,      ,               ,P45,045,0057
        'label': '80',
        'pos_re': re.compile(r'.* POS ([NS]\d{5})([EW]\d{5,6}) *,'),
        'pos_format': 'dm',
    },
    {
        # 76401
        # 02E18KBNAKLGA
        # N38803W07600416113052M037277024G000X2300309B,
        'label': 'H1',
        'pos_re': re.compile(r'76401.*\n.*\n[\S\s]*([NS]\d{5})([EW]\d{6})\d'),
        'pos_format': 'dd',
        'pos_div': 1000,
        'dep_re': re.compile(r'76401.*\n\d{2}.\d{2}([0-9A-Z]{4})[0-9A-Z]{4}'),
        'dst_re': re.compile(r'76401.*\n\d{2}.\d{2}[0-9A-Z]{4}([0-9A-Z]{4})')
    },
    {
        # ...<HEADRTR><FROM>EHAM</FROM><TO>KATL</TO><FNBR>DAL73     </FNBR></HEADRTR>...
        'label': 'H1',
        'sublabel': 'CF',
        'dep_re': re.compile(r'<FROM>([A-Z]{4})</FROM>.*<TO>[A-Z]{4}</TO>'),
        'dst_re': re.compile(r'<FROM>[A-Z]{4}</FROM>.*<TO>([A-Z]{4})</TO>')
    },
    {
        # /EA2003/DSKDCA/SK21
        'label': '30',
        'dst_re': re.compile(r'/EA\d{4}/DS([A-Z]{4})'),
        'eta_re': re.compile(r'/EA(\d{4})/DS[A-Z]{4}')
    },
    {
        # /AERODAT.22,C,1,1,IAD, 39.264, -77.547, 39.229, -77.542,11,309, 30, 15,499,15,31,244,223,4576,0.411,...,.../...8165
        'label': '32',
        'pos_re': re.compile(r'/.*\.\d+,.,.,.,[A-Z]{0,4}, (-?\d+\.\d{1,3}), (-?\d+\.\d{1,3}),'),
        'pos_format': 'dd',
        'pos_div': 1
    },
    {
        # 82,E,KCLT,KEWR,29,22R,170,09,,,0,0,0,0,0,0,,59165,C2ED
        # /AERODAT.22,C,IAD,PVD,23,,6,6,0,150/09,,,45,0,44810,0,0,0,0,B355
        'label': '33',
        'dep_re': re.compile(r'^(?:/AERODAT.)?\d+,[A-Z],([A-Z]{3,4}),[A-Z]{3,4},'),
        'dst_re': re.compile(r'^(?:/AERODAT.)?\d+,[A-Z],[A-Z]{3,4},([A-Z]{3,4}),')
    },
    {
        'label': '35',
        'dep_re': re.compile(r'^(?:/AERODAT.)?\d+,[A-Z],([A-Z]{3,4}),[A-Z]{3,4},'),
        'dst_re': re.compile(r'^(?:/AERODAT.)?\d+,[A-Z],[A-Z]{3,4},([A-Z]{3,4}),')
    },
    {
        # /KAUS.TI2/040KAUSA4CFA
        'label': 'B9',
        'dst_re': re.compile(r'^/([0-9A-Z]{4})\.')
    },
    {
        # PRG/FNDAL2697/DTKBDL,15O,97,172511,30EB38
        'label': 'H1',
        'dst_re': re.compile(r'^PRG.*/DT([0-9A-Z]{4}),'),
        'eta_re': re.compile(r'^PRG.*/DT[0-9A-Z]{4},[^,]+,[^,]+,(\d{4})')
    },
    {
        # S/N L:000000            DEPART:KMCO   DEST:KEWR
        'label': 'H1',
        'dep_re': re.compile(r' DEPART:([0-9A-Z]{4}) '),
        'dst_re': re.compile(r' DEST:([0-9A-Z]{4})')
    },
    {
        # A320,043656,1,2,TB000000/REP026,84,01,4/CC      ,SEP20,225312,KBWI,KDTW,8080/C0TWP020KS010400/C111,83000,4000,
        # A350,000113,1,1,TB000000/REP035,01,02;H01,035,01,02,4000,00137,.D-AIXM,3,0,21,09,21,02,44,57,071/H02,KIAD EDDM,DLH415
        'label': 'H1',
        'dep_re': re.compile(r',TB000000/REP0..,[^,]*,[^,]*,[^,]*,[^,]*,\d{6},([A-Z]{4}),[A-Z]{4},'),
        'dst_re': re.compile(r',TB000000/REP0..,[^,]*,[^,]*,[^,]*,[^,]*,\d{6},[A-Z]{4},([A-Z]{4}),')
    },
    {
        # A321,047801,1,1,TB000000/REP239,00,00,4/239N312DN0419092121040630786N38203W 77328369-24-51287 24T 0510 146
        # 40 255 468 000549030      KATLKBOS
        'label': 'H1',
        'dep_re': re.compile(r',TB000000/REP239,.*\n*.*([A-Z]{4})[A-Z]{4}$'),
        'dst_re': re.compile(r',TB000000/REP239,.*\n*.*[A-Z]{4}([A-Z]{4})$')
    },
    {
        # ++86501, N8811,B7378MAX,210920,WN4923,KBWI,TJSJ,0284,SMX47-2102-0000
        # 74302,7878,B737-700,210920,WN3616,KBWI,KMCI,0300,SW2102
        # ++76502,XXX,B737-800,210920,WN4133,KDTW,KBWI,0285,SW2102
        'label': 'H1',
        'dep_re': re.compile(r'^[^,]*,[^,]*,B7\d\d[^,]*,\d{6},[0-9A-Z\-]*,([A-Z]{4}),[A-Z]{4},\d{4},'),
        'dst_re': re.compile(r'^[^,]*,[^,]*,B7\d\d[^,]*,\d{6},[0-9A-Z\-]*,[A-Z]{4},([A-Z]{4}),\d{4},')
    },
    {
        # A5E6210319PHL SDF N39547W0755831733M036202006G2880N39546W076015183
        # D3M321KSEAKBWIN39258W07723020491272P004188022G0009N39257W077193205
        'label': 'H1',
        'dep_re': re.compile(r'^[0-9A-Z]+\d([A-Z]{3}[ A-Z])[A-Z]{3}[ A-Z][NS]\d{5}[EW]\d{6}\d{4}'),
        'dst_re': re.compile(r'^[0-9A-Z]+\d[A-Z]{3}[ A-Z]([A-Z]{3}[ A-Z])[NS]\d{5}[EW]\d{6}\d{4}'),
        # match only the last lat/lon pair
        'pos_re': re.compile(r'^[0-9A-Z]+\d[A-Z]{3}[ A-Z][A-Z]{3}[ A-Z][NS]\d{5}[EW]\d{6}\d{4}[\s\S]*([NS]\d{5})([EW]\d{6})'),
        'pos_format': 'dm'
    },
    {
        # FPN/RI:DA:KCLT:AA:KJFK:CR:CLTJFK01(13L)..KALDA.J121.SIE:A:CAMRN4:F:CAMRN..DISCO..ASALT:AP:RNVZ 13L:F:HIRBOA8CD
        'label': 'H1',
        'dep_re': re.compile(r'FPN/RI:DA:([0-9A-Z]{4}):AA:[0-9A-Z]{4}:'),
        'dst_re': re.compile(r'FPN/RI:DA:[0-9A-Z]{4}:AA:([0-9A-Z]{4}):')
    },
    {
        # APM    1 G-ZBKK         BAW293  EGLLKIAD200921165939
        # APM    2 SU-GES         MSR981  HECAKIAD210921003805
        'label': 'H1',
        'dep_re': re.compile(r'APM    \d [0-9A-Z\-]+ +[0-9A-Z\-]+ +([A-Z]{4})[A-Z]{4}\d{12}'),
        'dst_re': re.compile(r'APM    \d [0-9A-Z\-]+ +[0-9A-Z\-]+ +[A-Z]{4}([A-Z]{4})\d{12}')
    },
    {
        # EGLL,KIAH,201624, 39.74,- 76.38,40001,254,-119.5, 19300
        # MMMX,KJFK,201625, 37.94,- 75.58,39001,266,  47.2,  9300
        # position is not precise enough
        'label': '83',
        'alt_re': re.compile(r'^[A-Z]{4},[A-Z]{4},\d{6},[ \-\.0-9]*,[ \-\.0-9]*,(\d{1,5})'),
        'dep_re': re.compile(r'^([A-Z]{4}),[A-Z]{4},'),
        'dst_re': re.compile(r'^[A-Z]{4},([A-Z]{4}),')
    },
    {
        # /N38.268/W078.117/10/0.74/235/400/KHOU/1625/0073/00016/MOL  /PSK  /1405/YICUT/1357/
        'label': '10',
        'pos_re': re.compile(r'/([NS]\d{2,3}\.\d{1,3})/([EW]\d{2,3}\.\d{1,3})/\d+/[^/]+/\d+/\d+/[0-9A-Z]{4}/'),
        'pos_format': 'dd',
        'dst_re': re.compile(r'/[NS]\d{2,3}\.\d{1,3}/[EW]\d{2,3}\.\d{1,3}/\d+/[^/]+/\d+/\d+/([0-9A-Z]{4})/'),
        'eta_re': re.compile(r'/[NS]\d{2,3}\.\d{1,3}/[EW]\d{2,3}\.\d{1,3}/\d+/[^/]+/\d+/\d+/[0-9A-Z]{4}/(\d{4})/')
    },
    {
        # MRB-13 ,N 39.643,W  77.299,33999,0486,1448,036\\TS132657,200921
        # HYPER  ,N 39.721,W 76.997,12463,314,1954,016\\TS194025,200921
        # 134234,32304,1439,  68,N 39.523 W 76.324
        # N 38.887,W 77.064,927,5, 368
        'label': '16',
        'pos_re': re.compile(r'([NS] *\d+\.\d{1,3})[, ]([EW] *\d+\.\d{1,3})'),
        'pos_format': 'dd',
        'pos_div': 1,
        'alt_re': re.compile(r'[NS] *\d+\.\d{1,3},[EW] *\d+\.\d{1,3}, *(\d{2,5})')
    },
    {
        # POS02,N38228W077029,371,KVPC,KTEB,0920,2212,2257,008.1
        # POS02,N38596 W075144,373,KTEB,MYNN,0920,2213,0013,*****
        # 00POS03,N39393W078152,330,KBWI,KRST,0920,2210,0001,004.8
        'label': '44',
        'pos_re': re.compile(r'.*POS.*,([NS]\d{5}) ?([EW]\d{5,6}),'),
        'pos_format': 'dm',
        'dep_re': re.compile(r'.*POS.*,[NS]\d{5} ?[EW]\d{5,6},\d+,([A-Z]{4}),[A-Z]{4}'),
        'dst_re': re.compile(r'.*POS.*,[NS]\d{5} ?[EW]\d{5,6},\d+,[A-Z]{4},([A-Z]{4})'),
        'eta_re': re.compile(r'.*POS.*,[NS]\d{5} ?[EW]\d{5,6},\d+,[A-Z]{4},[A-Z]{4},\d{4},\d{4},(\d{4})')
    },
    {
        # INR02,KJFK,0,0,0,,,,,
        'label': '44',
        'dst_re': re.compile(r'^INR..,([0-9A-Z]{4}),')
    },
    {
        # /ET EXP TIME       / KEWR KMCO 20 003427/EON 0220 AUTO
        # /B6 LDG DATA REQ   / TNCA KEWR 20 002314 KEWR R29
        # /C3 GATE REQ       / KIAD KEWR 20 222300 1156 ---- ---- ---- ----
        'label': '5Z',
        'dep_re': re.compile(r'^/\w{2} [^/]* / ([A-Z]{4}) [A-Z]{4} '),
        'dst_re': re.compile(r'^/\w{2} [^/]* / [A-Z]{4} ([A-Z]{4}) '),
        'eta_re': re.compile(r'^/ET [^/]* / [A-Z]{4} [A-Z]{4} .*/EON (\d{4})')
    },
    {
        # OS KBDL /ALT00000351
        # OS KDCA /IR KDCA0311
        'label': '5Z',
        'dst_re': re.compile(r'^OS ([A-Z]{4}) /[A-Z]+'),
    },
    {
        # KADWKMVY154721SEP21
        # KDCAKMIA1907OS KMIA /FUL0258
        'label': 'QQ',
        'dep_re': re.compile(r'^([A-Z]{4})[A-Z]{4}\d'),
        'dst_re': re.compile(r'^[A-Z]{4}([A-Z]{4})\d'),
    },
    {
        # 202339 KATL KEWR7
        # any label
        'dep_re': re.compile(r'^\d{6} ([A-Z]{4}) [A-Z]{4}\d(?:$|\r|\n)'),
        'dst_re': re.compile(r'^\d{6} [A-Z]{4} ([A-Z]{4})\d(?:$|\r|\n)'),
    },
    {
        # 200224  ATL  HPN0
        # any label
        'dep_re': re.compile(r'^\d{6}  ([A-Z]{3})  [A-Z]{3}\d(?:$|\r|\n)'),
        'dst_re': re.compile(r'^\d{6}  [A-Z]{3}  ([A-Z]{3})\d(?:$|\r|\n)'),
    },
    {
        # LDR01,189,C,SWA-2600-013,0,N 38.722,W 76.705,8358,  8.6,KMCO,KBWI,KBWI,15R/,/,/,0,0,,,,,,,0,0,0,00,,119.2,08.0,127.2,----.,,
        # 28,E,21SEP21,161812,N 38.851,W 76.603,32422,  8680,KTPA,KEWR,KEWR,22L/,/,,,,,,,,0,0,0,0,0,0,0,,120.0,006.9,
        # 212,F,20,20SEP21,180912,N 37.456,W 76.698,36060,  80,KABE,KMYR,KMYR,18/,36/,,,,,6,,6,,1,0,0,0,0,0,,,,,120.5,005.8
        'pos_re': re.compile(r',([NS] *\d{1,3}\.\d{3}),([EW] *\d{1,3}\.\d{3}), *\d{1,5}. *[0-9\.]+,[A-Z]{4},[A-Z]{4},[A-Z]{4},'),
        'pos_format': 'dd',
        'pos_div': 1,
        'alt_re': re.compile(r',[NS] *\d{1,3}\.\d{3},[EW] *\d{1,3}\.\d{3}, *(\d{1,5}). *[0-9\.]+,[A-Z]{4},[A-Z]{4},[A-Z]{4},'),
        'dep_re': re.compile(r',[NS] *\d{1,3}\.\d{3},[EW] *\d{1,3}\.\d{3}, *\d{1,5}. *[0-9\.]+,([A-Z]{4}),[A-Z]{4},[A-Z]{4},'),
        'dst_re': re.compile(r',[NS] *\d{1,3}\.\d{3},[EW] *\d{1,3}\.\d{3}, *\d{1,5}. *[0-9\.]+,[A-Z]{4},([A-Z]{4}),[A-Z]{4},')
    }
]
