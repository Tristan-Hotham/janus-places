"""Step 11: the paper. Fills code/paper_template.tex from data/results.json, adds tables, compiles with xelatex.
Output: release/paper/Hotham_Two_Faces_Constituency.pdf and .tex. The DOI stays the placeholder https://doi.org/10.5281/zenodo.24105795 unless
the environment variable DOI is set:  DOI=10.5281/zenodo.N python3 code/11_paper.py"""
import subprocess, pandas as pd
from common import *

R = jload(f"{DATA}/results.json")
OUT = os.path.join(REL, "paper"); NAME = "Hotham_Two_Faces_Constituency"
Q = pd.DataFrame(jload(f"{ROOT}/hansard_queries.json")); Q["g"] = Q.group.str.split(":").str[0]
gc = Q.g.value_counts()
def tex(s): return str(s).replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#")
def ci(c, k="rr", d=2): return f"{c[k]:.{d}f} [{c['lo']:.{d}f}, {c['hi']:.{d}f}]"
S = R["sample"]
TS = ("\\begin{table}[tbp]\\centering\\small\\caption{Data flow and the fixed Hansard query list.}\\label{tab:sample}\\begin{tabular}{lr}\\toprule Item & Number\\\\\\midrule\n"
      f"Rows in the CrowdTangle export (cap 300,000) & {S['csv_rows']:,}\\\\\n"
      f"Pages in the list & {S['pages']:,}\\\\\n\\quad matched to a sitting MP & {S['matched']:,}\\\\\n\\quad excluded & {S['excluded']:,}\\\\\n"
      f"Posts on days the MP held the seat & {S['posts_all_sitting']:,}\\\\\n\\quad campaign posts (dissolution, re-elected MPs) & {S['posts_campaign']:,}\\\\\n"
      f"\\quad posts on other days, dropped & {S['posts_outside']:,}\\\\\n"
      f"Seat-place rows in the place lists & {S['places_rows']:,}\\\\\\midrule\n"
      f"Hansard queries & {S['queries']:,}\\\\\n"
      f"\\quad total contributions (denominator) & {gc['total']:,}\\\\\n\\quad places in the seat's name & {gc['seat']:,}\\\\\n"
      f"\\quad most populous other places & {gc['pop']:,}\\\\\n\\quad random sample of other places & {gc['random']:,}\\\\\n"
      f"\\quad MP's most-named Facebook places (descriptive) & {gc['fb_top']:,}\\\\\n\\quad placebo places in another seat & {gc['placebo']:,}\\\\\\midrule\n"
      f"Spells with items in both venues (analysis sample) & {S['spells']:,}\\\\\n\\quad MPs & {S['mps']:,}\\\\\n\\quad seats & {S['seats']:,}\\\\\n"
      f"Posts with a message in the sample & {S['posts']:,}\\\\\nSpoken Commons contributions in the sample & {S['contributions']:,}\\\\\n"
      f"Spell-venue-months & {S['rows']:,}\\\\\\bottomrule\\end{{tabular}}\\end{{table}}")
rt = R["rate"]
rows = ""
for lab, k, c in (("Main place set", "y_main", R["H1"]), ("Places in the seat's name", "y_seat", R["robust"]["seatonly"]),
                  ("Most populous other places", "y_pop", R["robust"]["poponly"]), ("Random sample of other places (weighted)", "y_random", R["robust"]["random"]),
                  ("Placebo: places in another seat", "y_placebo", R["placebo"])):
    rows += f"{lab} & {rt['facebook'][k]:.2f} & {rt['commons'][k]:.2f} & {ci(c)} & {'$<$0.001' if c['p'] < 0.001 else f"{c['p']:.3f}"}\\\\\n"
TM = ("\\begin{table}[tbp]\\centering\\small\\caption{Own-seat place mentions per 100 items in each venue, and the within-MP Facebook to Commons rate ratio "
      "(PPML with spell and month fixed effects, offset log items, standard errors clustered by spell; 95\\% CI). "
      f"N = {R['H1']['n']:,} spell-venue-months, {R['H1']['spells']} spells.}}\\label{{tab:main}}"
      "\\begin{tabular}{lrrlr}\\toprule Places & Facebook & Commons & Rate ratio [95\\% CI] & $p$\\\\\\midrule\n" + rows +
      "\\bottomrule\\end{tabular}\\end{table}")
H = R["H4"]
rows = (f"H2: population elasticity, Commons & {R['H2']['el_commons']:.2f} [{R['H2']['el_commons_lo']:.2f}, {R['H2']['el_commons_hi']:.2f}] & place-venue & {R['H2']['n']:,}\\\\\n"
        f"H2: Facebook minus Commons elasticity & {R['H2']['diff']:.2f} [{R['H2']['diff_lo']:.2f}, {R['H2']['diff_hi']:.2f}] & place-venue & {R['H2']['n']:,}\\\\\n"
        f"H3: gap $\\times$ majority (per 10 points) & {ci(R['H3']['maj'])} & month & {R['H3']['maj']['n']:,}\\\\\n"
        f"H3: gap $\\times$ marginal ($<$10 points) & {ci(R['H3']['marginal'])} & month & {R['H3']['marginal']['n']:,}\\\\\n"
        f"H4: gap $\\times$ frontbench & {ci(H['front'])} & month & {H['front']['n']:,}\\\\\n"
        f"H4: gap $\\times$ frontbench incl. whips & {ci(H['front_whip'])} & month & {H['front_whip']['n']:,}\\\\\n"
        f"H4: gap $\\times$ government side & {ci(H['gov'])} & month & {H['gov']['n']:,}\\\\\n"
        f"H4 (exploratory): frontbench, Commons only & {ci(H['front_commons'])} & month & {H['front_commons']['n']:,}\\\\\n"
        f"H4 (exploratory): frontbench, Facebook only & {ci(H['front_facebook'])} & month & {H['front_facebook']['n']:,}\\\\\n"
        f"H4 (exploratory): joint, frontbench & {ci(H['joint_front'])} & month & {H['joint_front']['n']:,}\\\\\n"
        f"H4 (exploratory): joint, government side & {ci(H['joint_gov'])} & month & {H['joint_gov']['n']:,}\\\\\n")
for k, lab in (("brexit", "Brexit months"), ("covid", "COVID months"), ("pre_ge", "two months before an election was called")):
    rows += f"H5 (exploratory): gap $\\times$ {lab} & {ci(R['H5'][k])} & month & {R['H5'][k]['n']:,}\\\\\n"
    rows += f"H5 (exploratory): {lab}, Facebook only & {ci(R['H5']['facebook_' + k])} & month & {R['H5']['facebook_' + k]['n']:,}\\\\\n"
    rows += f"H5 (exploratory): {lab}, Commons only & {ci(R['H5']['commons_' + k])} & month & {R['H5']['commons_' + k]['n']:,}\\\\\n"
TH = ("\\begin{table}[tbp]\\centering\\footnotesize\\caption{Planned tests of H2 to H5. H2 rows are coefficients on log population (PPML, spell-by-venue fixed effects, random-sample weights). "
      "Rows marked gap are ratios of the Facebook to Commons rate ratio; venue-only rows compare the period with the same MP's other months. Standard errors clustered by spell.}\\label{tab:het}"
      "\\begin{tabular}{llrr}\\toprule Term & Estimate [95\\% CI] & Unit & N\\\\\\midrule\n" + rows.replace("&  ", "& ").replace("H2: population", "H2: population") + "\\bottomrule\\end{tabular}\\end{table}")
# fix 4-column rows (label, estimate, unit, N)
TH = TH.replace("\\begin{tabular}{llrr}", "\\begin{tabular}{p{7.2cm}lrr}")
rows = "".join(f"{tex(v['label'])} & {ci(v)} & {v['n']:,} & {v['spells']}\\\\\n" for v in R["robust"].values())
TR = ("\\begin{table}[tbp]\\centering\\small\\caption{Robustness: the Facebook to Commons rate ratio under each check (95\\% CI).}\\label{tab:robust}"
      "\\begin{tabular}{lrrr}\\toprule Check & Rate ratio [95\\% CI] & N & Spells\\\\\\midrule\n"
      f"Main estimate & {ci(R['H1'])} & {R['H1']['n']:,} & {R['H1']['spells']}\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = "".join(f"{tex(k)} & {v['n']} & {v['fb']:.1f} & {v['cm']:.1f}\\\\\n" for k, v in R["by_nation"].items())
TA = ("\\begin{table}[htbp]\\centering\\small\\caption{Median own-seat place mentions per 100 items by nation, MPs with at least 20 items in each venue (descriptive).}\\label{tab:appx}"
      "\\begin{tabular}{lrrr}\\toprule Nation & MPs & Facebook & Commons\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
t = open(f"{ROOT}/code/paper_template.tex", encoding="utf-8").read()
t = t.replace("{{TABLE_SAMPLE}}", TS).replace("{{TABLE_MAIN}}", TM).replace("{{TABLE_HET}}", TH).replace("{{TABLE_ROBUST}}", TR).replace("{{TABLE_APPX}}", TA)
t = t.replace("{{AI}}", AI)
doi = os.environ.get("DOI")
t = re.sub(r"\{\{([^{}|]+)(\|(\w+))?\}\}", lambda m: m.group(0) if m.group(1) in ("DOI", "DOI_URL", "BLOG_URL")
           else fmt(get(R, m.group(1)), m.group(3)).replace("%", "\\%"), t)
t_out = t.replace("https://doi.org/10.5281/zenodo.24105795", f"https://doi.org/{doi}" if doi else "\\{\\{DOI\\_URL\\}\\}")
assert "{{" not in t_out.replace("\\{\\{DOI\\_URL\\}\\}", "")
for bad in ("—", "–", "D" "SIT", "D" "CMS"):
    assert bad not in t_out, bad
os.makedirs(OUT, exist_ok=True)
open(f"{OUT}/{NAME}.tex", "w", encoding="utf-8").write(t_out)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", f"{NAME}.tex"], cwd=OUT, capture_output=True, text=True)
log = open(f"{OUT}/{NAME}.log", encoding="utf-8", errors="ignore").read()
print("undefined refs:", log.count("undefined"), "| pages:", re.findall(r"Output written on .*?\((\d+) pages", log))
for e in ("aux", "log", "out"):
    p = f"{OUT}/{NAME}.{e}"
    if os.path.exists(p): os.remove(p)
txt = subprocess.run(["pdftotext", f"{OUT}/{NAME}.pdf", "-"], capture_output=True, text=True).stdout
body = txt.split("References")[0] if "References" in txt else txt
print("words (whole pdf):", len(txt.split()), "| before references:", len(body.split()))
ab = re.search(r"Abstract(.*?)Keywords", txt, re.S)
print("abstract words:", len(ab.group(1).split()) if ab else None)
