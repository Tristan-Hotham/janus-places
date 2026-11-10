import pandas as pd, sys
f='/mnt/user-data/uploads/l/crowdtangle data/2020-10-28-15-42-17-GMT-Historical-Report-UK---MPs-2010-01-01--2020-10-29.csv'
agg={}
n=0
for c in pd.read_csv(f,usecols=['Page Name','User Name','Facebook Id','Created','Likes at Posting'],chunksize=100000,dtype=str):
    n+=len(c)
    c['m']=c['Created'].str[:7]
    for fid,g in c.groupby('Facebook Id'):
        a=agg.setdefault(fid,{'names':set(),'users':set(),'n':0,'first':'9999','last':'0000','likes':None})
        a['names'].update(g['Page Name'].dropna()); a['users'].update(g['User Name'].dropna())
        a['n']+=len(g); a['first']=min(a['first'],g['m'].min()); a['last']=max(a['last'],g['m'].max())
        if a['likes'] is None: a['likes']=g['Likes at Posting'].iloc[0]
rows=[{'fb_id':k,'page_name':' | '.join(sorted(v['names'])),'user_name':' | '.join(sorted(v['users'])),'n_posts':v['n'],'first':v['first'],'last':v['last'],'likes_last':v['likes']} for k,v in agg.items()]
pd.DataFrame(rows).sort_values('n_posts',ascending=False).to_csv('/home/claude/studies/janus-places/data/pages_raw.csv',index=False)
print(n,len(rows))
