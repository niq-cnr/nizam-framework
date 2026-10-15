"""Frozen fresh QA runner; invoke only after explicit Root strict Mode B release."""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import platform
import stat
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
E = ROOT / '.agent/evidence/122'
HIST = '8ac94f6808e8197111197c9acbf59b2aa92efc7c'
def sha(raw): return hashlib.sha256(raw).hexdigest()
def git(root, *args): return subprocess.check_output(['git', '-C', str(root), *args], stderr=subprocess.PIPE).decode().strip()
def write(name, value):
    path = E / ('qa1-' + name)
    assert not path.exists(), 'refuse to overwrite QA evidence: ' + str(path)
    path.write_text(json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n')
def inventory(root):
    rows = []
    for p in sorted(root.rglob('*')):
        rel = p.relative_to(root).as_posix()
        if rel == '.git' or rel.startswith('.git/') or rel.startswith('.agent/evidence/122/qa1-') or rel == '.agent/evidence/122-qa-adversarial.txt': continue
        s = p.lstat()
        value = os.readlink(p) if stat.S_ISLNK(s.st_mode) else sha(p.read_bytes()) if stat.S_ISREG(s.st_mode) else 'directory'
        rows.append([rel, s.st_mode, value])
    return rows
def aggregate(rows): return sha(json.dumps(rows, separators=(',', ':'), ensure_ascii=False).encode())
def pins(root):
    names = ['tools/workflow_assurance.py','tools/test_workflow_assurance.py','.agent/contracts/122.json','.agent/run_state.json','.nizam/NIZAM.json']
    return {name: {'sha256':sha((root/name).read_bytes()), 'mode':(root/name).lstat().st_mode, 'git':git(root,'ls-tree','HEAD','--',name)} for name in names}
def ordered_cases():
    values = {}
    def value(node):
        if isinstance(node, ast.Name): return values[node.id]
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add): return value(node.left) + value(node.right)
        return ast.literal_eval(node)
    for node in ast.parse((ROOT/'tools/test_workflow_assurance.py').read_text()).body:
        if isinstance(node, ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
            try: values[node.targets[0].id] = value(node.value)
            except (ValueError, KeyError, TypeError): pass
    return list(sum((values[k] for k in ('CASES','AGF_CASES','RECEIPT_CASES','LANE_CASES','FAILURE_CASES')), ()))
p = argparse.ArgumentParser()
for name in ('revision','mode-b','mode-b-revision','source-sha256','test-sha256','contract-sha256','historical-root'): p.add_argument('--'+name,required=True)
a = p.parse_args()
assert git(ROOT,'rev-parse','HEAD') == a.revision and len(a.revision)==40
mode_raw = subprocess.check_output(['git','-C',str(ROOT),'show',a.mode_b_revision+':'+a.mode_b])
assert mode_raw == (ROOT/a.mode_b).read_bytes()
mode = json.loads(mode_raw)
assert mode['final_verdict']['approved'] is True and all(mode[k] == [] for k in ('issues','missing_acceptance_coverage','unsupported_claims'))
for path, expected in [('tools/workflow_assurance.py',a.source_sha256),('tools/test_workflow_assurance.py',a.test_sha256),('.agent/contracts/122.json',a.contract_sha256)]: assert sha((ROOT/path).read_bytes()) == expected
historical = Path(a.historical_root).resolve()
assert historical != ROOT and git(historical,'rev-parse','HEAD') == HIST
expected = ordered_cases()
assert len(expected)==46 and len(set(expected))==46
before = inventory(ROOT)
assert sum(row[0].startswith('.nizam/') and stat.S_ISREG(row[1]) for row in before)==239
before_hist = inventory(historical)
index = E/'qa1-protected-index.jsonl'
assert not index.exists()
index.write_text(''.join(json.dumps(row,separators=(',',':'),ensure_ascii=False)+'\n' for row in before))
env = {'PATH':os.environ['PATH'],'HOME':os.environ['HOME'],'LANG':'C.UTF-8','LC_ALL':'C','PYTHONDONTWRITEBYTECODE':'1'}
write('before.json', {'revision':a.revision,'protected_count':len(before),'protected_aggregate':aggregate(before),'historical_aggregate':aggregate(before_hist),'pins':pins(ROOT),'mode_b':{'path':a.mode_b,'revision':a.mode_b_revision,'sha256':sha(mode_raw)},'environment':env,'python':platform.python_version(),'git':git(ROOT,'--version'),'expected_default_order':expected})
selectors = ['infrastructure-failed','semantic-failed','reject-cause-relabel','counter-continuity']
commands = [(name,ROOT,['python3','tools/test_workflow_assurance.py','--case',name],0) for name in selectors]
commands += [('default46',ROOT,['python3','tools/test_workflow_assurance.py'],0),('historical118',historical,['python3','tools/test_workflow_assurance.py','--check','foundation-ready'],0),('current118',ROOT,['python3','tools/test_workflow_assurance.py','--check','foundation-ready'],1),('compliance',ROOT,['bash','tools/validate.sh'],0),('payload',ROOT,['bash','tools/validate.sh','--payload'],0),('adversarial',ROOT,['python3','.agent/evidence/122/qa1-adversarial.py'],0)]
results = []
for name,cwd,argv,wanted in commands:
    started=time.time(); result=subprocess.run(argv,cwd=cwd,env=env,capture_output=True)
    out = ROOT/'.agent/evidence/122-qa-adversarial.txt' if name=='adversarial' else E/('qa1-'+name+'.stdout')
    err=E/('qa1-'+name+'.stderr')
    assert not out.exists() and not err.exists()
    out.write_bytes(result.stdout); err.write_bytes(result.stderr)
    row={'name':name,'argv':argv,'cwd':str(cwd),'revision':git(cwd,'rev-parse','HEAD'),'environment':env,'actual_exit':result.returncode,'expected_exit':wanted,'stdout':str(out.relative_to(ROOT)),'stderr':str(err.relative_to(ROOT)),'elapsed_seconds':round(time.time()-started,3),'passed':result.returncode==wanted}
    if name=='default46': row['passed'] &= [line[5:] for line in result.stdout.decode().splitlines() if line.startswith('PASS ')]==expected
    if name=='current118': row['passed'] &= b'AssuranceError: pinned entry bytes/mode changed: tools/workflow_assurance.py' in result.stderr
    results.append(row); write(name+'.execution.json',row)
after=inventory(ROOT); after_hist=inventory(historical)
bmap={row[0]:row[1:] for row in before}; amap={row[0]:row[1:] for row in after}
changed=[path for path in sorted(bmap.keys()|amap.keys()) if bmap.get(path)!=amap.get(path)]
write('after.json',{'revision':git(ROOT,'rev-parse','HEAD'),'protected_count':len(after),'protected_aggregate':aggregate(after),'historical_aggregate':aggregate(after_hist),'pins':pins(ROOT),'changed_paths':changed,'preserved':before==after and before_hist==after_hist})
write('results.json',{'mandatory_command_count':9,'additional_adversarial_command_count':1,'commands':results,'protected_preserved':before==after and before_hist==after_hist,'all_passed':all(r['passed'] for r in results) and before==after and before_hist==after_hist})
raise SystemExit(0 if all(r['passed'] for r in results) and before==after and before_hist==after_hist else 1)
