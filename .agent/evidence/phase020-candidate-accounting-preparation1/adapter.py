"""Future released accounting adapter. Current preparation is deliberately unbound.

No implicit inventory discovery, attribution, generated exclusion or budget verdict.
Invoke only after Root releases exact END/heads and independent closure approval.
"""
import argparse,gzip,hashlib,json,runpy,subprocess
from pathlib import Path
PINS={'.agent/evidence/scope-budget-014/measure.py':'3d40a57b5200d7cd00f3fdfbc2cb348b87e9523669d1b9d2682419ca526d9973','.agent/evidence/133/root-final-scope1.py':'a93677bc96c02f48082b1739a19bc715c60e5e0f19de726892dcb10f251e29b8','.agent/evidence/133/delivery-supplement1/measure-v2.py':'6080ad601b9afadf187e85eebe759c63b60db7d056eff12a3008717230a160a4'}
def sha(raw):return hashlib.sha256(raw).hexdigest()
def git(*args):return subprocess.check_output(['git',*args])
def read(ref):
 raw=git('show',ref['revision']+':'+ref['path']);assert sha(raw)==ref['sha256'];return raw
def load(raw):return json.loads(gzip.decompress(raw) if raw[:2]==b'\x1f\x8b' else raw)
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--release',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
 # Release file is a retained Root-authored Git reference, not a mutable local inventory assertion.
 release_ref=json.loads(args.release.read_bytes());release=json.loads(read(release_ref))
 assert release['role']=='Root' and release['accounting_authorized'] is True
 cfg_raw=read(release['inventory']);cfg=load(cfg_raw)
 assert cfg['status']=='closed-and-independently-reviewed' and not cfg['pending']
 end=release['endpoint'];heads=release['heads'];assert end==cfg['endpoint'] and heads==cfg['heads'] and len(end)==40
 assert sha(Path(__file__).read_bytes())==release['adapter_sha256']
 assert git('rev-parse','HEAD').decode().strip()==end and not git('status','--porcelain','--untracked-files=all')
 assert git('show',end+':'+str(Path(__file__).resolve().relative_to(Path.cwd())))==Path(__file__).read_bytes()
 review=json.loads(read(release['closure_review']));assert review['final_verdict']['approved'] is True
 assert all(review[k]==[] for k in ('issues','missing_acceptance_coverage','unsupported_claims')) and review['inventory_sha256']==sha(cfg_raw)
 assert release['preservation_capture_required'] is True and release['installed_expected']==239
 assert git('remote','get-url','origin').decode().strip()=='https://github.com/niq-cnr/nizam-framework.git'
 out=args.output.resolve();assert Path.cwd().resolve() not in (out,*out.parents) and not out.exists()
 for p,pin in PINS.items():assert sha(Path(p).read_bytes())==pin
 frozen=runpy.run_path('.agent/evidence/scope-budget-014/measure.py');helper=runpy.run_path('.agent/evidence/133/root-final-scope1.py');v2=runpy.run_path('.agent/evidence/133/delivery-supplement1/measure-v2.py')
 # Reuse exact parsing/classification/block semantics; do not invoke historical mains or133 totals/ranges.
 classify,authored,records,allocate=frozen['classify'],helper['authored'],helper['records'],v2['allocate_blocks']
 actual_commits=set(git('rev-list',*heads,'^'+cfg['history_floor']).decode().split())
 assert actual_commits==set(cfg['commits']) and set(cfg['merge_proofs'])==set(git('rev-list','--min-parents=2',*heads,'^'+cfg['history_floor']).decode().split())
 for proof in cfg['merge_proofs'].values():assert proof['reviewed'] is True
 actual_events=set()
 for commit in actual_commits-set(cfg['merge_proofs']):
  parent=git('rev-parse',commit+'^').decode().strip()
  for name in git('diff','--name-only','--no-renames','-z',parent,commit).split(b'\0'):
   if name:actual_events.add(commit+':'+name.decode())
 assert actual_events==set(cfg['event_keys'])=={e['key'] for e in cfg['chronological']}
 assert {p.decode() for p in git('diff','--name-only','--no-renames','-z',cfg['history_floor'],end).split(b'\0') if p}=={e['path'] for e in cfg['snapshot']}
 assert cfg['inherited_product_test_baseline_proofs']
 totals={view:{'product':0,'independent_tests':0,'process':0} for view in ('snapshot','chronological')};features={view:{} for view in totals};rows=[];binary=[]
 def record(view,e):
  assert e['disposition'] in ('charge-authored','excluded-state','derived-observation','proven-copy','foreign')
  parent,rev,path=e['parent'],e['commit'],e['path'];before=v2['blob'](parent,path);after=v2['blob'](rev,path)
  assert (None if before is None else sha(before))==e['before_sha256'] and (None if after is None else sha(after))==e['after_sha256']
  frozen_category=classify(path);assert frozen_category!='unclassified'
  if path=='.agent/run_state.json':assert e['disposition']=='excluded-state'
  if e['disposition']!='charge-authored':
   assert e['proof'] and (e['disposition']!='proven-copy' or e['canonical_event'] in cfg['event_keys'])
   rows.append(dict(view=view,event=e['key'],disposition=e['disposition'],proof=e['proof']));return
  assert e['owner']=='020' and e['category'] in totals[view]
  data=after if after is not None else before
  kind=authored(path,data) if frozen_category=='evidence' else frozen_category
  assert kind is not None or e.get('reviewed_authored_override')
  raw=git('diff','--numstat','--no-renames','-z',parent,rev,'--',path)
  values=list(records(raw));assert len(values)==1 and values[0][0]==path
  amount=values[0][1];is_binary=any(x.split(b'\t',1)[0]==b'-' for x in raw.split(b'\0') if x)
  if is_binary:binary.append(dict(view=view,event=e['key'],before=e['before_sha256'],after=e['after_sha256']))
  if e.get('split_blocks'):
   amounts=allocate(parent,rev,path,e['split_blocks']);amount=amounts.get('020',0)
  if e.get('split_lines'):
   assert not e.get('split_blocks')
   patch=git('-c','color.ui=false','diff','--no-ext-diff','--no-textconv','--no-renames','--unified=0',parent,rev,'--',path).decode().splitlines()
   changed=[s for s in patch if s[:1] in ('+','-') and not s.startswith(('+++ ','--- '))]
   assert [sha(s.encode()) for s in changed]==[s['signed_line_sha256'] for s in e['split_lines']] and len(changed)==amount
   assert all(s['owner'] in ('020','foreign') for s in e['split_lines'])
   amount=sum(s['owner']=='020' for s in e['split_lines'])
  totals[view][e['category']]+=amount;feature=e['feature'] or 'other020';features[view][feature]=features[view].get(feature,0)+amount
  rows.append(dict(view=view,event=e['key'],category=e['category'],feature=feature,amount=amount,binary=is_binary,before=e['before_sha256'],after=e['after_sha256']))
 # Snapshot records bind per-path inherited baseline explicitly; never infer latest event ownership for a whole shared file.
 for e in cfg['chronological']:record('chronological',e)
 for e in cfg['snapshot']:record('snapshot',e)
 phase={v:sum(totals[v].values()) for v in totals}
 report={'endpoint':end,'heads':heads,'inventory_sha256':sha(cfg_raw),'category_views':totals,'feature_views':features,'phase_views':phase,'phase_conservative':max(phase.values()),'binary_inventory':binary,'rows':rows,'later_work':cfg['later_work'],'limitation':'Checkpoint only; no budget verdict, allowance or projected zero for laterQA/admin. Phase/feature and snapshot/chronological views overlap and are never added.'}
 out.write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
