"""Step 14: README.md, LICENSE and reddit/post.md, every number from data/results.json."""
from common import *

R = jload(f"{DATA}/results.json"); x = R["x"]; S = R["sample"]
def c(v, d=2): return f"{v['rr']:.{d}f} (95% CI {v['lo']:.{d}f} to {v['hi']:.{d}f})"
readme = f"""# Two faces of the constituency

What MPs name on Facebook and in the House of Commons, February 2017 to October 2020. For the same MPs, months and pre-specified places, how often their Facebook posts and their spoken Commons contributions name the towns and villages in their own seat.

Interactive page: {PAGE}
Paper: {{https://doi.org/10.5281/zenodo.24105795}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/janus-places/}}
Code and data: {REPO}

**The window.** The CrowdTangle export reached its 300,000-row cap ({S['csv_rows']:,} rows), so the Facebook posts start on 11 February 2017. Everything covers February 2017 to October 2020, not 2010 to 2020.

## Headline results

- Sample: {S['spells']} MP-seat spells ({S['mps']} MPs, {S['seats']} seats) with items in both venues; {S['posts']:,} Facebook posts with a message and {S['contributions']:,} spoken Commons contributions; {S['queries']:,} Hansard queries fixed in advance.
- MPs named their own seat's places {x['fb_per100']:.1f} times per 100 Facebook posts and {x['cm_per100']:.1f} times per 100 Commons contributions. Within MP and month the Facebook to Commons rate ratio is {c(R['H1'])}. {R['mp']['fb_higher']} of {R['mp']['n']} MPs with at least 20 items in each venue had the higher rate on Facebook.
- Placebo, places in another MP's seat: rate ratio {c(R['placebo'])}.
- Which places: the population elasticity of naming is {R['H2']['el_commons']:.2f} in the Commons and {R['H2']['el_fb']:.2f} on Facebook (difference {R['H2']['diff']:.2f}, CI {R['H2']['diff_lo']:.2f} to {R['H2']['diff_hi']:.2f}): Facebook is louder, not differently shaped. Seat-name places: ratio {R['H2']['rr_seat']:.1f}; other places {R['H2']['rr_noseat']:.1f}.
- Office: in frontbench months the Commons rate falls by {x['front_cm_drop_pc']:.0f}% (CI {x['front_cm_lo_pc']:.0f}% to {x['front_cm_hi_pc']:.0f}%) and the Facebook rate does not change ({c(R['H4']['front_facebook'])}).
- Marginal seats (majority under 10 points): a smaller gap, {c(R['H3']['marginal'])} times as large. Government side: {c(R['H4']['gov'])}.
- COVID months: Facebook local rate down {x['covid_fb_drop_pc']:.0f}% (exploratory). Brexit months: no clear change in either venue.
- {R['robust_range']['n']} robustness checks: ratios from {R['robust_range']['min']:.1f} to {R['robust_range']['max']:.1f}, all with intervals above 1.

## Files

| File | What it is |
|---|---|
| `index.html`, `js/page.js` | Interactive page: MapLibre on OpenFreeMap Positron; 2010 seats coloured by the Facebook minus Commons gap (or either rate), search for seats, MPs and places, layers, full screen, popups with each queried place's counts in both venues. |
| `header.png` | Social card, 1200 x 630. |
| `hansard_queries.json` | The {S['queries']:,} queries fixed before any Commons data: member, Parliament member id, seat, place, exact phrase, group, sample weight, dates. |
| `hansard_counts.json` | Monthly counts returned by the Hansard API for each query (absent months are 0). |
| `data/pages.csv`, `data/pages_raw.csv` | Every page in the list with post counts and the MP match (or the reason for exclusion). Hand decisions in `code/page_overrides.json`. |
| `data/commons_memberships.csv`, `data/frontbench_posts.csv` | Commons memberships and frontbench post categories in the window (parlparse). |
| `data/seat_places.csv` | Place list per 2010 seat with population, flags and the reason for each flag. |
| `data/fb_mp_months.csv`, `data/fb_place_counts.csv`, `data/fb_placebo_counts.csv`, `data/fb_outside.json` | Facebook counts only: posts per MP-month, posts naming each place, placebo places, posts outside membership. |
| `data/panel_months.csv`, `data/panel_places.csv`, `data/mp_covariates.csv`, `data/mp_gap.csv`, `data/monthly.csv` | Analysis panels and per-MP rates. |
| `data/models.csv`, `data/results.json`, `data/results_models.json` | Every estimate; every number quoted anywhere. |
| `data/seats_map.geojson`, `data/site.json` | Page data. |
| `code/` | Scripts in order, templates, `qa.js`. |
| `release/` | Paper (PDF, LaTeX, figures, `cover_note.md`), blog post and figures, Zenodo files. |
| `reddit/` | Collage, its script, the looping GIF and the post text. |
| `NOTES.md` | Working notes and the analysis plan, written before any Commons data. |

## Method in brief

- Pages: CrowdTangle list built by the author, exported October 2020; matched to Commons memberships (parlparse, with Parliament member ids) by cleaned name and by hand; posts kept only on days the MP held the seat.
- Places: Wikidata settlements, the *Mentioned in the House* places and the seat's own name, assigned to 2010 seats; ambiguous names searched as "in <place>" in both venues; whole-word, case-insensitive matching in both.
- Query list per MP-seat: seat-name places, eight most populous other places, a random five (weighted), up to three most-named Facebook places (descriptive only), two placebo places, total contributions.
- Model: PPML of place-naming counts with spell and month fixed effects and log items as offset, errors clustered by spell (pyfixest). Planned interactions for marginality, frontbench, government side and periods; 15 robustness checks; placebo.

## How to rerun

Needs Python 3 with pandas, numpy, pyfixest, statsmodels, scipy, shapely, pyproj, matplotlib, Pillow, wordfreq; xelatex; node with Playwright for QA. Inputs are listed in `code/common.py`; the CrowdTangle export is not shared (only counts are).

```
python3 code/00_pages_raw.py      # page list from the export (names and counts only)
python3 code/01_members.py        # Commons memberships (parlparse people.json)
python3 code/01b_posts.py         # frontbench posts (parlparse ministers-2010.json)
python3 code/02_match_pages.py    # page to MP matching
python3 code/03_places.py         # place lists per seat
python3 code/04_fb_counts.py      # Facebook counts (streams the export)
python3 code/04b_fb_placebo.py    # Facebook counts for placebo places
python3 code/05_queries.py        # Hansard query list (before any Commons data)
python3 code/06_panel.py          # join with hansard_counts.json
python3 code/07_models.py         # all models
python3 code/08_results.py        # results.json
python3 code/09_site_data.py      # map data
python3 code/10_figures.py        # figures and header
python3 code/11_paper.py          # paper (DOI=10.5281/zenodo.N to fill the DOI)
python3 code/12_site.py           # index.html
python3 reddit/collage.py
python3 code/14_readme.py         # README, LICENSE, Reddit post
python3 code/13_release.py        # blog post, Zenodo files
```

## Sources and licences

- Facebook: the author's CrowdTangle list of UK MPs' pages (CrowdTangle, Meta), exported October 2020. Only aggregate counts are published; no post text, links or URLs.
- Hansard, House of Commons, via the UK Parliament Hansard API: contains Parliamentary information licensed under the Open Parliament Licence v3.0.
- MPs, seats, parties, member ids and posts: mySociety parlparse members data (House of Commons records, Open Parliament Licence v3.0).
- Places: Wikidata (CC0); Hotham (2026) *Mentioned in the House*, doi:10.5281/zenodo.23761431. Majorities: Hotham (2026) *Who Won Here?*, doi:10.5281/zenodo.23761425. Seat boundaries: GB 2010 seats from an earlier study (ONS, Open Government Licence v3.0); Northern Ireland from martinjc/UK-GeoJSON (Open Government Licence v3.0). Common-word flags: wordfreq (data CC BY-SA 4.0).
- Base map: OpenFreeMap Positron (OpenStreetMap contributors, ODbL). MapLibre GL JS (BSD 3-Clause).
- Text, figures and derived data CC BY 4.0; code MIT.

## Citation

Hotham, T. (2026) Two faces of the constituency: how often British MPs name the places they represent on Facebook and in the House of Commons, 2017 to 2020. Zenodo. {{https://doi.org/10.5281/zenodo.24105795}}

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

{AI}
"""
lic = open("/home/claude/studies/byelection-attention/LICENSE", encoding="utf-8").read().split("Text, figures and the paper")[0]
lic += ("Text, figures and the paper: Creative Commons Attribution 4.0 International (CC BY 4.0), https://creativecommons.org/licenses/by/4.0/\n"
        "Derived data (data/, hansard_queries.json, hansard_counts.json): CC BY 4.0. Sources: Hansard and parlparse records (Open Parliament Licence v3.0), "
        "Wikidata (CC0), Northern Ireland boundaries (Open Government Licence v3.0). The Facebook files hold aggregate counts only.\n")
post = f"""**Title:** [OC] UK MPs named the towns and villages in their own seat {x['fb_per100']:.0f} times per 100 Facebook posts, but only {x['cm_per100']:.0f} times per 100 things they said in the Commons (2017 to 2020)

**Body:**

I matched {S['matched']} MPs' Facebook pages to their Commons record and, for each MP, fixed a list of places in their seat before looking at the Commons data. Then I counted how often each venue named those places, for the same MPs in the same months.

- Facebook: {x['fb_per100']:.0f} own-seat place mentions per 100 posts. Commons: {x['cm_per100']:.0f} per 100 spoken contributions.
- Same MP, same month: Facebook is {R['H1']['rr']:.1f}x as local. {R['mp']['fb_higher']} of {R['mp']['n']} MPs were more local on Facebook.
- Places in someone else's seat (a placebo): no gap ({R['placebo']['rr']:.2f}x).
- When an MP was on the front bench, their Commons rate fell {x['front_cm_drop_pc']:.0f}% and their Facebook rate didn't move.
- Marginal seats had a smaller gap, not a bigger one.

The posts start in February 2017 because the export hit CrowdTangle's 300,000-row cap.

Interactive map, tap any seat for its places in both venues: {PAGE}

**Source comment:**

Data: the author's CrowdTangle list of MPs' Facebook pages (counts only, no post text); Hansard via the UK Parliament API (Open Parliament Licence v3.0); mySociety parlparse; Wikidata (CC0). Method: Poisson regression with MP and month fixed effects, plan written before the Commons data. Tools: Python (pandas, pyfixest, matplotlib), MapLibre. Paper and code: {REPO}
"""
for t in (readme, lic, post):
    for bad in ("—", "–", "D" "SIT", "D" "CMS"):
        assert bad not in t, bad
open(f"{ROOT}/README.md", "w", encoding="utf-8").write(readme)
open(f"{ROOT}/LICENSE", "w", encoding="utf-8").write(lic)
os.makedirs(f"{ROOT}/reddit", exist_ok=True)
open(f"{ROOT}/reddit/post.md", "w", encoding="utf-8").write(post)
print("README", len(readme.split()), "words")
