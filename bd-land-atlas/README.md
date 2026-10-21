# Bangladesh Land Check Atlas

Research on verifying land in Bangladesh: who runs each land service, a map of all 544 upazilas, a GPS plot area checker and a buyer's checklist.

- `bangladesh-land-atlas.html` — the finished page. Open it in a browser; it needs no internet except for web fonts.
- `atlas.src.html` — the page source, with `__GEO__` where the boundary data goes.
- `build_gz.py` — turns `data/gazipur-findings.json` (collected with Claude in Chrome on 22 Oct 2026) into the compact Gazipur mouza index the page embeds.
- `data/gazipur-findings.json` — raw portal findings: menu paths, fees, mouza lists, office contacts.
- `build_geo.py` — turns the geoBoundaries upazila GeoJSON (from the `bangladesh-geojson` npm package) into the compact data the page embeds, fills in missing district names and applies hand corrections.

Rebuild:

```sh
npm pack bangladesh-geojson@1.0.0 && tar xzf bangladesh-geojson-1.0.0.tgz
python3 build_geo.py package/src/data/bangladesh.geojson upazilas.json
python3 build_gz.py data/gazipur-findings.json gz_mouzas.json
python3 -c "s=open('atlas.src.html').read(); g=open('upazilas.json').read().replace('</','<\\\\/'); m=open('gz_mouzas.json').read().replace('</','<\\\\/'); open('bangladesh-land-atlas.html','w').write(s.replace('__GEO__',g).replace('__GZM__',m))"
```

Boundaries © geoBoundaries (gbOpen BGD ADM3, 2020), CC BY 4.0, from BBS / OCHA ROAP. No public plot-level (dag) or owner dataset exists; use the official portals listed in the page.
