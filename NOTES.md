# janus-places: working notes and analysis plan

"Two faces of the constituency: what MPs name on Facebook and in the Commons". Author Dr Tristan Hotham, Independent researcher.

## Status

- Phase 1 (this file, 2026): pages matched to MPs, seat place lists, Facebook place counts (aggregates only), Hansard query list. **No Commons data has been loaded or seen.** The plan below is pre-specified in a written plan, fixed before the Commons counts arrive (`data/hansard_counts.json`, to be supplied by the lead).
- Phase 2: analysis, paper and release, after the counts arrive. Anything not in this plan will be labelled exploratory.

## How this differs from the author's other papers

- **Janus-faced parties (draft)**: party and leader pages vs party speeches, agenda topics and style, four countries. This paper is its constituency counterpart: individual MPs, and one specific thing they can say in either venue, the names of the places they represent. No party-level results are reused.
- **Ahead of the Tide? (held, 2027)**: matched MPs' pages (a different, capped "Influencers" list plus Welsh and SNP lists) to 2017 and 2019 results, and found frontbench and very large pages named the constituency less often on Facebook. Its outcome is electoral performance and its local measure is Facebook only. This paper has no electoral outcome. Its core is the within-MP comparison of the two venues (Facebook vs Commons) on the same pre-specified place set, and which places (the main town, the villages) each venue names. Frontbench status enters only as a moderator of the venue gap, and the paper will cite the held paper for the Facebook-only frontbench pattern rather than re-estimate it. The matching approach is shared in spirit (page names cleaned of titles, every non-unique or unmatched page checked by hand, moves between seats kept and dated), but here pages are matched to Parliament membership records with member ids, not to election results.

## Data found in phase 1 (facts that change the brief)

- **The Facebook export covers 11 February 2017 to 28 October 2020, not 2010 to 2020.** The file is named 2010-01-01 to 2020-10-29 but holds 299,993 rows, which is CrowdTangle's 300,000-row export cap; the cap cut off everything before 11 February 2017. February 2017 is a partial month (from the 11th). So the study period is February 2017 to October 2020: it covers the 2017 and 2019 general elections, the Brexit votes of 2019 and the first COVID months, but not 2010 to 2016. The paper and page must say so.
- 372 pages in the list. 363 are matched to a sitting MP in the window (347 by cleaned name, 16 by hand). 9 are excluded: 7 Australian or New Zealand politicians, David Cameron (not an MP in the window) and a page about David Mundell not run by him ("MP Watch"). Every match is listed in `data/pages.csv` with its reason; hand decisions are in `code/page_overrides.json`. Every one of the 347 name matches was read by eye against the page's user name and seat (for example `willquincecolchester` to Colchester).
- Membership records with Parliament member ids (data.parliament "datadotparl" ids, the ids the Hansard API uses), seats, parties and exact dates come from mySociety's parlparse `members/people.json` (GitHub). Government, opposition and parliamentary posts with dates come from parlparse `members/ministers-2010.json`, which mirrors data.parliament. Licence: parlparse publishes no licence file; the underlying records are Parliament's (Open Parliament Licence v3.0). Cite both, and redistribute only the derived columns (ids, names, seats, parties, dates, post titles).
- A post counts for an MP only on days the person held a Commons seat, or in a dissolution gap between two memberships of the same seat (the person stood again and won). Those are labelled `period = campaign`. Posts from other days (before election, after leaving, losing candidates) are dropped and counted in `data/fb_outside.json`.
- Seats: 2010 boundaries (in force 2010 to 2024, so constant in the window). GB polygons from `twins-remain/data/seats.geojson` (632 seats); Northern Ireland's 18 from martinjc/UK-GeoJSON `json/electoral/ni/wpc.json` (cite; ONS/OSNI origin, Open Government Licence). The GB polygons are simplified, so villages within a few hundred metres of a boundary can be assigned to the neighbouring seat; this affects few places and both venues equally.

## Place lists (`data/seat_places.csv`)

- Sources: Wikidata UK settlements (`raw_new8/uk_settlements.tsv`, CC0; villages, hamlets, towns, cities, suburbs, areas of London, localities, neighbourhoods; forts and deserted sites dropped) plus the 1,661 places of hansard-places, each assigned to the seat containing its point; plus the places in the seat's own name (split on commas and "and", compass words removed only when the remainder is a known place: "West Bromwich East" gives West Bromwich; "Kingston upon Hull North" gives Kingston upon Hull and Hull; "Newcastle upon Tyne" also gives Newcastle).
- Seat-name parts that are counties, regions or generic words (Somerset, Kent, Hampshire, Yorkshire, Border, Test, Riverside, Pavilion, Wirral, Tyneside, Galloway, "Cities of London", and **Westminster**, which on Facebook almost always means Parliament) are kept with `area_term = True` and never queried. The same applies to seven settlement records named like a county or nation (a "Somerset" point in Wells, "Wales" in Rother Valley, "Scotland" in Leeds North West, "London" in the Cities of London, "Westminster" in Ellesmere Port, "Anglesey" in Burton, "Weald" in Witney), found by reading the most-named places after a first Facebook count; 106 rows are `area_term` in all.
- 36,312 seat-place rows (median 28 places per seat; range 3 to 675).
- Flags (`why_flag`): `common word` (hand flags from hansard-places where the place is in that list, otherwise lower-case English word frequency, wordfreq zipf >= 4.0: Bath, Sale, Battle, Bury, Reading, Street, Hope...); `namesake abroad` (hansard-places: Boston, Washington, Perth, Durham...); `bigger namesake elsewhere` (a same-named settlement in another seat that is larger, e.g. Newport (Isle of Wight) vs Newport West's villages; for seat-name places, one of at least 5,000 people and at least a tenth of the place's own size); `shared` (hansard-places hand flag: Newport, Richmond, Hull, Blackburn). `ambiguous` = any of these.
- **Phrase rule, identical in both venues**: an ambiguous name is searched as "in <Place>" (as in hansard-places), any other as "<Place>". Matching is case-insensitive whole-word phrase matching, like the Hansard search.
- Known residual noise, both venues: surnames that are places (Lancaster, Preston, Ashton), and "the Member for <seat>" in the Commons. The second only inflates Commons counts of seat-name places when an MP names another MP's seat that shares a place name; it is measured in a robustness check that drops seat-name places.

## Facebook counts (`data/fb_mp_months.csv`, `data/fb_place_counts.csv`)

- Per MP-month-seat-period: posts, posts with a message, posts naming any own-seat place (in the message; in any text field).
- Per MP-month-seat-period-phrase: posts naming the phrase in the message (`n_message`, main) and in any field (`n_any_field`: message, link title, link description or image text; sensitivity only, since link text is usually written by someone else).
- Only counts are written. No post text, URL or link is stored anywhere in the study. The CSV is streamed in 50,000-row chunks from where it sits.

## Hansard queries (`hansard_queries.json`)

Per matched MP and per seat they held in the window, the place set is fixed now, before any Commons data:

1. **seat**: every queryable place in the seat's name.
2. **pop**: the 8 most populous other places in the seat (Wikidata/ONS population).
3. **random**: a fixed random sample of 5 further places from the rest (seed 2026), with `sample_weight` = remaining places / 5, so the seat's whole place list can be estimated.
4. **fb_top**: up to 3 of the MP's most-named Facebook places not already included. These are chosen on the Facebook outcome, so they are **descriptive only** and excluded from every test.
5. **placebo**: the 2 most populous unambiguous, unshared places (not seat-name places) of a different, randomly chosen seat in the same nation (seed 2026). Expect no Facebook excess for these.
6. **total**: one query per MP-seat with no phrase: all the MP's spoken Commons contributions in the period (the denominator).

Each query is `{query_id, member_name, member_id, person_id, seat, place, phrase, group, sample_weight, start, end}`; `start`/`end` are the membership dates clipped to 2017-02-11 and 2020-10-28. Requested return: monthly counts of spoken House of Commons contributions by that member containing the exact phrase, as `{query_id: {"YYYY-MM": n}}` (absent months = 0), the same timeline-stats call used for `hansard_monthly.json` with the member filter added. Contributions are counted, not word occurrences; Facebook posts are counted the same way (a post naming a place twice counts once).

## Phase 1 numbers

- 363 MPs with a matched page (one page each); 359 have posts on days they held their seat.
- 276,246 posts fall in membership days (246,982 sitting, 29,264 campaign); 12,981 posts on other days dropped. 14,230 MP-month-seat-period rows.
- Median MP: 36% of posts with a message name at least one own-seat place (same order as the held paper's 35% for the constituency name, on a different list and measure).
- 6,282 queries for 363 MPs (366 MP-seat spells; three MPs held two seats): total 366, seat 430, pop 2,297, random 1,757, fb_top 700, placebo 732. Every query has a member id.
- Rerun order: 00_pages_raw.py, 01_members.py, 01b_posts.py (both need parlparse files in scratch), 02_match_pages.py, 03_places.py (needs `pip install wordfreq` and the NI GeoJSON), 04_fb_counts.py (about 25 minutes on a busy machine), 05_queries.py.

## Pre-specified analysis plan

Unit: MP-venue-month (main), MP-place-venue (which places). Venue = Facebook post or Commons spoken contribution. Facebook items = posts with a message. Commons items = spoken contributions (query 6). Months in a dissolution are Facebook-only and enter only the election analysis (H5).

Outcome: local naming rate = sum over the MP's fixed place set (groups seat + pop + random, random weighted) of items naming each place, per 100 items. The same place set and phrases in both venues, so the comparison is within MP and within place.

- **H1 (local face).** MPs name their own seat's places at a higher rate on Facebook than in the Commons. Model: Poisson pseudo-maximum likelihood, count of place-naming items ~ Facebook + MP fixed effects + month fixed effects, offset log(items), SEs clustered by MP. Report the rate ratio with 95% CI and N. Against H1: a rate ratio at or below 1, or a CI including 1.
- **H2 (which places).** Facebook spreads naming further down the settlement hierarchy. (a) Place-level model: count ~ log(population) x Facebook + MP x venue fixed effects (offset items), clustered by MP: H2 predicts a smaller population elasticity on Facebook. (b) Share of each MP's local naming that goes to the seat's largest place, by venue. (c) Share of the seat's places (weighted) named at least once, by venue. Against H2: equal or steeper elasticity on Facebook.
- **H3 (marginality).** The Facebook minus Commons gap is larger in marginal seats (2017 majority, from elections-since-1832 candidates 2017; 2019 majority for the later months). Interaction Facebook x majority (percentage points, continuous) plus a < 10 point dummy.
- **H4 (role and side).** The gap is smaller for frontbenchers (government or opposition post held that month; from data.parliament posts) because their Commons speech is portfolio business but their Facebook is also national; and differs between government and opposition MPs (Conservatives, plus DUP during confidence and supply, coded government). Party families as descriptive splits only; no party ranking in public copy.
- **H5 (time).** Descriptive and exploratory: monthly local rates in each venue around the 2017 and 2019 campaigns, the 2019 Brexit votes (January to October 2019) and COVID (from March 2020). Expectation: Facebook local naming falls in national-news months and rises in COVID months; the Commons local rate is lower in Brexit months.

Robustness: (1) any-field Facebook counts; (2) dropping ambiguous phrases; (3) dropping seat-name places; (4) population places only (no weights); (5) MP-quarter aggregation; (6) excluding MPs with fewer than 20 contributions or 20 posts in a month window; (7) leave one nation or region out; (8) placebo places from another seat (expect rate ratio about 1 or lower); (9) drop the 10 largest pages; (10) negative binomial instead of Poisson.

Caveats to state: the pages are those the author listed in 2017, not a census; a third of MPs have no page; posts deleted before 2020 are missing; Facebook items and Commons contributions differ in length and purpose (the rate is per item, not per word); the counts are associations, not causal effects.

## Log

- 2026: plan written before any Commons data. Facebook window found to be capped at February 2017. Northern Ireland seat boundaries fetched from GitHub (martinjc/UK-GeoJSON). parlparse people.json and ministers-2010.json fetched to scratch, reduced to `data/commons_memberships.csv` and `data/frontbench_posts.csv`, originals deleted.

## Phase 2 log (after the Commons counts arrived)

- `hansard_counts.json` received for all 6,282 queries (UK Parliament Hansard API timeline statistics, Commons, Spoken, member filter, exact phrase; Open Parliament Licence v3.0, retrieved 2026).
- Implementation note: 04 searched each MP's posts only for their own seat's places, so the planned placebo places had no Facebook counts. `code/04b_fb_placebo.py` counts them with the same rule (an implementation of the planned test, not a new test).
- Added after the plan and labelled as such: dropping Deputy Speakers (their contributions are mostly from the chair); the frontbench and government-side terms estimated together; separate models for each venue for frontbench and period effects (used to explain the planned interactions).
- Results against the plan: H1 supported (rate ratio 4.36, 95% CI 3.76 to 5.06; placebo 1.04, 0.65 to 1.66; 15 checks from 3.1 to 6.1, all above 1). H2 not supported (population elasticity 1.01 in the Commons and 0.95 on Facebook, difference -0.06, CI -0.21 to 0.09). H3 not supported, the sign is reversed (the gap is 0.67 times as large in marginal seats). H4 not supported, the sign is reversed (the gap is 2.73 times as large in frontbench months: the Commons rate falls 77% and the Facebook rate does not move). H5 exploratory: the Facebook rate fell 27% in the COVID months; no clear change in the Brexit months.
- Frontbench role titles are reduced to categories in `data/frontbench_posts.csv` (minister, shadow, whip, party leader, chair, other).
- Outputs: paper (19 pages, about 7,200 words before the references), page, blog post, collage, GIF (/home/claude/gifs/out/janus-places.gif, copied to reddit/), Zenodo files. QA screenshots in qa/ (desktop 1280 and phone 390; no console errors).
- Independent review (2026): results.json reproduced exactly from 06 to 08. Added size-band ratios to results.json (used in the blog and page). Softened causal and unchecked wording (frontbench "turns to the job", COVID "national health messages", Grimmer and Stier descriptions, by-election citation), labelled the per-venue models as added after the plan, referenced the appendix table, fixed the collage label crossing the front-bench chart axis. References checked online.
