import json, sys, math
src, out = sys.argv[1], sys.argv[2]
g = json.load(open(src))

def rings(geom):
    if geom['type'] == 'Polygon': return [geom['coordinates']]
    return geom['coordinates']

def centroid(geom):
    # area-weighted centroid of outer rings
    A = cx = cy = 0
    for poly in rings(geom):
        r = poly[0]
        for (x1, y1), (x2, y2) in zip(r, r[1:]):
            c = x1 * y2 - x2 * y1
            A += c; cx += (x1 + x2) * c; cy += (y1 + y2) * c
    if A == 0:
        r = rings(geom)[0][0]; return [sum(p[0] for p in r)/len(r), sum(p[1] for p in r)/len(r)]
    return [cx / (3 * A), cy / (3 * A)]

def simp(r, q=3):
    o = []
    for x, y in r:
        p = [round(x, q), round(y, q)]
        if not o or p != o[-1]: o.append(p)
    if len(o) < 4: return None
    return o

feats = []
for f in g['features']:
    p = f['properties']; geom = f['geometry']
    polys = []
    for poly in rings(geom):
        rr = [s for s in (simp(r) for r in poly) if s]
        if rr: polys.append(rr)
    c = centroid(geom)
    feats.append({'n': p['name'], 'bn': p['bn_name'], 'd': p['district_name'], 'dbn': p['district_bn_name'],
                  'v': p['division_name'], 'vbn': p['division_bn_name'], 'c': [round(c[0], 4), round(c[1], 4)],
                  'g': polys, 'inf': 0})
import os
dd = json.load(open(os.path.join(os.path.dirname(src), 'bd-districts.json')))['districts']
hq = {d['name']: (float(d['long']), float(d['lat'])) for d in dd}
def km(a, b):
    return math.hypot((a[0]-b[0]) * 102, (a[1]-b[1]) * 111)
for f in feats:
    if f['d'] and (f['d'] not in hq or km(f['c'], hq[f['d']]) > 60):
        f['d'] = f['dbn'] = f['v'] = f['vbn'] = ''
known = [f for f in feats if f['d']]
for f in feats:
    if f['d']: continue
    best = min(known, key=lambda k: (k['c'][0]-f['c'][0])**2 + (k['c'][1]-f['c'][1])**2)
    for k in ('d', 'dbn', 'v', 'vbn'): f[k] = best[k]
    f['inf'] = 1
json.dump(feats, open(out, 'w'), ensure_ascii=False, separators=(',', ':'))
print(len(feats), sum(f['inf'] for f in feats))
# hand corrections where nearest-neighbour inference picked the wrong district
fix = {('Badda','Narayanganj'):'Dhaka',('Khilgaon','Narayanganj'):'Dhaka',('Khilkhet','Narayanganj'):'Dhaka',
 ('Dakshinkhan','Narayanganj'):'Dhaka',('Uttar Khan','Narayanganj'):'Dhaka',('Kadamtali','Narayanganj'):'Dhaka',
 ('Demra','Narayanganj'):'Dhaka',('Hatiya','Bhola'):'Noakhali',('Mirsharai','Feni'):'Chattogram',
 ('Kaliakair','Tangail'):'Gazipur',('Manohardi','Gazipur'):'Narsingdi',('Singra','Bogura'):'Natore',
 ('Serajdikhan','Dhaka'):'Munshiganj',('Zanjira','Munshiganj'):'Shariatpur',('Kawkhali (Betbunia)','Chattogram'):'Rangamati',
 ('Naikhongchhari',"Cox's Bazar"):'Bandarban',('Senbagh','Feni'):'Noakhali',('Companiganj','Feni'):'Noakhali',
 ('Roypur','Chandpur'):'Lakshmipur',('Mohammadpur','Faridpur'):'Magura',('Pirganj','Dinajpur'):'Thakurgaon',
 ('Kanthalia','Barguna'):'Jhalokati',('Gangni','Chuadanga'):'Meherpur',('Koyra','Bagerhat'):'Khulna',
 ('Naniarchar','Khagrachari'):'Rangamati',('Baghai Chhari','Khagrachari'):'Rangamati',('Sreepur','Rajbari'):'Magura'}
byname = {d['name']: d for d in dd}
divs = {}
for f in feats:
    if not f['inf'] and f['d'] in byname: divs[byname[f['d']]['division_id']] = (f['v'], f['vbn'])
fixed = 0
for f in feats:
    k = (f['n'], f['d'])
    if f['inf'] and k in fix:
        nd = byname.get(fix[k]) or byname.get(fix[k].replace('Jhalokati','Jhalakathi'))
        if not nd: print('missing', fix[k]); continue
        f['d'], f['dbn'] = nd['name'], nd['bn_name']; f['v'], f['vbn'] = divs[nd['division_id']]; fixed += 1
json.dump(feats, open(out, 'w'), ensure_ascii=False, separators=(',', ':'))
print('fixed', fixed)
