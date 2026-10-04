import json, random, datetime
from itertools import product
rules=json.load(open('src/content/rules.json')); season=json.load(open('src/content/season.json'))
LABELS=["healthy","rust","cercospora","phoma","miner","not_leaf"]; WINDOWS=["pre_short_rains","short_rains","pre_long_rains","long_rains","dry"]
def matches(c,s):
    for k,v in c.items():
        if k=="dominant" and s["dominant"]!=v: return False
        if k=="affected_gte" and not s["affected"]>=v: return False
        if k=="affected_lte" and not s["affected"]<=v: return False
        if k=="uncertain_gte" and not s["uncertain"]>=v: return False
        if k=="distinct_problems_gte" and not s["distinct"]>=v: return False
        if k=="window" and s["window"]!=v: return False
    return True
def decide(s):
    for r in rules:
        if matches(r.get("if",{}),s): return r.get("then","ask_officer")
    return "ask_officer"
matrix=[]
for d,a,u,di,w in product(LABELS+["none"],range(11),range(11),(1,2,3),WINDOWS):
    if a+u>10: continue
    if d in("healthy","none") and a>0: continue
    if d not in("healthy","none") and a==0: continue
    if di>max(1,a): continue
    s=dict(dominant=d,affected=a,uncertain=u,distinct=di,window=w); matrix.append([d,a,u,di,w,decide(s)])
# independent summarise reference (written from CONTRACTS.md text)
def summ(labels):
    n=len(labels); counts={l:0 for l in LABELS}; uns=0
    for x in labels:
        if x=="unsure": uns+=1
        else: counts[x]+=1
    D=["rust","cercospora","phoma","miner"]
    aff=sum(counts[d] for d in D); distinct=sum(1 for d in D if counts[d]>0); unc=uns+counts["not_leaf"]
    if counts["not_leaf"]>n/2: dom="not_leaf"
    elif aff>=1:
        mx=max(counts[d] for d in D); dom=[d for d in D if counts[d]==mx][0]
    elif counts["healthy"]>0: dom="healthy"
    else: dom="none"
    return dict(n=n,counts=counts,uncertain=unc,dominant=dom,affected=aff,distinctProblems=distinct)
random.seed(7); cases=[]
for i in range(3000):
    n=random.randint(1,12); pool=LABELS+["unsure"]
    w=[random.random() for _ in pool]
    labels=random.choices(pool,weights=w,k=n); cases.append([labels,summ(labels)])
# season windows reference for every day of 2026 (first match wins)
def win(dt):
    x=dt.month*100+dt.day
    for w in season["windows"]:
        s=w["start_month"]*100+w["start_day"]; e=w["end_month"]*100+w["end_day"]
        hit=(x>=s or x<=e) if (w.get("wraps_year") or s>e) else (s<=x<=e)
        if hit: return w["name"]
    return None
days=[]; d0=datetime.date(2026,1,1)
for k in range(365):
    dt=d0+datetime.timedelta(days=k); days.append([dt.isoformat(),win(dt)])
json.dump(dict(matrix=matrix,cases=cases,days=days),open('test/ref.json','w'))
print(len(matrix),len(cases),len(days), sum(1 for d in days if d[1] is None),'uncovered days')
