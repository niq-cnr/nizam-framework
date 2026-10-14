"""Independent bounded factual rereview2; prior receipt proof reused by identity."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import yaml
import jsonschema

CANDIDATE = '5be6c60b1f19689a19f7f951e1834cfdc11d7853'
PREVIOUS = 'e36aa45a2d603836e5b2fe1c358791ddcc25bfc6'
HISTORY = '58bc675c5ee4e845f8069893f08a77bd52002a78'
ROOT = '1debbe16659b589d161376e899e4c0cd9b84cf63'
def git(*args):
    return subprocess.check_output(['git', *args])
def sha(b):
    return hashlib.sha256(b).hexdigest()
def load(path):
    return json.loads(Path(path).read_bytes())
assert git('rev-parse','HEAD').decode().strip() == CANDIDATE
report = {'candidate':CANDIDATE,'prior_candidate':PREVIOUS,'historical_base':HISTORY,'root_contract_revision':ROOT,'documents':{}}
prior = load('.agent/evidence/127/public-projection-review-checks.stdout.txt')
for path in ['docs/planning/ROADMAP.md','docs/planning/HANDOVER.md']:
    data = Path(path).read_bytes(); old = git('show',HISTORY+':'+path)
    metadata,body = data.split(b'---\n',2)[1:]; oldmetadata,oldbody = old.split(b'---\n',2)[1:]
    meta = yaml.safe_load(metadata); before = yaml.safe_load(oldmetadata)
    jsonschema.validate(meta,load('.nizam/schema/frontmatter.schema.json'))
    assert meta['change_log'][0]['version'] == meta['version'] and meta['change_log'][0]['date'] == '2026-10-14'
    assert meta['version'] == prior['documents'][path]['version']
    assert meta['change_log'][1:] == before['change_log']
    assert metadata == git('show',PREVIOUS+':'+path).split(b'---\n',2)[1]
    title,suffix=oldbody.split(b'\n\n',1)
    assert body.startswith(title+b'\n\n') and body.endswith(suffix)
    assert sha(suffix) == prior['documents'][path]['historical_suffix_sha256']
    overlay=body[len(title)+2:-len(suffix)].decode()
    assert len(overlay.splitlines()) == 14
    assert 'historical snapshots' in overlay and 'contract attempt 1 preparation only' not in overlay
    assert 'its current gate/status follows [Root state]' in overlay
    assert '128 remains pending' in overlay
    links = re.findall(r'\]\(([^)]+)\)',overlay)
    assert all((Path(path).parent/link).resolve().is_file() for link in links)
    assert '1/2/3/8 (policy)/9/13' in overlay and 'full adapter and SBCL acceptance remain pending' in overlay
    assert 'unmeasured' in overlay and 'no superiority claim' in overlay
    assert '3,003/7,345' in overlay and '5,203/7,020' in overlay and '127 only' in overlay
    report['documents'][path]={'sha256':sha(data),'version':meta['version'],'overlay_lines':14,'historical_suffix_sha256':sha(suffix),'resolved_link_count':len(links)}
numstat=git('diff','--numstat','c2b95a1',CANDIDATE,'--',*report['documents']).decode()
assert sum(sum(map(int,line.split()[:2])) for line in numstat.splitlines()) == 38
report['counted_document_lines']=38
# These exact artifacts supplied the independent review1 factual/receipt proof.
# Verify unchanged committed bytes, then reuse that proof rather than rerun product acceptance.
reuse_paths=['.agent/evidence/126','.agent/qa/126.json','.agent/feature_list_016.json','.agent/feature_list_018.json','.agent/feature_list_019.json','.agent/feature_list_020.json','docs/planning/phase_016.yaml','docs/planning/agentic-excellence.md','.nizam','tools/runtime_session.py','tools/test_runtime_session.py','tools/fixtures/runtime_session/stub_runtime.py']
assert not git('diff','--name-only',PREVIOUS,CANDIDATE,'--',*reuse_paths).strip()
assert not git('diff','--name-only','b56d677a736629fb8441aa065dc40b7a288f7d33',CANDIDATE,'--','.agent/evidence/127/public-projection-review*').strip()
report['reused_factual_proof']={'path':'.agent/evidence/127/public-projection-review-checks.stdout.txt','sha256':sha(Path('.agent/evidence/127/public-projection-review-checks.stdout.txt').read_bytes()),'verified_unchanged_inputs':reuse_paths,'scope':'126 partial stub receipts/795-line sealed test/C3/QA9 plus own adversarial/hostedCI9/PR97 six checks/main five jobs, budget snapshots, DAG and unmeasured proposal.'}
contract = json.loads(git('show',ROOT+':.agent/contracts/127.json'))
assert contract['status'] == 'approved'
red = contract['acceptance_ownership']['red']
assert 'Before substantive repair' in red and 'A reviewed executable initial candidate may precede' in red
assert 'missing API' in red and 'is not semantic red' in red
handover=Path('docs/planning/HANDOVER.md').read_text()
line=next((i,s) for i,s in enumerate(handover.splitlines(),1) if s.startswith('Required order:'))
assert 'intended semantic red before source work' in line[1]
report['procedural_finding']={'path':'docs/planning/HANDOVER.md:'+str(line[0]),'document_text':line[1],'approved_contract_sha256':sha(git('show',ROOT+':.agent/contracts/127.json')),'approved_contract_red':red,'assessment':'Required order erroneously excludes the approved executable-initial-candidate route. Red is required before substantive repair; unsupported or missing API is not red. Correction needed, no document repairs made.'}
report['scope']='Documentation overlay review only; no feature127 implementation/gate approval, no lifecycle or Root state writes.'
print(json.dumps(report,indent=2))
