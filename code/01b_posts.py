"""Government, opposition and parliamentary posts (data.parliament via mySociety parlparse ministers-2010.json) overlapping the Facebook window."""
import json, pandas as pd
ST = '/home/claude/studies/janus-places/'
d = json.load(open('/home/claude/scratch/janus-places/dl/ministers-2010.json'))['memberships']
mem = pd.read_csv(ST + 'data/commons_memberships.csv', dtype=str)
pids = set(mem.person_id)
rows = []
for a in d:
    if a.get('source') not in ('datadotparl/governmentpost', 'datadotparl/oppositionpost', 'datadotparl/parliamentarypost'): continue
    pid = a['person_id'].split('/')[-1]
    s, e = a.get('start_date', ''), a.get('end_date') or '9999-12-31'
    if pid not in pids or s > '2020-10-28' or e < '2017-02-11': continue
    rows.append(dict(person_id=pid, kind=a['source'].split('/')[-1], role=a.get('role', ''), start=s, end=e))
df = pd.DataFrame(rows).sort_values(['person_id', 'start'])
import re
def cat(k, r):
    if re.search(r'Whip|Lord Commissioner|Comptroller of HM Household|Treasurer of HM Household|Vice-Chamberlain', r): return 'whip'
    if k == 'governmentpost': return 'minister'
    if k == 'oppositionpost': return 'shadow'
    if re.match(r'(Leader of the (Labour|Conservative) Party|Leader of the Liberal Democrats|Leader of the SNP|.*Westminster Leader)', r): return 'party_leader'
    if 'Deputy Speaker' in r or r.startswith('Speaker'): return 'chair'
    return 'other'
df['category'] = [cat(k, r) for k, r in zip(df.kind, df.role)]
df = df[['person_id', 'kind', 'category', 'start', 'end']]   # role titles are not kept, only their category
df.to_csv(ST + 'data/frontbench_posts.csv', index=False)
print(len(df), df.person_id.nunique(), df.kind.value_counts().to_dict())
