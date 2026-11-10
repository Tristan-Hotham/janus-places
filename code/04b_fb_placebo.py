"""Facebook counts for the placebo phrases (places in another seat), which 04 did not search because it looks only for each
MP's own seat's places. Same rules: message field, case-insensitive whole-phrase match, posts on days the MP held the seat.
Writes data/fb_placebo_counts.csv (spell, month, query_id, n_message, n_any_field). Aggregates only."""
import collections, re, unicodedata, pandas as pd
from common import *

Q = pd.DataFrame(jload(f"{ROOT}/hansard_queries.json"))
Q = Q[Q.group.str.startswith("placebo")]
pages = pd.read_csv(f"{DATA}/pages.csv", dtype=str).dropna(subset=["person_id"])
fb2pid = dict(zip(pages.fb_id, pages.person_id))
mem = pd.read_csv(f"{DATA}/commons_memberships.csv", dtype=str)
iv = collections.defaultdict(list)
for r in mem.itertuples():
    iv[r.person_id].append((r.start, r.end, r.seat))
def norm_t(s): return unicodedata.normalize("NFKC", s).replace("’", "'").replace("‘", "'")
def rx(ph): return re.compile(r"(?<![\w])" + r"\s+".join(re.escape(w) for w in norm_t(ph).split()) + r"(?![\w])", re.I)
terms = collections.defaultdict(list)
for r in Q.itertuples():
    terms[(r.person_id, r.seat)].append((r.query_id, rx(r.phrase)))
cnt = collections.Counter()
for ch in pd.read_csv(CT_CSV, usecols=["Facebook Id", "Created", "Message", "Link Text", "Description", "Image Text"], dtype=str, chunksize=50000):
    ch = ch[ch["Facebook Id"].isin(fb2pid.keys())]
    for fid, created, msg, lt, de, it in zip(ch["Facebook Id"], ch["Created"], ch["Message"], ch["Link Text"], ch["Description"], ch["Image Text"]):
        pid = fb2pid[fid]; day = created[:10]
        seat = next((s for a, b, s in iv[pid] if a <= day <= b), None)
        if seat is None or (pid, seat) not in terms: continue
        msg = norm_t(msg) if isinstance(msg, str) else ""
        allt = msg + " \n " + " \n ".join(norm_t(x) for x in (lt, de, it) if isinstance(x, str))
        for qid, r in terms[(pid, seat)]:
            if r.search(allt):
                cnt[(pid + "|" + seat, day[:7], qid, "any")] += 1
                if r.search(msg): cnt[(pid + "|" + seat, day[:7], qid, "msg")] += 1
rows = collections.defaultdict(dict)
for (sp, m, q, f), n in cnt.items():
    rows[(sp, m, q)][f] = n
out = pd.DataFrame([dict(spell=k[0], month=k[1], query_id=k[2], n_message=v.get("msg", 0), n_any_field=v.get("any", 0)) for k, v in rows.items()],
                   columns=["spell", "month", "query_id", "n_message", "n_any_field"])
out.to_csv(f"{DATA}/fb_placebo_counts.csv", index=False)
print(len(out), out.n_message.sum() if len(out) else 0)
