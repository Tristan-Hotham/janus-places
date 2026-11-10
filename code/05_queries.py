"""Write hansard_queries.json: the fixed, pre-specified Commons query list (see NOTES.md)."""
import json, numpy as np, pandas as pd
ST = '/home/claude/studies/janus-places/'
W0, W1 = '2017-02-11', '2020-10-28'
rng = np.random.default_rng(2026)
pages = pd.read_csv(ST + 'data/pages.csv', dtype=str).dropna(subset=['person_id'])
mem = pd.read_csv(ST + 'data/commons_memberships.csv', dtype=str)
mem = mem[mem.person_id.isin(pages.person_id)]
pl = pd.read_csv(ST + 'data/seat_places.csv')
pl = pl[~pl.area_term].copy()
pl['phrase'] = np.where(pl.ambiguous, 'in ' + pl.name, pl.name)
fbc = pd.read_csv(ST + 'data/fb_place_counts.csv', dtype={'person_id': str})
fbc = fbc[fbc.period == 'sitting'].groupby(['person_id', 'seat', 'phrase']).n_message.sum().reset_index()
nation = {f['properties']['seat']: {'E': 'England', 'W': 'Wales', 'S': 'Scotland'}[f['properties']['code'][0]]
          for f in json.load(open('/home/claude/studies/twins-remain/data/seats.geojson'))['features']}
nation['Ynys Môn'] = nation.pop('Ynys Mon')
for s in set(mem.seat) - set(nation): nation[s] = 'Northern Ireland'
allseats = sorted(pl.seat.unique())
Q = []
def add(r, place, phrase, group, w=1.0):
    Q.append(dict(query_id=f'q{len(Q)+1:05d}', member_name=r['name'], member_id=r['member_id'], person_id=r['pid'], seat=r['seat'],
                  place=place, phrase=phrase, group=group, sample_weight=round(w, 3), start=r['start'], end=r['end']))
for (pid, seat), g in mem.groupby(['person_id', 'seat']):
    s, e = max(g.start.min(), W0), min(g.end.max(), W1)
    if s > e: continue
    r = dict(pid=pid, seat=seat, member_id=g.member_id.iloc[0], name=f"{g.given.iloc[-1]} {g.family.iloc[-1]}", start=s, end=e)
    add(r, '', '', 'total')
    sp = pl[pl.seat == seat].sort_values('pop', ascending=False)
    used = set()
    for x in sp[sp.from_seat_name].itertuples():
        if x.phrase not in used: add(r, x.name, x.phrase, 'seat'); used.add(x.phrase)
    rest = sp[~sp.from_seat_name & sp['pop'].notna() & ~sp.phrase.isin(used)]
    for x in rest.head(8).itertuples():
        if x.phrase not in used: add(r, x.name, x.phrase, 'pop'); used.add(x.phrase)
    pool = sp[~sp.phrase.isin(used)].drop_duplicates('phrase')
    k = min(5, len(pool))
    if k:
        w = len(pool) / k
        for i in rng.choice(len(pool), size=k, replace=False):
            x = pool.iloc[i]; add(r, x['name'], x.phrase, 'random', w); used.add(x.phrase)
    f = fbc[(fbc.person_id == pid) & (fbc.seat == seat) & ~fbc.phrase.isin(used) & (fbc.n_message > 0)].sort_values('n_message', ascending=False)
    for x in f.head(3).itertuples():
        add(r, pl[(pl.seat == seat) & (pl.phrase == x.phrase)].name.iloc[0], x.phrase, 'fb_top'); used.add(x.phrase)
    others = [t for t in allseats if t != seat and nation.get(t) == nation[seat]]
    own_names = set(sp.name)
    for _ in range(20):
        o = others[rng.integers(len(others))]
        c = pl[(pl.seat == o) & ~pl.ambiguous & ~pl.from_seat_name & pl['pop'].notna() & ~pl.name.isin(own_names) & ~pl.shared].sort_values('pop', ascending=False).head(2)
        if len(c) == 2: break
    for x in c.itertuples():
        add(r, x.name, x.phrase, 'placebo:' + o)
json.dump(Q, open(ST + 'hansard_queries.json', 'w'), ensure_ascii=False, indent=0)
q = pd.DataFrame(Q); q['g'] = q.group.str.split(':').str[0]
print(len(q), q.person_id.nunique(), q.g.value_counts().to_dict())
