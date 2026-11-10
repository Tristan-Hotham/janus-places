"""Facebook: posts naming each of the MP's own seat's places, per MP-month. Aggregates only.
The CrowdTangle CSV is streamed in chunks from where it sits; post text, URLs and links are read in memory only and never written."""
import re, sys, json, unicodedata, collections, pandas as pd, numpy as np
ST = '/home/claude/studies/janus-places/'
CSV = '/mnt/user-data/uploads/l/crowdtangle data/2020-10-28-15-42-17-GMT-Historical-Report-UK---MPs-2010-01-01--2020-10-29.csv'
pages = pd.read_csv(ST + 'data/pages.csv', dtype=str).fillna('')
pages = pages[pages.person_id != '']
mem = pd.read_csv(ST + 'data/commons_memberships.csv', dtype=str)
mem = mem[mem.person_id.isin(pages.person_id)]
places = pd.read_csv(ST + 'data/seat_places.csv')
places = places[~places.area_term]
def phrase(r): return ('in ' + r.name) if r.ambiguous else r.name
places['phrase'] = [phrase(r) for r in places.itertuples()]
def norm(s):
    s = unicodedata.normalize('NFKC', s).replace('’', "'").replace('‘', "'")
    return s
def rx(ph):
    return r'(?<![\w])' + r'\s+'.join(re.escape(w) for w in norm(ph).split()) + r'(?![\w])'
seat_terms = {}
for seat, g in places.groupby('seat'):
    terms = sorted(set(g.phrase))
    seat_terms[seat] = (re.compile('|'.join(rx(t) for t in sorted(terms, key=len, reverse=True)), re.I),
                        [(t, re.compile(rx(t), re.I)) for t in terms])
# membership intervals per person, plus dissolution gaps when the same person returns for the same seat
iv = collections.defaultdict(list)
for pid, g in mem.groupby('person_id'):
    g = g.sort_values('start')
    rows = list(g.itertuples())
    for i, r in enumerate(rows):
        iv[pid].append((r.start, r.end, r.seat, 'sitting'))
        if i + 1 < len(rows) and rows[i + 1].seat == r.seat and r.end_reason == 'dissolution' and rows[i + 1].start > r.end:
            iv[pid].append((r.end, rows[i + 1].start, r.seat, 'campaign'))
fb2pid = dict(zip(pages.fb_id, pages.person_id))
def where(pid, day):
    for s, e, seat, per in iv[pid]:
        if s <= day <= e: return seat, per
    return None, None
mm = collections.Counter()      # (pid, month, seat, period) -> dict counters
tot = collections.defaultdict(lambda: collections.Counter())
cnt = collections.Counter()     # (pid, month, seat, period, phrase, field)
outside = collections.Counter()
for ch in pd.read_csv(CSV, usecols=['Facebook Id', 'Created', 'Message', 'Link Text', 'Description', 'Image Text'],
                      dtype=str, chunksize=50000):
    print("chunk", flush=True)
    ch = ch[ch['Facebook Id'].isin(fb2pid.keys())]
    for fid, created, msg, lt, de, it in zip(ch['Facebook Id'], ch['Created'], ch['Message'], ch['Link Text'], ch['Description'], ch['Image Text']):
        pid = fb2pid[fid]; day = created[:10]
        seat, per = where(pid, day)
        if seat is None:
            outside[pid] += 1; continue
        k = (pid, day[:7], seat, per)
        T = tot[k]; T['posts'] += 1
        msg = norm(msg) if isinstance(msg, str) else ''
        extra = ' \n '.join(norm(x) for x in (lt, de, it) if isinstance(x, str))
        if msg.strip(): T['posts_with_message'] += 1
        allt = msg + ' \n ' + extra
        big, singles = seat_terms[seat]
        if not big.search(allt): continue
        hit_m, hit_a = False, False
        for ph, r in singles:
            a = r.search(allt)
            if a:
                m = r.search(msg) is not None
                cnt[k + (ph, 'any')] += 1
                if m: cnt[k + (ph, 'message')] += 1; hit_m = True
                hit_a = True
        T['posts_naming_any_place_message'] += hit_m
        T['posts_naming_any_place_any_field'] += hit_a
rows = [dict(person_id=k[0], month=k[1], seat=k[2], period=k[3], **v) for k, v in tot.items()]
mo = pd.DataFrame(rows).fillna(0).sort_values(['person_id', 'month'])
mo.to_csv(ST + 'data/fb_mp_months.csv', index=False)
c = collections.defaultdict(dict)
for (pid, mon, seat, per, ph, fld), n in cnt.items():
    c[(pid, mon, seat, per, ph)][fld] = n
pr = pd.DataFrame([dict(person_id=k[0], month=k[1], seat=k[2], period=k[3], phrase=k[4], n_message=v.get('message', 0), n_any_field=v.get('any', 0))
                   for k, v in c.items()]).sort_values(['person_id', 'month', 'phrase'])
pr.to_csv(ST + 'data/fb_place_counts.csv', index=False)
json.dump({'posts_outside_membership': sum(outside.values()), 'by_person': dict(outside)}, open(ST + 'data/fb_outside.json', 'w'), indent=0)
print(len(mo), mo.posts.sum(), sum(outside.values()), len(pr), pr.n_message.sum())
