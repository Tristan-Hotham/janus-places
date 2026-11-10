"""Each 2010-boundary seat's list of place names, with ambiguity flags.
Inputs: Wikidata UK settlements (raw_new8/uk_settlements.tsv, CC0), hansard-places places.csv and ambiguous_names.csv,
GB seats 2010 (twins-remain/data/seats.geojson), NI seats (martinjc/UK-GeoJSON json/electoral/ni/wpc.json, scratch copy)."""
import json, re, sys, unicodedata, pandas as pd, numpy as np
from shapely.geometry import shape, Point
from shapely.strtree import STRtree
sys.path.insert(0, '/home/claude/scratch/janus-places/pylib')
from wordfreq import zipf_frequency
ST = '/home/claude/studies/janus-places/'
SET = '/home/claude/newdata/raw_new8/uk_settlements.tsv'
HP = '/home/claude/src6/hansard-places/data/'
KEEP = {'Village', 'hamlet', 'human settlement', 'suburb', 'town', 'market town', 'locality', 'area of London', 'neighborhood',
        'city', 'big city', 'city of the United Kingdom', 'town of the United Kingdom', 'village', 'urban area', 'district',
        'civil parish', 'community', 'seaside resort', 'cathedral city', 'new town', 'port settlement', 'unparished area',
        'county town', 'mining community', 'planned community', 'ward', 'settlement', 'island', 'post town'}
# --- seats
feats = []
for f in json.load(open('/home/claude/studies/twins-remain/data/seats.geojson'))['features']:
    nm = f['properties']['seat']; feats.append(('Ynys Môn' if nm == 'Ynys Mon' else nm, shape(f['geometry'])))
mem = pd.read_csv(ST + 'data/commons_memberships.csv')
ni = {s.upper(): s for s in mem.seat.unique()}
for f in json.load(open('/home/claude/scratch/janus-places/dl/ni_wpc.json'))['features']:
    feats.append((ni[f['properties']['PC_NAME']], shape(f['geometry'])))
geoms = [g for _, g in feats]; tree = STRtree(geoms)
def seat_of(lon, lat):
    p = Point(lon, lat)
    for i in tree.query(p):
        if geoms[i].contains(p): return feats[i][0]
    return None
# --- settlements
s = pd.read_csv(SET, sep='\t', dtype=str)
s.columns = ['qid', 'name', 'coord', 'pop', 'type']
s['type'] = s['type'].str.replace(r'^"|"@en$|@en$', '', regex=True).str.strip('"')
print('types kept:', s['type'].isin(KEEP).sum(), 'of', len(s))
s = s[s['type'].isin(KEEP)].copy()
s['name'] = s['name'].str.replace(r'@[a-z-]+$', '', regex=True).str.strip('"')
xy = s['coord'].str.extract(r'POINT\(([-0-9.e]+) ([-0-9.e]+)\)').astype(float)
s['lon'], s['lat'] = xy[0], xy[1]
s['pop'] = pd.to_numeric(s['pop'], errors='coerce')
s['qid'] = s['qid'].str.extract(r'(Q\d+)')[0]
s = s.dropna(subset=['lon', 'lat'])
hp = pd.read_csv(HP + 'places.csv')
hp = hp.rename(columns={'term': 'name'})[['name', 'lat', 'lon', 'pop']].assign(type='hansard-places', qid='')
s = pd.concat([s[['qid', 'name', 'type', 'lon', 'lat', 'pop']], hp], ignore_index=True)
s['name'] = s['name'].str.split(',').str[0].str.replace(r'\s*\(.*\)$', '', regex=True).str.strip()
s = s[s['name'].str.len() >= 3]
s['seat'] = [seat_of(a, b) for a, b in zip(s.lon, s.lat)]
s = s.dropna(subset=['seat'])
# --- seat-name components
DIRS = sorted(['north', 'south', 'east', 'west', 'central', 'mid', 'outer', 'inner', 'city of', 'the', 'upper', 'north east',
               'north west', 'south east', 'south west', 'mid and south', 'east and north'], key=len, reverse=True)
PRE = re.compile(r'^(' + '|'.join(DIRS) + r')\s+', re.I)
SUF = re.compile(r'\s+(' + '|'.join(DIRS) + r')$', re.I)
known = set(s['name'])
# components naming a county, region or a generic word rather than a place in the seat: kept in the file, never queried
AREA = {'Aberdeenshire', 'Antrim', 'Ayrshire', 'Bedfordshire', 'Berwickshire', 'Cambridgeshire', 'Cleveland', 'Clwyd', 'Cornwall',
        'Derbyshire', 'Devon', 'Dorset', 'Down', 'Dumfriesshire', 'Dunbartonshire', 'Essex', 'Fermanagh', 'Fife', 'Hampshire',
        'Herefordshire', 'Hertfordshire', 'Kent', 'Lancashire', 'Leicestershire', 'Lothian', 'Norfolk', 'Northamptonshire', 'Perthshire',
        'Renfrewshire', 'Shropshire', 'Somerset', 'Staffordshire', 'Suffolk', 'Surrey', 'Sussex', 'Tyrone', 'Ulster', 'Warwickshire',
        'Wiltshire', 'Worcestershire', 'Yorkshire', 'Border', 'Test', 'Riverside', 'Pavilion', 'Westminster', 'Cities of London',
        'Wirral', 'Tyneside', 'Galloway', 'Lancashire', 'Durham' if False else '', 'Angus' if False else ''}
AREA.discard('')
def comps(seat):
    out = set()
    for part in re.split(r',| and | & ', re.sub(r'\s*\(.*\)', '', seat)):
        p = part.strip()
        p2 = PRE.sub('', SUF.sub('', p)).strip()
        if p.lower().startswith('isle of'): p2 = p
        cands = [SUF.sub('', p).strip(), p, p2]
        hits = [c for c in cands if c in known]
        q = hits[0] if hits else p2
        for c in (hits[:1] or [p2]):
            if len(c) >= 3 and c.lower() not in {'and', 'the'}: out.add(c)
        m = re.match(r'(.+?)(?: upon |-on-| on )(.+)', q)
        if m: out.add('Hull' if m.group(1) == 'Kingston' and m.group(2) == 'Hull' else m.group(1).strip())
    return out
rows = []
for seat in sorted({n for n, _ in feats}):
    for c in comps(seat):
        rows.append(dict(seat=seat, name=c, qid='', type='seat-name component', lon=np.nan, lat=np.nan, pop=np.nan))
s = pd.concat([s, pd.DataFrame(rows)], ignore_index=True)
s['from_seat_name'] = s.type.eq('seat-name component')
# settlement records named like a county or nation (Somerset in Wells, Wales in Rother Valley, London) are not seat places either
NOTPLACE = AREA | {'London', 'England', 'Scotland', 'Wales', 'Britain', 'Anglesey', 'Weald', 'Westminster'}
s['area_term'] = (s.from_seat_name & s.name.isin(AREA)) | (~s.from_seat_name & s.name.isin(NOTPLACE))
g = (s.sort_values('pop', ascending=False)
       .groupby(['seat', 'name'], as_index=False)
       .agg(qid=('qid', 'first'), type=('type', 'first'), lon=('lon', 'first'), lat=('lat', 'first'), pop=('pop', 'max'),
            from_seat_name=('from_seat_name', 'max'), area_term=('area_term', 'max'), n_records=('name', 'size')))
# --- flags
amb = pd.read_csv(HP + 'ambiguous_names.csv').fillna('')
hpf = {r.term: (r.flag or r.any_flag) for r in amb.itertuples()}
hpp = {r.term: float(r.precision_factor or 1) for r in amb.itertuples()}
hpset = set(hp.name)
g['hp_flag'] = g.name.map(hpf).fillna('')
g['hp_precision'] = g.name.map(hpp)
g['zipf'] = [round(zipf_frequency(n.lower(), 'en'), 2) for n in g.name]
# common word: hansard-places hand flags where the place is in that list; otherwise lower-case word frequency (zipf >= 4)
g['common_word'] = np.where(g.name.isin(hpset), g.hp_flag.isin(['word']) | (g.hp_flag.eq('other') & (g.hp_precision < 0.95)),
                            g.zipf >= 4.0)
g['namesake'] = g.hp_flag.isin(['namesake'])
g['surname'] = g.hp_flag.eq('surname')
g['n_seats_with_name'] = g.name.map(g.groupby('name').seat.nunique())
g['shared'] = g.n_seats_with_name > 1
# a same-named settlement in a seat that does not carry the name, and bigger than this one (components: >= 5,000 people)
rec = g[~g.from_seat_name][['name', 'seat', 'pop']]
comp_pairs = set(zip(g[g.from_seat_name].name, g[g.from_seat_name].seat))
comp_names = g[g.from_seat_name].groupby('name').seat.apply(set).to_dict()
# records of each name lying in seats that do not carry the name
rec = rec[[s not in comp_names.get(n, set()) for n, s in zip(rec.name, rec.seat)]]
by = {n: list(zip(x.seat, x['pop'])) for n, x in rec.groupby('name')}
own_pop = g[[s in comp_names.get(n, set()) for n, s in zip(g.name, g.seat)]].groupby('name')['pop'].max().fillna(0).to_dict()
def bigger_elsewhere(name, seat, pop, comp):
    o = [(s, p) for s, p in by.get(name, []) if s != seat]
    if not o: return False
    if comp:
        own = own_pop.get(name, 0)
        return any(p == p and p >= max(5000, 0.1 * own) for _, p in o)
    if pop != pop: return any(p == p for _, p in o)
    return any(p == p and p > pop for _, p in o)
g['larger_elsewhere'] = [bool(sh) and bigger_elsewhere(n, s, p, c) for n, s, p, c, sh in zip(g.name, g.seat, g['pop'], g.from_seat_name, g.shared)]
g['ambiguous'] = g.common_word | g.namesake | g.larger_elsewhere | g.hp_flag.eq('shared')
g['why_flag'] = [';'.join(k for k, v in [('common word', c), ('namesake abroad', n), ('bigger namesake elsewhere', l), ('shared (hansard-places)', h == 'shared')] if v)
                  for c, n, l, h in zip(g.common_word, g.namesake, g.larger_elsewhere, g.hp_flag)]
g = g.sort_values(['seat', 'pop'], ascending=[True, False])
g['rank_in_seat'] = g.groupby('seat')['pop'].rank(ascending=False, method='first')
g.drop(columns=['n_records']).to_csv(ST + 'data/seat_places.csv', index=False)
print(len(g), g.seat.nunique(), g.groupby('seat').size().describe().round(1).to_dict())
print(g[['common_word', 'shared', 'larger_elsewhere', 'surname', 'ambiguous']].sum().to_dict())
