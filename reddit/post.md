**Title:** [OC] UK MPs named the towns and villages in their own seat 42 times per 100 Facebook posts, but only 9 times per 100 things they said in the Commons (2017 to 2020)

**Body:**

I matched 363 MPs' Facebook pages to their Commons record and, for each MP, fixed a list of places in their seat before looking at the Commons data. Then I counted how often each venue named those places, for the same MPs in the same months.

- Facebook: 42 own-seat place mentions per 100 posts. Commons: 9 per 100 spoken contributions.
- Same MP, same month: Facebook is 4.4x as local. 315 of 331 MPs were more local on Facebook.
- Places in someone else's seat (a placebo): no gap (1.04x).
- When an MP was on the front bench, their Commons rate fell 77% and their Facebook rate didn't move.
- Marginal seats had a smaller gap, not a bigger one.

The posts start in February 2017 because the export hit CrowdTangle's 300,000-row cap.

Interactive map, tap any seat for its places in both venues: https://maps.tristanhotham.com/janus-places/

**Source comment:**

Data: the author's CrowdTangle list of MPs' Facebook pages (counts only, no post text); Hansard via the UK Parliament API (Open Parliament Licence v3.0); mySociety parlparse; Wikidata (CC0). Method: Poisson regression with MP and month fixed effects, plan written before the Commons data. Tools: Python (pandas, pyfixest, matplotlib), MapLibre. Paper and code: https://github.com/Tristan-Hotham/janus-places
