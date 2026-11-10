"""Step 7: the pre-specified models (NOTES.md) and every number used anywhere -> data/results.json, data/models.csv,
data/mp_gap.csv (one row per spell), data/monthly.csv (venue rates by month)."""
import warnings, pandas as pd, numpy as np, pyfixest as pf
from scipy import stats
import statsmodels.formula.api as smf
from common import *
warnings.filterwarnings("ignore")

pm = pd.read_csv(f"{DATA}/panel_months.csv", dtype={"person_id": str})
pp = pd.read_csv(f"{DATA}/panel_places.csv", dtype={"person_id": str})
cov = pd.read_csv(f"{DATA}/mp_covariates.csv", dtype={"person_id": str, "fb_id": str})
fbp = pd.read_csv(f"{DATA}/frontbench_posts.csv", dtype={"person_id": str})
pages = pd.read_csv(f"{DATA}/pages.csv", dtype=str)
fbm_all = pd.read_csv(f"{DATA}/fb_mp_months.csv", dtype={"person_id": str})
outside = jload(f"{DATA}/fb_outside.json")
R = {}

# ------------------------------------------------------------------ sample
both = pm.groupby("spell").venue.nunique()
S = pm[pm.spell.isin(both[both == 2].index)].copy()
S["li"] = np.log(S["items"])
S["quarter"] = S.month.str[:4] + "Q" + ((S.month.str[5:7].astype(int) - 1) // 3 + 1).astype(str)
cv = cov.set_index("spell")
for c in ("party", "nation", "followers_last", "maj2015", "maj2017", "maj2019", "member_name", "seat"):
    S[c] = S.spell.map(cv[c]) if c != "seat" else S[c]
S["maj"] = np.where(S.month < "2017-06", S.maj2015, np.where(S.month < "2019-12", S.maj2017, S.maj2019))
S["maj10"] = S.maj / 10
S["marginal"] = (S.maj < 10).astype(int)
mstart = pd.to_datetime(S.month + "-01"); mend = mstart + pd.offsets.MonthEnd(0)
def active(cats):
    f = fbp[fbp.category.isin(cats)]
    out = np.zeros(len(S), dtype=int)
    d = f.groupby("person_id")
    for i, (pid, a, b) in enumerate(zip(S.person_id, mstart, mend)):
        if pid in d.groups:
            g = d.get_group(pid)
            out[i] = int(((pd.to_datetime(g.start) <= b) & (pd.to_datetime(g.end.str.replace("9999", "2099")) >= a)).any())
    return out
S["front"] = active(["minister", "shadow", "party_leader"])
S["front_whip"] = active(["minister", "shadow", "party_leader", "whip"])
S["chair"] = active(["chair"])
gov_party = S.party.isin(["Conservative"]) | (S.party.eq("DUP") & (S.month >= CS[0][:7]) & (S.month <= CS[1][:7]))
S["gov"] = gov_party.astype(int)
S["brexit"] = ((S.month >= BREXIT[0]) & (S.month <= BREXIT[1])).astype(int)
S["covid"] = (S.month >= COVID).astype(int)
S["pre_ge"] = S.month.isin(["2017-03", "2017-04", "2019-09", "2019-10"]).astype(int)

n_sp = S.spell.nunique()
R["sample"] = dict(pages=len(pages), matched=int(pages.person_id.notna().sum()), excluded=int(pages.person_id.isna().sum()),
                   excluded_foreign=7, spells_all=int(pm.spell.nunique()), spells=n_sp, mps=int(S.person_id.nunique()),
                   rows=len(S), rows_fb=int((S.venue == "facebook").sum()), rows_commons=int((S.venue == "commons").sum()),
                   posts=int(S[S.venue == "facebook"]["items"].sum()), contributions=int(S[S.venue == "commons"]["items"].sum()),
                   posts_all_sitting=int(fbm_all[fbm_all.period == "sitting"].posts.sum()),
                   posts_campaign=int(fbm_all[fbm_all.period == "campaign"].posts.sum()),
                   posts_outside=int(outside["posts_outside_membership"]), csv_rows=299993,
                   first="February 2017", last="October 2020", by_nation=S.drop_duplicates("spell").nation.value_counts().to_dict(),
                   queries=len(jload(f"{ROOT}/hansard_queries.json")), months=int(S.month.nunique()),
                   seats=int(S.seat.nunique()), places_rows=int(len(pd.read_csv(f"{DATA}/seat_places.csv"))))
R["sample"]["n_parties"] = int(S.drop_duplicates("spell").party.nunique())

# ------------------------------------------------------------------ helpers
def pois(fml, d, offset="li", cluster="spell", weights=None):
    return pf.fepois(fml, d, offset=offset, vcov={"CRV1": cluster}, weights=weights)
def coef(m, name):
    t = m.tidy().loc[name]
    return dict(b=float(t.Estimate), se=float(t["Std. Error"]), p=float(t["Pr(>|t|)"]), rr=float(np.exp(t.Estimate)),
                lo=float(np.exp(t["2.5%"])), hi=float(np.exp(t["97.5%"])), n=int(m._N))
MODELS = []
def keep(label, group, m, name, d, extra=""):
    c = coef(m, name); c.update(spells=int(d.spell.nunique()), label=label, group=group, term=name, note=extra)
    MODELS.append(c); return c

# ------------------------------------------------------------------ descriptives
tot = S.groupby("venue")[["items", "y_main", "y_seat", "y_pop", "y_random", "y_fb_top", "y_placebo"]].sum()
rate = (tot.div(tot["items"], axis=0) * 100)
R["rate"] = {v: {k: float(rate.loc[v, k]) for k in rate.columns if k != "items"} for v in rate.index}
R["rate"]["ratio_main"] = R["rate"]["facebook"]["y_main"] / R["rate"]["commons"]["y_main"]
mp = S.groupby(["spell", "venue"])[["items", "y_main"]].sum().unstack()
mp.columns = [f"{a}_{b}" for a, b in mp.columns]
mp["fb_rate"] = mp.y_main_facebook / mp.items_facebook * 100
mp["cm_rate"] = mp.y_main_commons / mp.items_commons * 100
mp["gap"] = mp.fb_rate - mp.cm_rate
big = mp[(mp.items_facebook >= 20) & (mp.items_commons >= 20)]
R["mp"] = dict(n=len(big), fb_higher=int((big.gap > 0).sum()), fb_higher_pc=float((big.gap > 0).mean() * 100),
               fb_median=float(big.fb_rate.median()), cm_median=float(big.cm_rate.median()), gap_median=float(big.gap.median()),
               ratio_median=float((big.fb_rate / big.cm_rate.replace(0, np.nan)).median()),
               cm_zero=int((big.y_main_commons == 0).sum()), fb_zero=int((big.y_main_facebook == 0).sum()),
               items_fb_median=float(big.items_facebook.median()), items_cm_median=float(big.items_commons.median()))
R["mp"]["wilcoxon_p"] = float(stats.wilcoxon(big.fb_rate, big.cm_rate).pvalue)
R["mp"]["spearman_rho"] = float(stats.spearmanr(big.fb_rate, big.cm_rate).statistic)
R["mp"]["spearman_p"] = float(stats.spearmanr(big.fb_rate, big.cm_rate).pvalue)

# ------------------------------------------------------------------ H1
m1 = pois("y_main ~ fb | spell + month", S)
R["H1"] = keep("Main: own-seat places, Facebook vs Commons", "main", m1, "fb", S)
d = S.copy(); d["y"] = d.y_main_unw
R["H1_unweighted"] = keep("Unweighted counts (random places not reweighted)", "robust", pois("y ~ fb | spell + month", d), "fb", d)

# ------------------------------------------------------------------ robustness of H1
rb = {}
rb["anyfield"] = keep("Facebook: any text field", "robust", pois("y_main_anyfield ~ fb | spell + month", S), "fb", S)
rb["noamb"] = keep("Drop ambiguous phrases", "robust", pois("y_noamb ~ fb | spell + month", S), "fb", S)
rb["noseat"] = keep("Drop seat-name places", "robust", pois("y_noseat ~ fb | spell + month", S), "fb", S)
rb["seatonly"] = keep("Seat-name places only", "robust", pois("y_seat ~ fb | spell + month", S), "fb", S)
rb["poponly"] = keep("Most populous places only", "robust", pois("y_pop ~ fb | spell + month", S), "fb", S)
rb["random"] = keep("Random sample of places only", "robust", pois("y_random ~ fb | spell + month", S), "fb", S)
q = S.groupby(["spell", "venue", "quarter"], as_index=False)[["items", "y_main"]].sum(); q["fb"] = (q.venue == "facebook").astype(int); q["li"] = np.log(q["items"])
rb["quarter"] = keep("MP-quarter aggregation", "robust", pois("y_main ~ fb | spell + quarter", q), "fb", q)
ok = big.index
d = S[S.spell.isin(ok)]
rb["min20"] = keep("MPs with 20+ posts and 20+ contributions", "robust", pois("y_main ~ fb | spell + month", d), "fb", d)
for n in sorted(S.nation.unique()):
    d = S[S.nation != n]
    rb["no_" + n] = keep(f"Leave out {n}", "robust", pois("y_main ~ fb | spell + month", d), "fb", d)
top10 = cov.drop_duplicates("person_id").nlargest(10, "followers_last").person_id
d = S[~S.person_id.isin(top10)]
rb["notop10"] = keep("Drop the 10 largest pages", "robust", pois("y_main ~ fb | spell + month", d), "fb", d)
d = S[~S.spell.isin(S[S.chair == 1].spell)]
rb["nochair"] = keep("Drop Deputy Speakers (added after the plan)", "robust", pois("y_main ~ fb | spell + month", d), "fb", d, "exploratory")
# negative binomial (integer counts, dummies for spell and month)
d = S.copy(); d["y"] = d.y_main_unw.round().astype(int)
try:
    nb = smf.negativebinomial("y ~ fb + C(spell) + C(month)", d, offset=d.li).fit(disp=0, maxiter=200, method="nm") if False else None
    import statsmodels.api as sm
    X = pd.get_dummies(d[["spell", "month"]], drop_first=True, dtype=float); X.insert(0, "fb", d.fb.astype(float)); X = sm.add_constant(X)
    g = sm.GLM(d.y, X, family=sm.families.NegativeBinomial(alpha=1.0), offset=d.li).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(d.spell)[0]})
    b, se = g.params["fb"], g.bse["fb"]
    c = dict(b=float(b), se=float(se), p=float(g.pvalues["fb"]), rr=float(np.exp(b)), lo=float(np.exp(b - 1.96 * se)), hi=float(np.exp(b + 1.96 * se)),
             n=int(len(d)), spells=int(d.spell.nunique()), label="Negative binomial (alpha = 1)", group="robust", term="fb", note="")
    MODELS.append(c); rb["negbin"] = c
except Exception as e:
    print("negbin failed", e)
R["robust"] = rb
R["robust_range"] = dict(n=len(rb), min=min(v["rr"] for v in rb.values()), max=max(v["rr"] for v in rb.values()),
                         all_sig=int(sum(v["lo"] > 1 for v in rb.values())))
# placebo: places in another seat
R["placebo"] = keep("Placebo: places in another seat", "placebo", pois("y_placebo ~ fb | spell + month", S), "fb", S)
R["placebo"]["fb_n"] = float(S[S.venue == "facebook"].y_placebo.sum()); R["placebo"]["cm_n"] = float(S[S.venue == "commons"].y_placebo.sum())
R["placebo"]["fb_rate"] = R["rate"]["facebook"]["y_placebo"]; R["placebo"]["cm_rate"] = R["rate"]["commons"]["y_placebo"]
R["fbtop"] = dict(fb_rate=R["rate"]["facebook"]["y_fb_top"], cm_rate=R["rate"]["commons"]["y_fb_top"])

# ------------------------------------------------------------------ H2: which places
P = pp[pp.spell.isin(S.spell.unique())].copy()
P["fb"] = (P.venue == "facebook").astype(int)
P["li"] = np.log(P["items"])
P["w"] = np.where(P.g == "random", P.sample_weight, 1.0)
P["sv"] = P.spell + "|" + P.venue
pl = P[P.g.isin(["pop", "random"]) & P["pop"].gt(0)].copy()
pl["lpop"] = np.log(pl["pop"])
m2 = pf.fepois("count ~ lpop + lpop:fb | sv", pl, offset="li", vcov={"CRV1": "spell"}, weights="w")
t = m2.tidy()
R["H2"] = dict(el_commons=float(t.loc["lpop", "Estimate"]), el_commons_lo=float(t.loc["lpop", "2.5%"]), el_commons_hi=float(t.loc["lpop", "97.5%"]),
               diff=float(t.loc["lpop:fb", "Estimate"]), diff_lo=float(t.loc["lpop:fb", "2.5%"]), diff_hi=float(t.loc["lpop:fb", "97.5%"]),
               diff_p=float(t.loc["lpop:fb", "Pr(>|t|)"]), n=int(m2._N), places=int(pl.query_id.nunique()), spells=int(pl.spell.nunique()))
R["H2"]["el_fb"] = R["H2"]["el_commons"] + R["H2"]["diff"]
MODELS.append(dict(label="H2: population elasticity, Commons", group="H2", term="lpop", b=R["H2"]["el_commons"], lo=R["H2"]["el_commons_lo"], hi=R["H2"]["el_commons_hi"], n=R["H2"]["n"], spells=R["H2"]["spells"], p=float(t.loc["lpop", "Pr(>|t|)"]), rr=None, se=float(t.loc["lpop", "Std. Error"]), note="log scale"))
MODELS.append(dict(label="H2: Facebook minus Commons elasticity", group="H2", term="lpop:fb", b=R["H2"]["diff"], lo=R["H2"]["diff_lo"], hi=R["H2"]["diff_hi"], n=R["H2"]["n"], spells=R["H2"]["spells"], p=R["H2"]["diff_p"], rr=None, se=float(t.loc["lpop:fb", "Std. Error"]), note="log scale"))
# (b) share of local naming going to the seat's largest place
main = P[P.g.isin(MAIN_GROUPS)].copy(); main["wc"] = main.w * main["count"]
largest = main[main["rank"] == 1]
tot_loc = main.groupby(["spell", "venue"]).wc.sum()
lg = largest.groupby(["spell", "venue"]).wc.sum().reindex(tot_loc.index).fillna(0)
sh = (lg / tot_loc).unstack()
nloc = tot_loc.unstack()
okb = nloc[(nloc.commons >= 5) & (nloc.facebook >= 5)].index
shb = sh.loc[sh.index.intersection(okb)]
R["H2"]["largest_share_fb"] = float(shb.facebook.mean() * 100); R["H2"]["largest_share_cm"] = float(shb.commons.mean() * 100)
R["H2"]["largest_n"] = int(len(shb)); R["H2"]["largest_p"] = float(stats.wilcoxon(shb.facebook, shb.commons).pvalue)
# (c) coverage of the sampled (non seat-name) places: weighted share named at least once
cv2 = P[P.g.isin(["pop", "random"])].copy(); cv2["named"] = (cv2["count"] > 0).astype(float)
cov_ = cv2.groupby(["spell", "venue"]).apply(lambda g: np.average(g.named, weights=g.w), include_groups=False).unstack()
R["H2"]["coverage_fb"] = float(cov_.facebook.mean() * 100); R["H2"]["coverage_cm"] = float(cov_.commons.mean() * 100)
R["H2"]["coverage_n"] = int(cov_.dropna().shape[0])
# small places: under 5,000 people
sm_ = cv2[cv2["pop"] < 5000]
R["H2"]["small_fb_rate"] = float(sm_[sm_.venue == "facebook"].pipe(lambda d: (d.w * d["count"]).sum()) / S[S.venue == "facebook"]["items"].sum() * 1000)
R["H2"]["small_cm_rate"] = float(sm_[sm_.venue == "commons"].pipe(lambda d: (d.w * d["count"]).sum()) / S[S.venue == "commons"]["items"].sum() * 1000)
R["H2"]["small_ratio"] = R["H2"]["small_fb_rate"] / R["H2"]["small_cm_rate"] if R["H2"]["small_cm_rate"] else None
# group rate ratios (seat-name places vs others) from the month models above
R["H2"]["rr_seat"] = rb["seatonly"]["rr"]; R["H2"]["rr_noseat"] = rb["noseat"]["rr"]; R["H2"]["rr_random"] = rb["random"]["rr"]

# ------------------------------------------------------------------ H3, H4, H5
def inter(label, fml, term, d, grp):
    m = pois(fml, d); return keep(label, grp, m, term, d)
R["H3"] = dict(maj=inter("Facebook x majority (per 10 points)", "y_main ~ fb + fb:maj10 + maj10 | spell + month", "fb:maj10", S, "H3"),
               marginal=inter("Facebook x marginal (majority under 10 points)", "y_main ~ fb + fb:marginal + marginal | spell + month", "fb:marginal", S, "H3"))
R["H3"]["n_marginal_spells"] = int(S[S.marginal == 1].spell.nunique())
d = S
R["H4"] = dict(front=inter("Facebook x frontbench", "y_main ~ fb + fb:front + front | spell + month", "fb:front", d, "H4"),
               front_whip=inter("Facebook x frontbench incl. whips", "y_main ~ fb + fb:front_whip + front_whip | spell + month", "fb:front_whip", d, "H4"),
               gov=inter("Facebook x government side", "y_main ~ fb + fb:gov + gov | spell + month", "fb:gov", d, "H4"),
               front_main=coef(pois("y_main ~ fb + fb:front + front | spell + month", d), "front"))
mj = pois("y_main ~ fb + fb:front + front + fb:gov + gov | spell + month", d)
R["H4"]["joint_front"] = keep("Joint: Facebook x frontbench (with government side)", "H4x", mj, "fb:front", d, "exploratory")
R["H4"]["joint_gov"] = keep("Joint: Facebook x government side (with frontbench)", "H4x", mj, "fb:gov", d, "exploratory")
for v in ("facebook", "commons"):
    dv = S[S.venue == v]
    mv = pf.fepois("y_main ~ front | spell + month", dv, offset="li", vcov={"CRV1": "spell"})
    R["H4"][f"front_{v}"] = coef(mv, "front")
R["H4"]["n_front_spells"] = int(S[S.front == 1].spell.nunique()); R["H4"]["n_gov_spells"] = int(S[S.gov == 1].spell.nunique())
m5 = pois("y_main ~ fb + fb:brexit + fb:covid + fb:pre_ge + brexit:fb | spell + month", S) if False else pois("y_main ~ fb + fb:brexit + fb:covid + fb:pre_ge | spell + month", S)
R["H5"] = {k: keep(f"Facebook x {k}", "H5", m5, f"fb:{k}", S, "exploratory") for k in ("brexit", "covid", "pre_ge")}
# venue-specific changes (each venue against its own other months)
for v in ("facebook", "commons"):
    d = S[S.venue == v].copy()
    d["t"] = np.arange(len(d))
    m = pf.fepois("y_main ~ brexit + covid + pre_ge | spell", d, offset="li", vcov={"CRV1": "spell"})
    for k in ("brexit", "covid", "pre_ge"):
        R["H5"][f"{v}_{k}"] = coef(m, k)
# campaign months (Facebook only): local rate during dissolution vs sitting months
camp = fbm_all[fbm_all.period == "campaign"]
R["H5"]["campaign_local_pc"] = float(camp.posts_naming_any_place_message.sum() / camp.posts_with_message.sum() * 100)
sit = fbm_all[fbm_all.period == "sitting"]
R["H5"]["sitting_local_pc"] = float(sit.posts_naming_any_place_message.sum() / sit.posts_with_message.sum() * 100)
R["fb_any_place"] = dict(sitting_pc=R["H5"]["sitting_local_pc"], campaign_pc=R["H5"]["campaign_local_pc"])

# ------------------------------------------------------------------ monthly series and MP table
mon = S.groupby(["month", "venue"])[["items", "y_main"]].sum().unstack()
mon.columns = [f"{a}_{b}" for a, b in mon.columns]
mon["fb_rate"] = mon.y_main_facebook / mon.items_facebook * 100
mon["cm_rate"] = mon.y_main_commons / mon.items_commons * 100
mon.reset_index().to_csv(f"{DATA}/monthly.csv", index=False)
R["monthly"] = dict(fb_max_month=mon.fb_rate.idxmax(), fb_min_month=mon.fb_rate.idxmin(), fb_max=float(mon.fb_rate.max()), fb_min=float(mon.fb_rate.min()),
                    cm_max_month=mon.cm_rate.idxmax(), cm_min_month=mon.cm_rate.idxmin(), cm_max=float(mon.cm_rate.max()), cm_min=float(mon.cm_rate.min()),
                    months_fb_higher=int((mon.fb_rate > mon.cm_rate).sum()), months_both=int(mon[["fb_rate", "cm_rate"]].dropna().shape[0]))
mpt = mp.join(cov.set_index("spell")[["person_id", "member_name", "seat", "party", "nation", "followers_last", "maj2017"]])
mpt.reset_index().to_csv(f"{DATA}/mp_gap.csv", index=False)
# party families: descriptive only
fam = {"Conservative": "Conservative", "Labour": "Labour", "Labour/Co-operative": "Labour", "Scottish National Party": "SNP"}
mpt["fam"] = mpt.party.map(fam).fillna("Other")
b2 = mpt[(mpt.items_facebook >= 20) & (mpt.items_commons >= 20)]
R["by_family"] = {f: dict(n=int(len(g)), fb=float(g.fb_rate.median()), cm=float(g.cm_rate.median())) for f, g in b2.groupby("fam")}
R["by_nation"] = {f: dict(n=int(len(g)), fb=float(g.fb_rate.median()), cm=float(g.cm_rate.median())) for f, g in b2.groupby("nation")}

pd.DataFrame(MODELS).to_csv(f"{DATA}/models.csv", index=False)
S.drop(columns=["li"]).to_csv(f"{SCR}/S.csv", index=False)
jsave(R, f"{DATA}/results_models.json", indent=1)
print(json.dumps(nonan({k: R[k] for k in ("H1", "rate", "mp", "placebo", "robust_range")}), indent=0)[:3000])
print(json.dumps(nonan(R["H2"]), indent=0)); print({k: (round(v["rr"], 3), round(v["lo"], 3), round(v["hi"], 3)) for k, v in R["H3"].items() if isinstance(v, dict)})
print({k: (round(v["rr"], 3), round(v["lo"], 3), round(v["hi"], 3), v.get("p")) for k, v in R["H4"].items() if isinstance(v, dict)})
print({k: (round(v["rr"], 3), round(v["lo"], 3), round(v["hi"], 3)) for k, v in R["H5"].items() if isinstance(v, dict)})
print({k: (round(v["rr"], 2), round(v["lo"], 2), round(v["hi"], 2)) for k, v in rb.items()})
