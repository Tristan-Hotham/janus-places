"""Commons memberships overlapping the Facebook window, with Parliament member ids.
Source: mySociety parlparse members/people.json (GitHub), downloaded to scratch; only ids, names, seats, parties and dates are kept."""
import json, sys, pandas as pd
SRC = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/scratch/janus-places/dl/people.json'
OUT = '/home/claude/studies/janus-places/data/commons_memberships.csv'
W0, W1 = '2017-02-11', '2020-10-28'
d = json.load(open(SRC))
posts = {p['id']: p for p in d['posts']}
orgs = {o['id']: o.get('name', o['id']) for o in d['organizations']}
persons = {p['id']: p for p in d['persons']}
rows = []
for m in d['memberships']:
    p = posts.get(m.get('post_id'))
    if not p or p.get('organization_id') != 'house-of-commons':
        continue
    s, e = m.get('start_date', ''), m.get('end_date', '9999-12-31')
    if s > W1 or e < W0:
        continue
    per = persons[m['person_id']]
    ids = {i['scheme']: str(i['identifier']) for i in per.get('identifiers', [])}
    nm = m.get('name') or next((n for n in per.get('other_names', []) if n.get('note') == 'Main'), {})
    rows.append(dict(person_id=m['person_id'].split('/')[-1], member_id=ids.get('datadotparl_id', ''), wikidata=ids.get('wikidata', ''),
                     given=nm.get('given_name', ''), family=nm.get('family_name', ''), seat=p['area']['name'],
                     party=orgs.get(m.get('on_behalf_of_id'), m.get('on_behalf_of_id')), start=s, end=e,
                     start_reason=m.get('start_reason', ''), end_reason=m.get('end_reason', '')))
df = pd.DataFrame(rows).sort_values(['family', 'given', 'start'])
df.to_csv(OUT, index=False)
print(len(df), df.person_id.nunique(), (df.member_id == '').sum(), df.seat.nunique())
