# Compact Gazipur mouza index from the Claude in Chrome findings (DLRMS RS lists + other surveys)
import json, sys
d = json.load(open(sys.argv[1]))
AREA = {'Gazipur Sadar': 0, 'Kaliakair': 1, 'Kaliganj': 2, 'Kapasia': 3, 'Sreepur': 4}
TONGI = 5
BN2 = str.maketrans('০১২৩৪৫৬৭৮৯', '0123456789')
rows = {}
def add(area, name, jl, sv):
    name = name.strip()
    if not name or name.translate(BN2).isdigit(): return
    k = (area, name)
    r = rows.setdefault(k, {'a': area, 'n': name, 'jl': jl.rstrip('.'), 's': []})
    if sv not in r['s']: r['s'].append(sv)
for key, lst in d['mouzas'].items():
    area = TONGI if key.startswith('Tongi') else AREA[key]
    for m in lst: add(area, m['name_bn'], m['jl_no'], 'RS')
for key, lst in d['extra']['mouzas_other_surveys'].items():
    area = TONGI if key.startswith('Tongi') else AREA[key.split(' ')[0] if not key.startswith('Gazipur') else 'Gazipur Sadar']
    sv = next(t for t in key.split(' ') if t in ('CS', 'SA', 'BDS'))
    for m in lst: add(area, m['name_bn'], m['jl_no'], sv)
out = [[r['a'], r['n'], r['jl'], ''.join(x[0] for x in ['RS' in r['s'] and 'R', 'SA' in r['s'] and 'S', 'CS' in r['s'] and 'C', 'BDS' in r['s'] and 'B'] if x)] for r in rows.values()]
json.dump(out, open(sys.argv[2], 'w'), ensure_ascii=False, separators=(',', ':'))
from collections import Counter
print(len(out), Counter(o[0] for o in out), Counter(o[3] for o in out))
