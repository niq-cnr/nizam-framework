"""Independent final bounded docs-only review, reusing identity-verified proofs."""
import hashlib,json,re,subprocess
from pathlib import Path
import yaml,jsonschema
CANDIDATE='d12b17629229200f8051728c24372df457aaa1bb'
PRIOR='5be6c60b1f19689a19f7f951e1834cfdc11d7853'
def git(*args): return subprocess.check_output(['git',*args])
def load(path): return json.loads(Path(path).read_bytes())
def sha(data): return hashlib.sha256(data).hexdigest()
assert git('rev-parse','HEAD').decode().strip()==CANDIDATE
proof=load('.agent/evidence/127/public-projection-review2-checks.stdout.txt')
reused=proof['reused_factual_proof']['verified_unchanged_inputs']
assert not git('diff','--name-only',PRIOR,CANDIDATE,'--',*reused).strip()
priorproofs=['.agent/evidence/127/public-projection-review.json','.agent/evidence/127/public-projection-review2.json','.agent/evidence/127/public-projection-review-checks.stdout.txt','.agent/evidence/127/public-projection-review2-checks.stdout.txt']
assert not git('diff','--name-only','3f8aaad5011d63d01288d8d34b5116d70b7d5f2b',CANDIDATE,'--',*priorproofs).strip()
assert load(priorproofs[0])['final_verdict']['approved'] is False and load(priorproofs[1])['final_verdict']['approved'] is False
assert Path('docs/planning/ROADMAP.md').read_bytes()==git('show',PRIOR+':docs/planning/ROADMAP.md')
report={'candidate':CANDIDATE,'previous_candidate':PRIOR,'documents':{},'reused_proof_paths':{p:sha(Path(p).read_bytes()) for p in priorproofs},'verified_unchanged_factual_inputs':reused}
for path in ['docs/planning/ROADMAP.md','docs/planning/HANDOVER.md']:
 data=Path(path).read_bytes();old=git('show','58bc675:'+path)
 fm,body=data.split(b'---\n',2)[1:];oldbody=old.split(b'---\n',2)[2]
 meta=yaml.safe_load(fm);jsonschema.validate(meta,load('.nizam/schema/frontmatter.schema.json'))
 assert fm==git('show',PRIOR+':'+path).split(b'---\n',2)[1]
 assert meta['version']==proof['documents'][path]['version']
 assert meta['change_log'][0]['version']==meta['version'] and meta['change_log'][0]['date']=='2026-10-14'
 title,suffix=oldbody.split(b'\n\n',1)
 assert body.startswith(title+b'\n\n') and body.endswith(suffix)
 assert sha(suffix)==proof['documents'][path]['historical_suffix_sha256']
 overlay=body[len(title)+2:-len(suffix)].decode()
 assert len(overlay.splitlines())==14 and 'historical snapshots' in overlay
 assert 'contract attempt 1 preparation only' not in overlay and 'its current gate/status follows [Root state]' in overlay
 assert 'intended semantic red before source work' not in overlay
 links=re.findall(r'\]\(([^)]+)\)',overlay)
 assert all((Path(path).parent/link).resolve().is_file() for link in links)
 report['documents'][path]={'sha256':sha(data),'version':meta['version'],'historical_suffix_sha256':sha(suffix),'overlay_lines':14,'resolved_links':len(links)}
old=git('show',PRIOR+':docs/planning/HANDOVER.md').decode().splitlines();new=Path('docs/planning/HANDOVER.md').read_text().splitlines()
changes=[(i+1,a,b) for i,(a,b) in enumerate(zip(old,new)) if a!=b]
assert len(old)==len(new) and len(changes)==1
assert changes[0][0]==69 and changes[0][1].startswith('Required order:')
assert changes[0][2]=='Follow the [approved127 contract](../../.agent/contracts/127.json) for the authoritative acceptance authoring, executable-candidate controls, implementation, QA, CI and capture gates.'
assert load('.agent/contracts/127.json')['status']=='approved'
assert not git('diff','--name-only','1debbe1',CANDIDATE,'--','.agent/contracts/127.json').strip()
numstat=git('diff','--numstat','c2b95a1',CANDIDATE,'--',*report['documents']).decode()
count=sum(sum(map(int,line.split()[:2])) for line in numstat.splitlines())
assert count==38
report['counted_document_lines']=count
report['known_findings']={'stale_attempt':'Resolved: stage-neutral selection scope and canonical Root state pointer.','red_order':'Resolved: HANDOVER:69 directly cites the existing approved contract, preserving its initial-candidate controls without restating or strengthening procedural order.'}
report['scope']='Approve only the two current documentation overlays/frontmatter at exact candidate; no feature127 implementation approval or gate/lifecycle advancement. Prior rejections retained. No documents, source, coordination, contracts, installed payload, requirements, budgets, historical phase records or acceptance evidence changed by reviewer.'
print(json.dumps(report,indent=2))
