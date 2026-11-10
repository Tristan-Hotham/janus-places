"""Step 10: figures for the page (img/*.jpg), the blog (release/blog/b_*.png, 1800 px), the paper (release/paper/f_*.pdf)
and header.png (1200 x 630). Light paper; Facebook = warm red, Commons = blue (venues, never parties)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib import font_manager as fm
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon as MPoly
import numpy as np, pandas as pd
from PIL import Image
from pyproj import Transformer
from shapely.geometry import shape
from shapely.ops import transform as stransform
from common import *

for f in ("FrauncesVar.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "SourceSerif4-It.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
SERIF = "Source Serif 4"; DISP = fm.FontProperties(fname=f"{FONTS}/FrauncesVar.ttf").get_name(); MONO = "IBM Plex Mono"
PAPER, INK, MUT, RULE = "#F6EED8", "#2B2119", "#6E604E", "#D9C9A3"
FB, CM, GREY = "#B4442E", "#2F6A9E", "#9C9384"
CMAP = LinearSegmentedColormap.from_list("g", ["#2F6A9E", "#C9C2B4", "#E9B49E", "#B4442E", "#6E1F12"])
plt.rcParams.update({"font.family": SERIF, "font.size": 12, "axes.edgecolor": MUT, "axes.labelcolor": INK, "xtick.color": MUT,
                     "ytick.color": MUT, "axes.facecolor": PAPER, "figure.facecolor": PAPER, "axes.unicode_minus": False,
                     "pdf.fonttype": 42, "axes.spines.top": False, "axes.spines.right": False})
HALO = [pe.withStroke(linewidth=3, foreground=PAPER)]
R = jload(f"{DATA}/results.json")
BLOG, PAPD = f"{REL}/blog", f"{REL}/paper"
for d_ in (BLOG, PAPD): os.makedirs(d_, exist_ok=True)
SRC = ("Data: the author's CrowdTangle list of MPs' Facebook pages (aggregates only); Hansard, UK Parliament API (OPL v3.0)\n"
       "February 2017 to October 2020 · maps.tristanhotham.com/janus-places")


def out(fig, name, page=True, blog=True, paper=True):
    from matplotlib.ticker import NullFormatter, ScalarFormatter
    for a in fig.axes:
        for ax_ in (a.xaxis, a.yaxis):
            if ax_.get_scale() == "log":
                ax_.set_minor_formatter(NullFormatter())
    if paper: fig.savefig(f"{PAPD}/f_{name}.pdf", facecolor=fig.get_facecolor())
    fig.savefig(f"{SCR}/{name}.png", dpi=220, facecolor=fig.get_facecolor()); plt.close(fig)
    im = Image.open(f"{SCR}/{name}.png").convert("RGB")
    if page:
        w = min(1500, im.size[0]); im.resize((w, round(im.size[1] * w / im.size[0])), Image.LANCZOS).save(f"{IMG}/{name}.jpg", quality=85, optimize=True)
    if blog:
        im.resize((1800, round(im.size[1] * 1800 / im.size[0])), Image.LANCZOS).save(f"{BLOG}/b_{name}.png", optimize=True)
    os.remove(f"{SCR}/{name}.png")


def title(fig, t, sub, y=0.965):
    fig.text(0.04, y, t, fontsize=21, fontweight="bold", family=DISP, color=INK, va="top")
    fig.text(0.04, y - 0.06, sub, fontsize=12, color=MUT, va="top")


def foot(fig, s=SRC):
    fig.text(0.04, 0.012, s, fontsize=8, family=MONO, color=MUT, va="bottom", linespacing=1.4)


# ---------------------------------------------------------------- 1. every MP: two rates
mp = pd.read_csv(f"{DATA}/mp_gap.csv")
b = mp[(mp.items_facebook >= 20) & (mp.items_commons >= 20)]
fig = plt.figure(figsize=(9, 8.6)); ax = fig.add_axes([0.11, 0.15, 0.84, 0.66])
ax.scatter(b.cm_rate, b.fb_rate, s=np.clip(np.sqrt(b.items_facebook) * 1.1, 8, 70), color=FB, alpha=.55, edgecolor="white", lw=.5, zorder=3)
lim = max(b.cm_rate.max(), 45) * 1.05
ax.plot([0, lim], [0, lim], color=INK, lw=1, ls="--", zorder=2)
ax.text(lim * .80, lim * .80 + 3, "same rate\nin both", color=INK, fontsize=10.5, ha="center", va="bottom", path_effects=HALO)
ax.set_xlim(0, lim); ax.set_ylim(0, max(b.fb_rate.max() * 1.05, 90))
ax.set_xlabel("Commons: own-seat place mentions per 100 spoken contributions"); ax.set_ylabel("Facebook: own-seat place mentions per 100 posts")
ax.text(lim * .97, 4, f"{R['mp']['fb_higher']} of {R['mp']['n']} MPs\nname their patch more\noften on Facebook", ha="right", va="bottom", fontsize=12, color=FB, family=DISP, fontweight="bold", path_effects=HALO)
ax.grid(color=RULE, lw=.6, zorder=0)
title(fig, "Two faces of the constituency", f"Each dot is one MP ({R['mp']['n']} with 20 or more items in each venue). Medians: {R['mp']['fb_median']:.0f} mentions\nper 100 Facebook posts, {R['mp']['cm_median']:.0f} per 100 Commons contributions. Dot size: number of posts.", y=0.97)
foot(fig); out(fig, "scatter")

# ---------------------------------------------------------------- 2. month by month
mon = pd.read_csv(f"{DATA}/monthly.csv")
mon = mon[(mon.items_facebook >= 500) & (mon.items_commons >= 500)]
fig = plt.figure(figsize=(11, 6.4)); ax = fig.add_axes([0.08, 0.15, 0.9, 0.58])
x = np.array([mi(m) for m in mon.month])
for a, b_, lab in ((mi("2017-05"), mi("2017-06"), "2017\nelection"), (mi("2019-11"), mi("2019-12"), "2019\nelection")):
    ax.axvspan(a - .5, b_ + .5, color="#E9DEC2", zorder=0); ax.text((a + b_) / 2, 63, lab, ha="center", fontsize=9.5, color=MUT, va="top")
ax.axvspan(mi(BREXIT[0]) - .5, mi(BREXIT[1]) + .5, color="#EFE6D0", zorder=0); ax.text((mi(BREXIT[0]) + mi(BREXIT[1])) / 2, 63, "Brexit votes", ha="center", fontsize=9.5, color=MUT, va="top")
ax.axvline(mi(COVID) - .5, color=MUT, lw=1, ls=":"); ax.text(mi(COVID), 63, "COVID", fontsize=9.5, color=MUT, va="top")
ax.plot(x, mon.fb_rate, color=FB, lw=2.4, marker="o", ms=3.5); ax.plot(x, mon.cm_rate, color=CM, lw=2.4, marker="o", ms=3.5)
ax.text(x[-1] + .4, mon.fb_rate.iloc[-1], "Facebook", color=FB, fontsize=12, va="center", fontweight="bold")
ax.text(x[-1] + .4, mon.cm_rate.iloc[-1], "Commons", color=CM, fontsize=12, va="center", fontweight="bold")
ticks = [m for m in range(0, 46) if m % 6 == 0]
ax.set_xticks(ticks); ax.set_xticklabels([f"{['Jan', 'Jul'][(t % 12) // 6]} {2017 + t // 12}" for t in ticks])
ax.set_xlim(x.min() - 1, x.max() + 5); ax.set_ylim(0, 65); ax.set_ylabel("Own-seat place mentions per 100 items")
ax.grid(axis="y", color=RULE, lw=.6)
title(fig, "Every month, Facebook is more local", "All matched MPs pooled; months where both venues have at least 500 items\n(Parliament does not sit during election campaigns or most of August).")
foot(fig); out(fig, "monthly")

# ---------------------------------------------------------------- 3. which places
rt = R["rate"]
grp = [("Places in the seat's name", "y_seat"), ("Most populous other places", "y_pop"), ("Random sample of other places\n(scaled to the whole seat)", "y_random"),
       ("Places in a different seat\n(placebo)", "y_placebo")]
fig = plt.figure(figsize=(10, 6.2)); ax = fig.add_axes([0.32, 0.2, 0.64, 0.56])
yy = np.arange(len(grp))[::-1]
for i, (lab, k) in enumerate(grp):
    f, c = rt["facebook"][k], rt["commons"][k]
    ax.barh(yy[i] + .18, f, height=.34, color=FB); ax.barh(yy[i] - .18, c, height=.34, color=CM)
    ax.text(f + .3, yy[i] + .18, f"{f:.1f}" if f >= .1 else f"{f:.2f}", va="center", fontsize=10.5, color=FB)
    ax.text(c + .3, yy[i] - .18, f"{c:.1f}" if c >= .1 else f"{c:.2f}", va="center", fontsize=10.5, color=CM)
ax.set_yticks(yy); ax.set_yticklabels([g[0] for g in grp]); ax.set_xlabel("Mentions per 100 posts (Facebook) or per 100 spoken contributions (Commons)")
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color=FB, label="Facebook"), Patch(color=CM, label="Commons")], frameon=False, loc="lower right")
ax.grid(axis="x", color=RULE, lw=.6)
title(fig, "The gap holds for every kind of place", "The same place list for each MP in both venues. Places in someone else's seat are rare in both.")
foot(fig); out(fig, "groups")

# ---------------------------------------------------------------- 4. size of place
pp = pd.read_csv(f"{DATA}/panel_places.csv")
pp = pp[pp.g.isin(["pop", "random"]) & pp["pop"].gt(0)].copy()
pp["w"] = np.where(pp.g == "random", pp.sample_weight, 1.0)
bins = [0, 1000, 5000, 20000, 100000, 1e7]; labs = ["under 1,000", "1,000 to 5,000", "5,000 to 20,000", "20,000 to 100,000", "100,000 and over"]
pp["bin"] = pd.cut(pp["pop"], bins, labels=labs, right=False)
items = pp.drop_duplicates(["spell", "venue"]).groupby("venue")["items"].sum()
fig = plt.figure(figsize=(10, 6.2)); ax = fig.add_axes([0.1, 0.2, 0.86, 0.56])
xs = np.arange(len(labs))
for v, col, off in (("facebook", FB, .18), ("commons", CM, -.18)):
    d = pp[pp.venue == v]
    # mentions per place per 1,000 items of that MP
    d = d.assign(r=d["count"] / d["items"] * 1000)
    m = d.groupby("bin", observed=False).apply(lambda g: np.average(g.r, weights=g.w) if len(g) else np.nan, include_groups=False)
    ax.bar(xs + off, m.values, width=.34, color=col, label="Facebook" if v == "facebook" else "Commons")
    for xi, val in zip(xs, m.values):
        ax.text(xi + off, val * 1.08, f"{val:.1f}" if val >= 1 else f"{val:.2f}", ha="center", fontsize=9.5, color=col)
ax.set_yscale("log"); ax.set_yticks([0.3, 1, 3, 10, 30, 100]); ax.set_yticklabels(["0.3", "1", "3", "10", "30", "100"]); ax.set_xticks(xs); ax.set_xticklabels(labs); ax.set_xlabel("Population of the place"); ax.set_ylabel("Mentions of one place per 1,000 items (log)")
ax.legend(frameon=False, loc="upper left"); ax.grid(axis="y", color=RULE, lw=.6)
title(fig, "Bigger places get named more, in both venues", f"Places other than those in the seat's name. Facebook's lead is similar at every size (elasticity {R['H2']['el_fb']:.2f} vs {R['H2']['el_commons']:.2f}).")
foot(fig); out(fig, "size")

# ---------------------------------------------------------------- 5. who and when (heterogeneity)
rows = [("Frontbench months: Commons", R["H4"]["front_commons"]), ("Frontbench months: Facebook", R["H4"]["front_facebook"]),
        ("COVID months (from March 2020): Commons", R["H5"]["commons_covid"]), ("COVID months: Facebook", R["H5"]["facebook_covid"]),
        ("Brexit votes, 2019: Commons", R["H5"]["commons_brexit"]), ("Brexit votes, 2019: Facebook", R["H5"]["facebook_brexit"]),
        ("Gap: marginal seat (majority under 10 points)", R["H3"]["marginal"]), ("Gap: frontbench months", R["H4"]["front"]), ("Gap: government side", R["H4"]["gov"])]
fig = plt.figure(figsize=(10, 7.2)); ax = fig.add_axes([0.42, 0.16, 0.54, 0.64])
for i, (lab, c) in enumerate(rows[::-1]):
    col = FB if "Facebook" in lab else CM if "Commons" in lab else INK
    ax.plot([c["lo"], c["hi"]], [i, i], color=col, lw=2.2); ax.plot(c["rr"], i, "o", color=col, ms=7)
    ax.text(c["hi"] * 1.06, i, f"{c['rr']:.2f}", va="center", fontsize=10, color=col)
ax.axvline(1, color=MUT, lw=1, ls="--"); ax.set_xscale("log"); ax.set_xticks([.2, .5, 1, 2, 4]); ax.set_xticklabels(["0.2", "0.5", "1", "2", "4"])
ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in rows[::-1]]); ax.set_xlabel("Rate ratio (log scale; 1 = no difference)")
ax.grid(axis="x", color=RULE, lw=.6)
title(fig, "Office moves the Commons face, not the Facebook one", "Within-MP rate ratios with 95% intervals. Rows marked Gap: how much bigger the Facebook to Commons ratio is.")
foot(fig); out(fig, "who")

# ---------------------------------------------------------------- 6. robustness
rb = R["robust"]
order = [("Main estimate", R["H1"])] + [(v["label"], v) for v in rb.values()] + [("Placebo: places in another seat", R["placebo"])]
fig = plt.figure(figsize=(10, 8.6)); ax = fig.add_axes([0.42, 0.13, 0.54, 0.71])
for i, (lab, c) in enumerate(order[::-1]):
    col = INK if lab == "Main estimate" else GREY if "Placebo" in lab else FB
    ax.plot([c["lo"], c["hi"]], [i, i], color=col, lw=2); ax.plot(c["rr"], i, "o", color=col, ms=6)
ax.axvline(1, color=MUT, lw=1, ls="--"); ax.set_xscale("log"); ax.set_xticks([.5, 1, 2, 4, 8]); ax.set_xticklabels(["0.5", "1", "2", "4", "8"])
ax.set_yticks(range(len(order))); ax.set_yticklabels([o[0] for o in order[::-1]], fontsize=10.5); ax.set_xlabel("Facebook to Commons rate ratio (log scale)")
ax.grid(axis="x", color=RULE, lw=.6)
title(fig, "Every check points the same way", f"{R['robust_range']['n']} checks: rate ratios from {R['robust_range']['min']:.1f} to {R['robust_range']['max']:.1f}. The placebo stays at about 1.", y=0.975)
foot(fig); out(fig, "robust")

# ---------------------------------------------------------------- 7. static map
site = jload(f"{DATA}/site.json")["seats"]
gj = jload(f"{DATA}/seats_map.geojson")
T = Transformer.from_crs(4326, 27700, always_xy=True)
def polys(g):
    g = stransform(T.transform, shape(g))
    return list(g.geoms) if g.geom_type == "MultiPolygon" else [g]
def draw_map(ax, lw=.15):
    pats, cols = [], []
    for f in gj["features"]:
        s = f["properties"]["s"]; d = site.get(s)
        val = d[0]["g"] if d else None
        for p in polys(f["geometry"]):
            pats.append(MPoly(np.asarray(p.exterior.coords), closed=True))
            cols.append(CMAP(np.clip((val + 20) / 80, 0, 1)) if val is not None else "#FBF7EC")
    ax.add_collection(PatchCollection(pats, facecolor=cols, edgecolor="#CDBF9E", lw=lw))
    ax.set_xlim(-80000, 680000); ax.set_ylim(0, 1230000); ax.set_aspect("equal"); ax.axis("off")
fig = plt.figure(figsize=(8, 10)); ax = fig.add_axes([0.02, 0.06, 0.96, 0.8]); draw_map(ax)
cax = fig.add_axes([0.06, 0.82, 0.4, 0.014]); sm = plt.cm.ScalarMappable(cmap=CMAP, norm=plt.Normalize(-20, 60)); cb = fig.colorbar(sm, cax=cax, orientation="horizontal")
cb.set_label("Facebook minus Commons, mentions per 100 items", fontsize=9.5); cb.outline.set_visible(False); cax.tick_params(labelsize=9)
fig.text(0.06, 0.748, "Pale cream: no matched MP page", fontsize=9.5, color=MUT)
title(fig, "Where the gap is widest", f"2010 seats with a matched MP ({len(site)} of 650), coloured by the MP's local naming gap.", y=0.975)
foot(fig); out(fig, "map")

# ---------------------------------------------------------------- header.png
fig = plt.figure(figsize=(12, 6.3), dpi=100)
ax = fig.add_axes([0.6, 0.02, 0.38, 0.96]); draw_map(ax, lw=.08)
fig.text(0.05, 0.86, "Two faces of", fontsize=40, family=DISP, fontweight="bold", color=INK)
fig.text(0.05, 0.75, "the constituency", fontsize=40, family=DISP, fontweight="bold", color=FB)
fig.text(0.05, 0.62, "What MPs name on Facebook and in the Commons", fontsize=17, color=INK)
fig.text(0.05, 0.45, f"{R['x']['fb_per100']:.0f}", fontsize=60, family=DISP, fontweight="bold", color=FB)
fig.text(0.19, 0.47, "own-seat place mentions\nper 100 Facebook posts", fontsize=14, color=INK)
fig.text(0.05, 0.27, f"{R['x']['cm_per100']:.0f}", fontsize=60, family=DISP, fontweight="bold", color=CM)
fig.text(0.19, 0.29, "per 100 Commons\ncontributions", fontsize=14, color=INK)
fig.text(0.05, 0.07, "Dr Tristan Hotham · 2017 to 2020 · maps.tristanhotham.com/janus-places", fontsize=11, family=MONO, color=MUT)
fig.savefig(f"{ROOT}/header.png", dpi=100, facecolor=PAPER); plt.close(fig)
print(Image.open(f"{ROOT}/header.png").size)
