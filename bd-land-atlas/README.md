# Bangladesh Land Check Atlas

Research on verifying land in Bangladesh: who runs each land service, a map of all 544 upazilas, a GPS plot area checker and a buyer's checklist.

- `bangladesh-land-atlas.html` — the finished page. Open it in a browser; it needs no internet except for web fonts.
- `atlas.src.html` — the page source, with `__GEO__` where the boundary data goes.
- `build_geo.py` — turns the geoBoundaries upazila GeoJSON (from the `bangladesh-geojson` npm package) into the compact data the page embeds, fills in missing district names and applies hand corrections.

Rebuild:

```sh
npm pack bangladesh-geojson@1.0.0 && tar xzf bangladesh-geojson-1.0.0.tgz
python3 build_geo.py package/src/data/bangladesh.geojson upazilas.json
python3 -c "s=open('atlas.src.html').read(); g=open('upazilas.json').read().replace('</','<\\\\/'); open('bangladesh-land-atlas.html','w').write(s.replace('__GEO__',g))"
```

Boundaries © geoBoundaries (gbOpen BGD ADM3, 2020), CC BY 4.0, from BBS / OCHA ROAP. No public plot-level (dag) or owner dataset exists; use the official portals listed in the page.
