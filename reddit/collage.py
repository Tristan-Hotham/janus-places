"""Reddit collage (r/dataisbeautiful style), light background, 2700 x 2025 px: map of seats coloured by the Facebook minus
Commons gap, the two headline rates, every MP as a dot, and the frontbench result. Run after code/10_figures.py:
python3 reddit/collage.py"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "code"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib import font_manager as fm
from matplotlib.collections import PatchCollection
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Polygon as MPoly
import numpy as np, pandas as pd
from pyproj import Transformer
from shapely.geometry import shape
from shapely import transform as stf
from common import *

for f in ("FrauncesVar.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "IBMPlexMono-Regular.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
DISP = fm.FontProperties(fname=f"{FONTS}/FrauncesVar.ttf").get_name()
plt.rcParams.update({"font.family": "Source Serif 4", "axes.unicode_minus": False, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#6E604E", "xtick.color": "#6E604E", "ytick.color": "#6E604E"})
PAPER, INK, MUT, FB, CM = "#FAF6EC", "#2B2119", "#6E604E", "#B4442E", "#2F6A9E"
CMAP = LinearSegmentedColormap.from_list("g", ["#2F6A9E", "#C9C2B4", "#E9B49E", "#B4442E", "#6E1F12"])
HALO = [pe.withStroke(linewidth=4, foreground=PAPER)]
R = jload(f"{DATA}/results.json"); x = R["x"]
site = jload(f"{DATA}/site.json")["seats"]; gj = jload(f"{DATA}/seats_map.geojson")
T = Transformer.from_crs(4326, 27700, always_xy=True)

fig = plt.figure(figsize=(13.5, 10.125), dpi=200); fig.patch.set_facecolor(PAPER)
fig.text(0.035, 0.957, "Two faces of the constituency", family=DISP, fontsize=33, fontweight="bold", color=INK, va="top")
fig.text(0.035, 0.897, "How often UK MPs named the towns and villages in their own seat: on their Facebook page and in the House of Commons.\n"
         "Same MPs, same months, same pre-set list of places. February 2017 to October 2020.", fontsize=13.5, color=MUT, va="top")
# map
ax = fig.add_axes([0.0, 0.085, 0.47, 0.62]); ax.axis("off")
pats, cols = [], []
for f in gj["features"]:
    d = site.get(f["properties"]["s"]); g = shape(f["geometry"])
    g = stf(g, lambda a: np.column_stack(T.transform(a[:, 0], a[:, 1])))
    for p in (g.geoms if g.geom_type == "MultiPolygon" else [g]):
        pats.append(MPoly(np.asarray(p.exterior.coords), closed=True))
        cols.append(CMAP(np.clip((d[0]["g"] + 20) / 80, 0, 1)) if d else "#FFFFFF")
ax.add_collection(PatchCollection(pats, facecolor=cols, edgecolor="#BFB194", lw=0.12))
ax.set_xlim(-60000, 660000); ax.set_ylim(0, 1220000); ax.set_aspect("equal")
# legend on the sea, top left of the map panel
cax = fig.add_axes([0.045, 0.765, 0.16, 0.013])
cb = fig.colorbar(plt.cm.ScalarMappable(cmap=CMAP, norm=plt.Normalize(-20, 60)), cax=cax, orientation="horizontal")
cb.outline.set_visible(False); cax.tick_params(labelsize=10, colors=MUT)
fig.text(0.045, 0.825, "Each seat: Facebook minus Commons", fontsize=12.5, fontweight="bold", color=INK)
fig.text(0.045, 0.803, "own-seat place mentions per 100 items", fontsize=11, color=MUT)
fig.text(0.24, 0.80, f"red: more local on Facebook\n({R['map']['pos']} of {R['map']['n']} seats)\nwhite: no MP page in the list", fontsize=11, color=INK, va="top", linespacing=1.4)
# big numbers
def big(x0, y0, val, unit, col):
    fig.text(x0, y0, val, family=DISP, fontsize=64, fontweight="bold", color=col, va="top")
    fig.text(x0 + 0.105, y0 - 0.02, unit, fontsize=14, color=INK, va="top", linespacing=1.3)
big(0.50, 0.835, f"{x['fb_per100']:.0f}", "mentions per 100\nFacebook posts", FB)
big(0.75, 0.835, f"{x['cm_per100']:.0f}", "per 100 things said\nin the Commons", CM)
fig.text(0.50, 0.715, f"Same MP, same month: Facebook is {R['H1']['rr']:.1f}x as local (95% interval {R['H1']['lo']:.1f} to {R['H1']['hi']:.1f}).\n"
         f"Places in someone else's seat: no gap ({R['placebo']['rr']:.2f}x).", fontsize=13, color=INK, va="top", linespacing=1.4)
# scatter
mp = pd.read_csv(f"{DATA}/mp_gap.csv"); b = mp[(mp.items_facebook >= 20) & (mp.items_commons >= 20)]
a2 = fig.add_axes([0.54, 0.30, 0.20, 0.25]); a2.set_facecolor(PAPER)
a2.scatter(b.cm_rate.clip(upper=60), b.fb_rate.clip(upper=120), s=10, color=FB, alpha=.55, edgecolor="white", lw=.3)
a2.plot([0, 60], [0, 60], color=INK, lw=1, ls="--"); a2.set_xlim(0, 60); a2.set_ylim(0, 122)
a2.set_xlabel("Commons, per 100", fontsize=10.5, color=INK); a2.set_ylabel("Facebook, per 100", fontsize=10.5, color=INK); a2.tick_params(labelsize=9)
a2.text(58, 4, "equal\nrates", fontsize=9.5, color=INK, ha="right", va="bottom")
fig.text(0.50, 0.59, f"Each MP: {R['mp']['fb_higher']} of {R['mp']['n']} above the line", fontsize=13, fontweight="bold", color=INK)
# frontbench
a3 = fig.add_axes([0.81, 0.30, 0.15, 0.22]); a3.set_facecolor(PAPER)
vals = [R["H4"]["front_commons"], R["H4"]["front_facebook"]]
a3.bar([0, 1], [v["rr"] for v in vals], color=[CM, FB], width=.6)
for i, v in enumerate(vals):
    a3.plot([i, i], [v["lo"], v["hi"]], color=INK, lw=1.2)
    a3.text(i, v["hi"] + .04, f"{v['rr']:.2f}x", ha="center", fontsize=11, color=INK)
a3.axhline(1, color=MUT, lw=.8, ls=":"); a3.set_ylim(0, 1.35); a3.set_xticks([0, 1]); a3.set_xticklabels(["Commons", "Facebook"], fontsize=10.5)
a3.tick_params(axis="y", labelsize=9)
fig.text(0.785, 0.59, "On the front bench", fontsize=13, fontweight="bold", color=INK)
fig.text(0.785, 0.575, "local naming vs the same\nMP's other months", fontsize=10, color=MUT, va="top")
fig.text(0.50, 0.245, f"In the months an MP was on the front bench, their Commons local naming\nwas {x['front_cm_drop_pc']:.0f}% lower than in their other months. Their Facebook rate did not change.\nIn marginal seats the gap was smaller, not bigger.", fontsize=12.5, color=INK, va="top", linespacing=1.4)
fig.text(0.50, 0.135, f"{R['sample']['spells']} MP-seat spells, {R['sample']['posts']:,} posts, {R['sample']['contributions']:,} Commons contributions. Counts only.\n"
         "Posts start in February 2017: the export hit CrowdTangle's 300,000-row cap.", fontsize=11, color=MUT, va="top", linespacing=1.4)
fig.text(0.035, 0.022, "Data: the author's CrowdTangle list of MPs' Facebook pages (counts only); Hansard via the UK Parliament API (Open Parliament Licence v3.0);"
         "\nmySociety parlparse; Wikidata (CC0) · Dr Tristan Hotham · maps.tristanhotham.com/janus-places", fontsize=9.5, family="IBM Plex Mono", color=MUT, va="bottom", linespacing=1.5)
out = os.path.join(HERE, "janus_places_collage.png")
fig.savefig(out, dpi=200, facecolor=PAPER); plt.close(fig)
from PIL import Image
print(Image.open(out).size)
