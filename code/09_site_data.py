"""Step 9: map data. data/seats_map.geojson (2010 seats: GB from twins-remain, NI simplified from martinjc/UK-GeoJSON) and
data/site.json: per seat, each matched MP spell with its two rates and the queried places named in each venue.
Only counts and rates; no post text."""
import pandas as pd, numpy as np
from shapely.geometry import shape, mapping
from common import *

R = jload(f"{DATA}/results.json")
mpg = pd.read_csv(f"{DATA}/mp_gap.csv", dtype={"person_id": str})
pp = pd.read_csv(f"{DATA}/panel_places.csv", dtype={"person_id": str})
feats = []
for f in jload("/home/claude/studies/twins-remain/data/seats.geojson")["features"]:
    nm = f["properties"]["seat"]; nm = "Ynys Môn" if nm == "Ynys Mon" else nm
    g = shape(f["geometry"]).simplify(0.0008, preserve_topology=True)
    feats.append({"type": "Feature", "properties": {"s": nm}, "geometry": mapping(g)})
mem = pd.read_csv(f"{DATA}/commons_memberships.csv", dtype=str)
ni = {s.upper(): s for s in mem.seat.unique()}
for f in jload(f"{SCR}/dl/ni_wpc.json")["features"]:
    g = shape(f["geometry"]).simplify(0.002, preserve_topology=True)
    feats.append({"type": "Feature", "properties": {"s": ni[f["properties"]["PC_NAME"]]}, "geometry": mapping(g)})
def rnd(o):
    if isinstance(o, float): return round(o, 4)
    if isinstance(o, (list, tuple)): return [rnd(v) for v in o]
    if isinstance(o, dict): return {k: rnd(v) for k, v in o.items()}
    return o
gj = {"type": "FeatureCollection", "features": [{"type": "Feature", "properties": f["properties"], "geometry": rnd(f["geometry"])} for f in feats]}
jsave(gj, f"{DATA}/seats_map.geojson")
S = {}
fam = {"Conservative": "Conservative", "Labour": "Labour", "Labour/Co-operative": "Labour (Co-op)", "Scottish National Party": "SNP"}
for r in mpg.itertuples():
    if not (r.items_facebook > 0 and r.items_commons > 0):
        continue
    sp = pp[pp.spell == r.spell]
    pl = []
    for q in sp[sp.g.isin(["seat", "pop", "random", "fb_top"])].drop_duplicates("query_id").itertuples():
        f = sp[(sp.query_id == q.query_id) & (sp.venue == "facebook")]["count"].sum()
        c = sp[(sp.query_id == q.query_id) & (sp.venue == "commons")]["count"].sum()
        pl.append([q.place, q.phrase.startswith("in "), int(f), int(c), q.g])
    pl.sort(key=lambda a: -(a[2] / r.items_facebook + a[3] / r.items_commons))
    S.setdefault(r.seat, []).append(dict(m=r.member_name, p=r.party, f=round(r.fb_rate, 2), c=round(r.cm_rate, 2), g=round(r.gap, 2),
                                         nf=int(r.items_facebook), nc=int(r.items_commons), pl=pl[:14], ok=bool(r.items_facebook >= 20 and r.items_commons >= 20)))
for k in S:
    S[k].sort(key=lambda d: -d["nf"])
site = dict(seats=S, n_seats=len(S), x=dict(fb=round(R["x"]["fb_per100"], 1), cm=round(R["x"]["cm_per100"], 1)))
jsave(site, f"{DATA}/site.json")
print(len(gj["features"]), len(S), os.path.getsize(f"{DATA}/seats_map.geojson") // 1024, "KB", os.path.getsize(f"{DATA}/site.json") // 1024, "KB")
