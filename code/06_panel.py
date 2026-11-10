"""Step 6: join the Facebook counts and the Hansard counts into
  data/panel_months.csv  one row per MP-seat spell x month x venue (items and weighted place-naming counts)
  data/panel_places.csv  one row per MP-seat spell x queried place x venue (totals over the sitting months)
  data/mp_covariates.csv one row per spell: party, nation, page size, majority, frontbench months
Facebook items are posts with a message on days the MP sat; Commons items are the member's spoken contributions."""
import pandas as pd, numpy as np
from common import *

Q = pd.DataFrame(jload(f"{ROOT}/hansard_queries.json"))
H = jload(f"{ROOT}/hansard_counts.json")
assert set(Q.query_id) == set(H), "every query must have a count entry"
Q["g"] = Q.group.str.split(":").str[0]
Q["spell"] = Q.person_id + "|" + Q.seat
P = pd.read_csv(f"{DATA}/seat_places.csv")
P["phrase"] = np.where(P.ambiguous, "in " + P.name, P.name)
attr = P.drop_duplicates(["seat", "phrase"]).set_index(["seat", "phrase"])
fbm = pd.read_csv(f"{DATA}/fb_mp_months.csv", dtype={"person_id": str})
fbm = fbm[fbm.period == "sitting"].copy()
fbc = pd.read_csv(f"{DATA}/fb_place_counts.csv", dtype={"person_id": str})
fbc = fbc[fbc.period == "sitting"].copy()
fbm["spell"] = fbm.person_id + "|" + fbm.seat
fbc["spell"] = fbc.person_id + "|" + fbc.seat

# ---- Commons: long table spell x month x query
rows = []
for r in Q.itertuples():
    for m, n in H[r.query_id].items():
        rows.append((r.spell, m, r.query_id, n))
HC = pd.DataFrame(rows, columns=["spell", "month", "query_id", "n"])
qi = Q.set_index("query_id")
tot = HC[HC.query_id.isin(Q.query_id[Q.g == "total"])].groupby(["spell", "month"]).n.sum().rename("items").reset_index()
tot = tot[tot["items"] > 0]
# placebo phrases are looked up in their own seat
def pattr(seat, phrase, col):
    try: return attr.loc[(seat, phrase), col]
    except KeyError: return np.nan
Q["pseat"] = np.where(Q.g == "placebo", Q.group.str.split(":", n=1).str[1], Q.seat)
Q["pop"] = [pattr(s, p, "pop") for s, p in zip(Q.pseat, Q.phrase)]
Q["ambiguous"] = [bool(pattr(s, p, "ambiguous")) if p else False for s, p in zip(Q.pseat, Q.phrase)]
Q["seatname"] = Q.g.eq("seat")
Q["rank"] = [pattr(s, p, "rank_in_seat") for s, p in zip(Q.pseat, Q.phrase)]
qi = Q.set_index("query_id")

# ---- Facebook: same phrases, same spells
key = Q[Q.g != "total"][["query_id", "spell", "phrase"]]
F = fbc.merge(key, on=["spell", "phrase"], how="inner")[["spell", "month", "query_id", "n_message", "n_any_field"]]
F = F[~F.query_id.isin(Q.query_id[Q.g == "placebo"])]
F = pd.concat([F, pd.read_csv(f"{DATA}/fb_placebo_counts.csv")], ignore_index=True)   # placebo places, counted by 04b
fitems = fbm[fbm.posts_with_message > 0][["spell", "month", "posts_with_message", "posts"]].rename(columns={"posts_with_message": "items"})

# ---- month panel
def agg(df, ncol, venue, items):
    d = df.merge(Q[["query_id", "g", "sample_weight", "ambiguous", "seatname"]], on="query_id")
    d["w"] = np.where(d.g == "random", d.sample_weight, 1.0)
    d["wn"] = d.w * d[ncol]
    out = {}
    main = d[d.g.isin(MAIN_GROUPS)]
    out["y_main"] = main.groupby(["spell", "month"]).wn.sum()
    out["y_main_unw"] = main.groupby(["spell", "month"])[ncol].sum()
    out["y_noamb"] = main[~main.ambiguous].groupby(["spell", "month"]).wn.sum()
    out["y_noseat"] = main[~main.seatname].groupby(["spell", "month"]).wn.sum()
    for g in ("seat", "pop", "random", "fb_top", "placebo"):
        sub = d[d.g == g]
        out["y_" + g] = sub.groupby(["spell", "month"])["wn" if g == "random" else ncol].sum()
    o = pd.DataFrame(out).reset_index()
    o = items.merge(o, on=["spell", "month"], how="left").fillna(0)
    o["venue"] = venue
    return o
cm = agg(HC.merge(Q[["query_id"]], on="query_id"), "n", "commons", tot)
fm = agg(F, "n_message", "facebook", fitems.drop(columns="posts"))
fa = agg(F, "n_any_field", "facebook", fitems.drop(columns="posts"))
fm["y_main_anyfield"] = fa["y_main"].values
cm["y_main_anyfield"] = cm["y_main"]
# keep FB months inside the query window of the spell
win = Q[Q.g == "total"].set_index("spell")[["start", "end"]]
fm = fm[[win.loc[s, "start"][:7] <= m <= win.loc[s, "end"][:7] for s, m in zip(fm.spell, fm.month)]]
pm = pd.concat([cm, fm], ignore_index=True)
pm["person_id"] = pm.spell.str.split("|").str[0]
pm["seat"] = pm.spell.str.split("|", n=1).str[1]
pm["fb"] = (pm.venue == "facebook").astype(int)
pm.to_csv(f"{DATA}/panel_months.csv", index=False)
print("month rows", len(pm), pm.groupby("venue").size().to_dict(), "spells", pm.spell.nunique())

# ---- place panel (totals over months where that venue has items)
def placetot(df, ncol, items, venue):
    d = df.merge(items[["spell", "month"]], on=["spell", "month"])
    t = d.groupby("query_id")[ncol].sum()
    it = items.groupby("spell")["items"].sum()
    o = Q[Q.g != "total"][["query_id", "spell", "person_id", "seat", "place", "phrase", "g", "sample_weight", "pop", "ambiguous", "seatname", "rank", "pseat"]].copy()
    o["count"] = o.query_id.map(t).fillna(0)
    o["items"] = o.spell.map(it)
    o["venue"] = venue
    return o[o["items"].notna()]
fm_items = fm[["spell", "month", "items"]]
pp = pd.concat([placetot(HC, "n", tot, "commons"), placetot(F, "n_message", fm_items, "facebook")], ignore_index=True)
pp.to_csv(f"{DATA}/panel_places.csv", index=False)
print("place rows", len(pp))

# ---- covariates per spell
mem = pd.read_csv(f"{DATA}/commons_memberships.csv", dtype=str)
pages = pd.read_csv(f"{DATA}/pages.csv", dtype=str).dropna(subset=["person_id"])
sp = Q[Q.g == "total"][["spell", "person_id", "seat", "member_name", "member_id", "start", "end"]].copy()
last = mem.sort_values("start").groupby(["person_id", "seat"]).party.agg(lambda s: s.iloc[-1])
first = mem.sort_values("start").groupby(["person_id", "seat"]).party.agg(lambda s: s.iloc[0])
sp["party"] = [first.get((p, s)) for p, s in zip(sp.person_id, sp.seat)]
sp["party_last"] = [last.get((p, s)) for p, s in zip(sp.person_id, sp.seat)]
seats = jload("/home/claude/studies/twins-remain/data/seats.geojson")["features"]
nat = {f["properties"]["seat"]: {"E": "England", "W": "Wales", "S": "Scotland"}[f["properties"]["code"][0]] for f in seats}
nat["Ynys Môn"] = nat.pop("Ynys Mon")
sp["nation"] = sp.seat.map(nat).fillna("Northern Ireland")
pg = pages.set_index("person_id")
sp["fb_id"] = sp.person_id.map(pg.fb_id)
sp["page_name"] = sp.person_id.map(pg.page_name)
raw = pd.read_csv(f"{DATA}/pages_raw.csv", dtype=str).set_index("fb_id")
sp["followers_last"] = pd.to_numeric(sp.fb_id.map(raw.likes_last), errors="coerce")
# majorities (vote share of winner minus runner-up) at 2015, 2017 and 2019
c = pd.read_csv(f"{ELEC}/candidates.csv", dtype={"election": str}, low_memory=False)
c = c[c.election.isin(["2015", "2017", "2019"])]
c["k"] = c.constituency.map(norm)
def maj(g):
    s = g.share.sort_values(ascending=False).values
    return s[0] - s[1] if len(s) > 1 else np.nan
M = c.groupby(["election", "k"]).apply(maj, include_groups=False)
alias = {"kingston upon hull east": "hull east", "kingston upon hull north": "hull north", "kingston upon hull west and hessle": "hull west and hessle"}
KS = set(c.k)
def mk(seat):
    k = norm(seat)
    if k in KS: return k
    m = re.match(r"(.+) (north|south|east|west|central)( and .+)?$", k)
    if m:
        k2 = f"{m.group(2)} {m.group(1)}{m.group(3) or ''}"
        if k2 in KS: return k2
    return alias.get(k, k)
for y in ("2015", "2017", "2019"):
    sp["maj" + y] = [M.get((y, mk(s)), np.nan) for s in sp.seat]
miss = sp[sp.maj2017.isna()].seat.unique()
print("seats without 2017 majority:", list(miss)[:10])
sp.to_csv(f"{DATA}/mp_covariates.csv", index=False)
