"""Exact private-byte deltas and historical selected-state bindings; no API call."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];E=ROOT/'.agent/evidence/122'
git=lambda *a:subprocess.check_output(['git','-C',str(ROOT),*a])
inventory=json.loads((E/'controls3-identities.json').read_bytes());source=(ROOT/'tools/workflow_assurance.py').read_bytes()
deltas={
 'infrastructure-failed':("request['cause'] + ('-diagnosis' if request['cause'] == 'infrastructure' else '-repair'),","request['cause'] + ('-repair' if request['cause'] == 'infrastructure' else '-repair'),"),
 'semantic-failed':("require(rejected or any(verdict.get(key, []) for key in arrays), 'failure semantic verdict passed')","require(True or any(verdict.get(key, []) for key in arrays), 'failure semantic verdict passed')"),
 'reject-cause-relabel':("authority['role'] == 'Orchestrator' and authority['approved'] is True and","authority['role'] == 'Orchestrator' and authority['approved'] in (True, 1) and"),
 'counter-continuity':('    verify_record_update(anchor, current, owned)',"    verify_record_update(anchor, current, owned + ['/scope_budget/total_lines_changed'])")}
for case,(old,new) in deltas.items():
    assert source.count(old.encode())==1 and source.replace(old.encode(),new.encode())==git('cat-file','blob',inventory['objects'][case]['git_oid'])
    print('EXACT_PRIVATE_DELTA_OK',case,repr(old),'=>',repr(new))
binary=Path('/home/cnross/.tmp/nizam-feature122-ci-git255-build1/install/bin/git')
assert hashlib.sha256(binary.read_bytes()).hexdigest()=='81ba53616316440d4afc8a99107301b32790eb1a9157bdd97274017fbd4d0e4b'
for prefix in ('controls3-runtime2','controls3-executable-review1'):
    result=json.loads((E/(prefix+'-result.json')).read_bytes());revision=result['exercised_revision'];pin=result['protected_before']['pins']['.agent/run_state.json']
    raw=git('show',revision+':.agent/run_state.json');row=git('ls-tree',revision,'--','.agent/run_state.json').decode().split()
    assert hashlib.sha256(raw).hexdigest()==pin['sha256'] and row[2]==pin['git_blob'] and (row[0]=='100755')==pin['executable']
    for capture in result['captures']:
        env=capture['environment'];assert env['PATH'].split(':')[0]==str(binary.parent) and env['GIT_EXEC_PATH']=='/home/cnross/.tmp/nizam-feature122-ci-git255-build1/install/libexec/git-core'
    print('HISTORICAL_STATE_AND_PINNED_GIT_OK',prefix,revision,'blob+executable only; fullFS equality separately retained')
