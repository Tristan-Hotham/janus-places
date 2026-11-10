"""Shared paths, constants and helpers for janus-places ("Two faces of the constituency").

Inputs:
  CT_CSV                  CrowdTangle historical export of the author's "UK - MPs" Facebook list (October 2020). Streamed in
                          chunks by 00 and 04; never copied. Only page names, ids, dates and counts leave it.
  data/commons_memberships.csv, data/frontbench_posts.csv   from mySociety parlparse (members/people.json and
                          members/ministers-2010.json, GitHub), which mirror data.parliament (Open Parliament Licence v3.0).
  data/seat_places.csv    place lists per 2010 seat (03).
  hansard_queries.json    the fixed query list (05); hansard_counts.json: monthly counts returned by the UK Parliament
                          Hansard API (timeline statistics, House of Commons, Spoken, member filter, exact phrase),
                          Open Parliament Licence v3.0, retrieved 2026.
  ELEC/candidates.csv     Who Won Here? (Hotham 2026, doi:10.5281/zenodo.23761425): candidate vote shares 2015 to 2019.
"""
import json, os, re, math, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
IMG = os.path.join(ROOT, "img")
REL = os.path.join(ROOT, "release")
SCR = os.environ.get("JP_SCRATCH", "/home/claude/scratch/janus-places")
ELEC = os.environ.get("JP_ELEC", "/home/claude/ref/elections-since-1832/data")
FONTS = os.environ.get("JP_FONTS", "/home/claude/ref/fonts")
CT_CSV = ("/mnt/user-data/uploads/l/crowdtangle data/"
          "2020-10-28-15-42-17-GMT-Historical-Report-UK---MPs-2010-01-01--2020-10-29.csv")
for d in (DATA, IMG):
    os.makedirs(d, exist_ok=True)

SLUG = "janus-places"
TITLE = "Two faces of the constituency"
SUBTITLE = "What MPs name on Facebook and in the Commons, 2017 to 2020"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")
BYLINE = "Dr Tristan Hotham · Independent researcher · 2026"
W0, W1 = "2017-02-11", "2020-10-28"
MAIN_GROUPS = ("seat", "pop", "random")
# events
GE = {"2017-06": "General election 2017", "2019-12": "General election 2019"}
BREXIT = ("2019-01", "2019-10")        # meaningful votes to the October deal
COVID = "2020-03"
CS = ("2017-06-26", "2019-12-12")      # DUP confidence and supply agreement (government side)


def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    s = s.replace("&", "and")
    s = re.sub(r"[’'`]", "", s)
    s = re.sub(r"[^a-z0-9]+", " ", s).strip()
    return s


def nonan(v):
    if isinstance(v, float) and (v != v or v in (float("inf"), float("-inf"))):
        return None
    if isinstance(v, (list, tuple)):
        return [nonan(x) for x in v]
    if isinstance(v, dict):
        return {str(k): nonan(x) for k, x in v.items()}
    if hasattr(v, "item"):
        return nonan(v.item())
    return v


def jload(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def jsave(obj, p, indent=None):
    with open(p, "w", encoding="utf-8") as f:
        json.dump(nonan(obj), f, ensure_ascii=False, allow_nan=False, indent=indent,
                  separators=None if indent else (",", ":"))


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "pc1": return f"{float(v):.1f}%"
    if f == "f0": return f"{float(v):.0f}"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "f3": return f"{float(v):.3f}"
    if f == "abs0": return f"{abs(float(v)):.0f}"
    if f == "abs1": return f"{abs(float(v)):.1f}"
    raise ValueError(f)


def fill(t, R, keep=("DOI", "DOI_URL", "BLOG_URL")):
    t = re.sub(r"\{\{([^{}|]+)(\|(\w+))?\}\}",
               lambda m: m.group(0) if m.group(1) in keep or m.group(1).startswith("IMG") or m.group(1).startswith("TABLE")
               else fmt(get(R, m.group(1)), m.group(3)), t)
    return t


def mi(ym):
    y, m = (int(x) for x in ym.split("-")[:2])
    return (y - 2017) * 12 + m - 1
