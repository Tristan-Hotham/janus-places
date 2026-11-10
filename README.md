# Two faces of the constituency

What MPs name on Facebook and in the House of Commons, February 2017 to October 2020. For the same MPs, months and pre-specified places, how often their Facebook posts and their spoken Commons contributions name the towns and villages in their own seat.

Interactive page: https://maps.tristanhotham.com/janus-places/
Paper: https://doi.org/10.5281/zenodo.24105795
Blog post: https://blog.tristanhotham.com/2026/10/31/janus-places/
Code and data: https://github.com/Tristan-Hotham/janus-places

**The window.** The CrowdTangle export reached its 300,000-row cap (299,993 rows), so the Facebook posts start on 11 February 2017. Everything covers February 2017 to October 2020, not 2010 to 2020.

## Headline results

- Sample: 358 MP-seat spells (355 MPs, 350 seats) with items in both venues; 224,340 Facebook posts with a message and 153,184 spoken Commons contributions; 6,282 Hansard queries fixed in advance.
- MPs named their own seat's places 42.3 times per 100 Facebook posts and 9.0 times per 100 Commons contributions. Within MP and month the Facebook to Commons rate ratio is 4.36 (95% CI 3.76 to 5.06). 315 of 331 MPs with at least 20 items in each venue had the higher rate on Facebook.
- Placebo, places in another MP's seat: rate ratio 1.04 (95% CI 0.65 to 1.66).
- Which places: the population elasticity of naming is 1.01 in the Commons and 0.95 on Facebook (difference -0.06, CI -0.21 to 0.09): Facebook is louder, not differently shaped. Seat-name places: ratio 3.5; other places 5.9.
- Office: in frontbench months the Commons rate falls by 77% (CI 69% to 83%) and the Facebook rate does not change (1.00 (95% CI 0.92 to 1.09)).
- Marginal seats (majority under 10 points): a smaller gap, 0.67 (95% CI 0.49 to 0.91) times as large. Government side: 2.26 (95% CI 1.71 to 2.99).
- COVID months: Facebook local rate down 27% (exploratory). Brexit months: no clear change in either venue.
- 15 robustness checks: ratios from 3.1 to 6.1, all with intervals above 1.

## Files

| File | What it is |
|---|---|
| `index.html`, `js/page.js` | Interactive page: MapLibre on OpenFreeMap Positron; 2010 seats coloured by the Facebook minus Commons gap (or either rate), search for seats, MPs and places, layers, full screen, popups with each queried place's counts in both venues. |
| `header.png` | Social card, 1200 x 630. |
| `hansard_queries.json` | The 6,282 queries fixed before any Commons data: member, Parliament member id, seat, place, exact phrase, group, sample weight, dates. |
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

Hotham, T. (2026) Two faces of the constituency: how often British MPs name the places they represent on Facebook and in the House of Commons, 2017 to 2020. Zenodo. https://doi.org/10.5281/zenodo.24105795

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
