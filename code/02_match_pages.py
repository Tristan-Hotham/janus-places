"""Match each CrowdTangle page (page name / user name only, never post text) to a Commons member."""
import json, re, sys, unicodedata, pandas as pd
ST = '/home/claude/studies/janus-places/'
pages = pd.read_csv('/home/claude/studies/janus-places/data/pages_raw.csv', dtype=str)
mem = pd.read_csv(ST + 'data/commons_memberships.csv', dtype=str)
ppl = json.load(open('/home/claude/scratch/janus-places/dl/people.json'))['persons']
alt = {}
for p in ppl:
    pid = p['id'].split('/')[-1]
    for n in p.get('other_names', []):
        alt.setdefault(pid, set()).add(f"{n.get('given_name','')} {n.get('family_name','')}")
def norm(s):
    s = unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode().lower()
    s = re.sub(r"\b(for|mp for|member for)\b.*$", '', s)
    s = re.sub(r"\b(rt\.? hon\.?|the|sir|dame|dr|doctor|lord|qc|mp|ms|mrs|mr|snp|dup|uup|as/mp|as|labour|official|watch|federal labor member)\b", ' ', s)
    s = re.sub(r"[^a-z ]", ' ', s)
    return ' '.join(s.split())
OVR = json.load(open(ST + 'code/page_overrides.json'))
names = {}
for pid, g in mem.groupby('person_id'):
    ks = {norm(f"{r.given} {r.family}") for r in g.itertuples()} | {norm(a) for a in alt.get(pid, [])}
    for k in ks:
        names.setdefault(k, set()).add(pid)
out = []
for r in pages.itertuples():
    o = OVR.get(r.fb_id)
    if o is not None:
        pid, how = o.get('person_id', ''), 'override: ' + o['why']
    else:
        k = norm(r.page_name.split(' | ')[0])
        c = names.get(k, set())
        pid, how = (next(iter(c)), 'name') if len(c) == 1 else ('', f'unmatched ({len(c)} candidates)')
    out.append(dict(fb_id=r.fb_id, page_name=r.page_name, user_name=r.user_name, n_posts=int(r.n_posts), first=r.first, last=r.last,
                    person_id=pid, match=how))
out = pd.DataFrame(out)
m1 = mem.drop_duplicates('person_id').set_index('person_id')
out['member_id'] = out.person_id.map(m1.member_id).fillna('')
out['mp_name'] = out.person_id.map(m1.given + ' ' + m1.family).fillna('')
out.to_csv(ST + 'data/pages.csv', index=False)
print(out.match.str.split(':').str[0].value_counts())
print(out[out.person_id == ''][['fb_id', 'page_name', 'user_name', 'n_posts', 'match']].to_string())
