"""Step 13: blog post and meta (release/blog), Zenodo files and metadata (release/zenodo).
10.5281/zenodo.24105795, https://doi.org/10.5281/zenodo.24105795 and https://blog.tristanhotham.com/2026/10/31/janus-places/ are left for the publisher to fill."""
import json as _json, shutil, zipfile
from PIL import Image
from common import *

R = jload(f"{DATA}/results.json")
NAME = "Hotham_Two_Faces_Constituency"
KEEP = {"DOI", "DOI_URL", "BLOG_URL"}
post = open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read()
post = re.sub(r"\{\{(?!IMG)([^{}|]+)(\|(\w+))?\}\}", lambda m: m.group(0) if m.group(1) in KEEP else fmt(get(R, m.group(1)), m.group(3)), post)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8, len(used)
assert all(re.search(r"^\{\{IMG\|" + re.escape(u_), post, re.M) for u_ in used) and "wp:image" not in post
for img in used:
    assert Image.open(f"{REL}/blog/{img}").size[0] == 1800, img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
assert set(re.findall(r"\{\{([^|}]+)\}\}", post)) <= KEEP
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
for bad in ("\u2014", "\u2013", "--", "D" "SIT", "D" "CMS", "civil" " serv", "pre-" "registered"):
    assert bad not in vis, bad
assert AI in post
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
meta = {"title": "Two faces of the constituency",
        "slug": "janus-places",
        "excerpt": f"How often do MPs name the towns and villages they represent? On Facebook, {R['x']['fb_per100']:.0f} times per 100 posts. In the Commons, {R['x']['cm_per100']:.0f} times per 100 contributions. The same MPs, the same places, 2017 to 2020.",
        "seo_description": f"MPs named their own seat's places {R['x']['fb_per100']:.0f} times per 100 Facebook posts and {R['x']['cm_per100']:.0f} per 100 Commons contributions, 2017 to 2020.",
        "tags": ["maps", "data visualisation", "Parliament", "Hansard", "Facebook", "social media", "places", "representation"],
        "header_alt": "Title card on cream paper reading 'Two faces of the constituency' with the numbers 42 and 9 beside a map of UK constituencies, most shaded red."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
_json.dump(meta, open(f"{REL}/blog/meta.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)
for fn in os.listdir(Z):
    os.remove(os.path.join(Z, fn))
shutil.copy(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/{SLUG}_data_and_code.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for fn in sorted(os.listdir(os.path.join(ROOT, "code"))):
        if fn.endswith((".pyc", ".png")) or fn == "__pycache__":
            continue
        z.write(os.path.join(ROOT, "code", fn), f"{SLUG}/code/{fn}")
    for fn in sorted(os.listdir(DATA)):
        z.write(os.path.join(DATA, fn), f"{SLUG}/data/{fn}")
    for fn in ("README.md", "LICENSE", "NOTES.md", "hansard_queries.json", "hansard_counts.json"):
        z.write(os.path.join(ROOT, fn), f"{SLUG}/{fn}")
    z.write(os.path.join(REL, "paper", "cover_note.md"), f"{SLUG}/release/paper/cover_note.md")
    z.write(os.path.join(ROOT, "reddit", "collage.py"), f"{SLUG}/reddit/collage.py")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\&", "&").replace("$", "").replace("``", "\"").replace("''", "\"")
zmeta = {"title": "Two Faces of the Constituency: How Often British MPs Name the Places They Represent on Facebook and in the House of Commons, 2017 to 2020",
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{PAGE}\">{PAGE}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: {{https://blog.tristanhotham.com/2026/10/31/janus-places/}}.</p>"
                        "<p>Sources: the author's CrowdTangle list of UK MPs' Facebook pages, exported October 2020 (aggregate counts only; no post text, links or URLs are shared); "
                        "Hansard via the UK Parliament Hansard API (Open Parliament Licence v3.0); mySociety parlparse members data (House of Commons records, Open Parliament Licence v3.0); "
                        "Wikidata (CC0); Mentioned in the House (doi:10.5281/zenodo.23761431); Who Won Here? (doi:10.5281/zenodo.23761425); Northern Ireland boundaries from martinjc/UK-GeoJSON (Open Government Licence v3.0). "
                        "Text, figures and data CC BY 4.0; code MIT.</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["constituency representation", "home style", "Members of Parliament", "Facebook", "social media", "House of Commons", "Hansard", "United Kingdom"],
         "license": "cc-by-4.0", "language": "eng",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE, "relation": "isSupplementedBy", "resource_type": "other"},
                                 {"identifier": "10.5281/zenodo.23761431", "relation": "isDerivedFrom", "resource_type": "publication"},
                                 {"identifier": "10.5281/zenodo.23761425", "relation": "isDerivedFrom", "resource_type": "publication"}],
         "files": sorted(os.listdir(Z))}
sj = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
for bad in ("\u2014", "\u2013", "--", "D" "SIT", "D" "CMS"):
    assert bad not in sj, bad
_json.dump(zmeta, open(f"{Z}/metadata.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("blog words", words, "figures", len(used), "; zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")
