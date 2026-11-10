"""Step 8: data/results.json = the model results plus derived numbers quoted in the text, with asserts."""
import pandas as pd, numpy as np
from common import *

R = jload(f"{DATA}/results_models.json")
H = R["H4"]
x = {}
x["h1"] = R["H1"]["rr"]; x["h1_lo"] = R["H1"]["lo"]; x["h1_hi"] = R["H1"]["hi"]
x["fb_per100"] = R["rate"]["facebook"]["y_main"]; x["cm_per100"] = R["rate"]["commons"]["y_main"]
x["fb_seat_per100"] = R["rate"]["facebook"]["y_seat"]; x["cm_seat_per100"] = R["rate"]["commons"]["y_seat"]
x["fb_other_per100"] = R["rate"]["facebook"]["y_pop"] + R["rate"]["facebook"]["y_random"]
x["cm_other_per100"] = R["rate"]["commons"]["y_pop"] + R["rate"]["commons"]["y_random"]
x["front_cm_drop_pc"] = (1 - H["front_commons"]["rr"]) * 100
x["front_cm_lo_pc"] = (1 - H["front_commons"]["hi"]) * 100; x["front_cm_hi_pc"] = (1 - H["front_commons"]["lo"]) * 100
x["front_fb_change_pc"] = (H["front_facebook"]["rr"] - 1) * 100
x["covid_fb_drop_pc"] = (1 - R["H5"]["facebook_covid"]["rr"]) * 100
x["covid_cm_drop_pc"] = (1 - R["H5"]["commons_covid"]["rr"]) * 100
x["marginal_pc"] = (1 - R["H3"]["marginal"]["rr"]) * 100
x["maj_pc"] = (R["H3"]["maj"]["rr"] - 1) * 100
x["gov_x"] = R["H4"]["gov"]["rr"]; x["front_x"] = R["H4"]["front"]["rr"]
x["mp_ratio_median"] = R["mp"]["ratio_median"]
x["largest_fb"] = R["H2"]["largest_share_fb"]; x["largest_cm"] = R["H2"]["largest_share_cm"]
x["small_ratio"] = R["H2"]["small_ratio"]
x["placebo_rr"] = R["placebo"]["rr"]
x["sitting_any_pc"] = R["fb_any_place"]["sitting_pc"]; x["campaign_any_pc"] = R["fb_any_place"]["campaign_pc"]
x["posts_total_csv"] = R["sample"]["csv_rows"]
R["x"] = x
# size bands (as in figure 4): mentions of one place per 1,000 items, Facebook vs Commons
pp = pd.read_csv(f"{DATA}/panel_places.csv")
pp = pp[pp.g.isin(["pop", "random"]) & pp["pop"].gt(0)].copy()
pp["w"] = np.where(pp.g == "random", pp.sample_weight, 1.0)
pp["bin"] = pd.cut(pp["pop"], [0, 1000, 5000, 20000, 100000, 1e7], labels=["under 1,000", "1,000 to 5,000", "5,000 to 20,000", "20,000 to 100,000", "100,000 and over"], right=False)
pp["r"] = pp["count"] / pp["items"] * 1000
sb = {}
for b_, g in pp.groupby("bin", observed=False):
    f = g[g.venue == "facebook"]; c = g[g.venue == "commons"]
    fr = float(np.average(f.r, weights=f.w)); cr = float(np.average(c.r, weights=c.w))
    sb[str(b_)] = dict(fb=fr, cm=cr, ratio=fr / cr)
R["size_bands"] = sb
x["size_ratio_min"] = min(v["ratio"] for v in sb.values()); x["size_ratio_max"] = max(v["ratio"] for v in sb.values())
R["x"] = x
site_g = pd.read_csv(f"{DATA}/mp_gap.csv")
site_g = site_g[(site_g.items_facebook > 0) & (site_g.items_commons > 0)].sort_values("items_facebook", ascending=False).drop_duplicates("seat")
R["map"] = dict(n=int(len(site_g)), pos=int((site_g.gap > 0).sum()))
# checks
assert R["H1"]["lo"] > 1 and R["robust_range"]["all_sig"] == R["robust_range"]["n"]
assert R["placebo"]["lo"] < 1 < R["placebo"]["hi"]
assert R["H2"]["diff_lo"] < 0 < R["H2"]["diff_hi"]
assert R["H4"]["front_commons"]["hi"] < 1 and R["H4"]["front_facebook"]["lo"] < 1 < R["H4"]["front_facebook"]["hi"]
assert R["H3"]["marginal"]["hi"] < 1
assert R["mp"]["fb_higher"] == 315 and R["sample"]["spells"] == 358
jsave(R, f"{DATA}/results.json", indent=1)
print({k: round(v, 2) if isinstance(v, float) else v for k, v in x.items()})
