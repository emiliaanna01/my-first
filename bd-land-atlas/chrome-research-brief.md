# Research brief for Claude in Chrome: Bangladesh land portals, Gazipur

Paste everything below the line into Claude in Chrome. When it finishes, copy its final JSON block into a file named `gazipur-findings.json`, then paste or upload that file in the Claude Code session that wrote this brief.

---

You are helping me check land records in Gazipur district, Bangladesh. Another Claude session built a land-verification atlas but could not open Bangladeshi government websites from its server. You are running in my Chrome on my own connection, so please open these sites and record what they actually show today.

## Rules

- Read only. Do not pay any fee, submit any application, or create an account.
- Do not type my NID, phone number or any password. If a page needs login, an OTP or payment to go further, stop there and record what you could see before that point.
- Do not try to get past a CAPTCHA. If one blocks you, record `"blocked": "captcha"` and move on.
- Do not collect owner names for any plot except the test lookups I list in Task 9.
- For every fact, record the exact URL you saw it on. If you can't find something, write `"not_found"`. Never guess.
- Keep menu labels exactly as written on the site, in Bangla, with an English gloss.

## Tasks

1. **Portal status.** Open each address below. Record whether it loads, any redirect, the page title and the main services it offers:
   land.gov.bd · dlrms.land.gov.bd · eporcha.gov.bd (does it redirect to dlrms?) · map.land.gov.bd · map.settlement.gov.bd · ldtax.gov.bd · mutation.land.gov.bd · causelist.judiciary.org.bd · rajuk.gov.bd · gazipur.gov.bd · sadar.gazipur.gov.bd · gis.gov.bd

2. **Khatian search path (DLRMS or land.gov.bd).** Go to the khatian search, choose ঢাকা › গাজীপুর › গাজীপুর সদর. Record the exact steps and labels, which surveys the survey dropdown lists for Gazipur Sadar (CS, SA, RS, BS, City Survey, BDS?), and whether you can search by owner name, khatian number and dag number.

3. **Mouza list.** Record the complete mouza dropdown for each of the five Gazipur upazilas (Gazipur Sadar, Kaliakair, Kaliganj, Kapasia, Sreepur), with the JL number if it's shown. Do Gazipur Sadar first. If one survey type gives a different list, say which survey you used.

4. **Plot map viewer.** On map.land.gov.bd (or the web version of Smart Bhumi Naksha), check whether Gazipur Sadar mouzas show plot (dag) outlines. Name 3 example mouzas that do and 3 that don't, and which survey the map comes from.

5. **DLRS map store.** On map.settlement.gov.bd, check which surveys you can order for Gazipur Sadar, the price per sheet, the delivery options, and whether you can view a map online before buying.

6. **Fees.** Find current official fees for: a certified khatian copy (online), a mouza map sheet, an e-mutation (namjari) application, and LD tax payment charges. Record the URL for each.

7. **Court cases.** On causelist.judiciary.org.bd, check whether Gazipur district courts (District Judge, Joint District Judge, Senior Assistant Judge, Chief Judicial Magistrate) are listed, and whether you can search by party name.

8. **Gazipur offices and rules.**
   - Contact pages for the AC Land office of each of the five upazilas and for the Gazipur sub-registry offices, from gazipur.gov.bd or the upazila portals.
   - Any notice about the BDS (Bangladesh Digital Survey) in Gazipur.
   - Whether RAJUK's DAP 2022–2035 map covers any part of Gazipur, and where to look up a plot's land-use zone.

9. **Optional test lookup.** Only if I give you a mouza name and a khatian or dag number below, run that one search. Record the result, but write owner names as initials only.
   - Mouza: ______  Khatian/Dag: ______

## Output

Finish with one JSON code block in exactly this shape, and nothing after it:

```json
{
  "checked_on": "YYYY-MM-DD",
  "portals": [
    {"url": "", "loads": true, "redirects_to": "", "title": "", "services": [""], "blocked": ""}
  ],
  "khatian_search": {
    "portal_url": "", "steps": [""], "surveys_listed_gazipur_sadar": [""],
    "search_by": {"owner_name": true, "khatian_no": true, "dag_no": true}, "notes": ""
  },
  "mouzas": {
    "Gazipur Sadar": [{"name_bn": "", "name_en": "", "jl_no": ""}],
    "Kaliakair": [], "Kaliganj": [], "Kapasia": [], "Sreepur": []
  },
  "mouza_survey_used": "",
  "plot_map_viewer": {"url": "", "shows_dag_outlines": "", "example_with": [""], "example_without": [""], "survey": ""},
  "dlrs_map_store": {"surveys_for_gazipur_sadar": [""], "price_per_sheet_bdt": "", "delivery": [""], "online_preview": "", "source_url": ""},
  "fees": [{"service": "", "amount_bdt": "", "source_url": ""}],
  "court_causelist": {"gazipur_courts_listed": [""], "search_by_party_name": "", "source_url": ""},
  "offices": [{"office": "", "upazila": "", "address": "", "phone": "", "source_url": ""}],
  "bds_gazipur": {"status": "", "mouzas": [""], "source_url": ""},
  "rajuk_dap_gazipur": {"covered": "", "how_to_check_zone": "", "source_url": ""},
  "test_lookup": {"mouza": "", "khatian_or_dag": "", "result_summary": "", "source_url": ""},
  "problems": [""]
}
```
