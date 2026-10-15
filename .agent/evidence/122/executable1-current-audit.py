"""Independent post-replay AST, archive, actual trace and preservation review."""
import ast,hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];E=ROOT/'.agent/evidence/122'
sha=lambda b:hashlib.sha256(b).hexdigest()
result=json.loads((E/'controls3-executable-review1-result.json').read_bytes());inventory=json.loads((E/'controls3-identities.json').read_bytes())
assert result['complete'] is True and result['preparation_only'] is False and result['protected_before']==result['protected_after']
assert sha((E/'controls3-identities.pack').read_bytes())==inventory['pack_sha256']
objects={k:subprocess.check_output(['git','-C',str(ROOT),'cat-file','blob',v['git_oid']]) for k,v in inventory['objects'].items()}
assert len(objects)==8
for name,raw in objects.items():
    ref=inventory['objects'][name];assert sha(raw)==ref['sha256'] and len(raw)==ref['size_bytes'] and ref['type']=='blob'
original=ast.parse(objects['source']);targets={'infrastructure-failed':'route_failed_attempt','semantic-failed':'_failure_rejection','reject-cause-relabel':'route_failed_attempt','counter-continuity':'_failure_continuity'}
for case,function in targets.items():
    mutant=ast.parse(objects[case]);assert len(original.body)==len(mutant.body)
    changed=[getattr(a,'name',None) for a,b in zip(original.body,mutant.body) if ast.dump(a)!=ast.dump(b)]
    assert changed==[function],(case,changed)
captures=result['captures'];assert len(captures)==24
for c in captures:
    assert c['actual_exit']==c['expected_exit'] and c['protected_unchanged'] and c['release_revision']==result['release_revision']
    assert sha((ROOT/c['stderr']).read_bytes())==c['stderr_sha256']
    if c['stdout_storage']=='portable-pack-object':
        ref=json.loads((ROOT/c['stdout']).read_bytes());assert ref['pack']=='.agent/evidence/122/controls3-identities.pack'
        raw=subprocess.check_output(['git','-C',str(ROOT),'cat-file','blob',ref['identity']['git_oid']]);assert sha(raw)==ref['identity']['sha256'] and len(raw)==ref['identity']['size_bytes']
    else:raw=(ROOT/c['stdout']).read_bytes()
    assert sha(raw)==c['stdout_sha256'] and len(raw)==c['stdout_size_bytes']
for case in targets:
    trio=[c for c in captures if c['label'].startswith(case+'-')];assert [c['actual_exit'] for c in trio]==[0,1,0]
    assert (ROOT/trio[0]['stdout']).read_text().splitlines()==['PASS '+case] and (ROOT/trio[2]['stdout']).read_text().splitlines()==['PASS '+case]
    negative=trio[1];assert (ROOT/negative['stderr']).read_text().splitlines()==[inventory['controls'][case]['assertion']]
    lines=(ROOT/negative['stdout']).read_text().splitlines();assert not any(s.startswith('PASS ') for s in lines) and any(s.startswith('FIXTURE_TRACE ') for s in lines)
    traces=[json.loads(s[10:]) for s in lines if s.startswith('API_TRACE ')];last=traces[-1]
    assert last['returned'] is True and last['source_sha256']==inventory['objects'][case]['sha256'] and last==negative['intended_api_trace']
    if case=='infrastructure-failed':assert last['result']['route']=='infrastructure-repair' and last['result']['outcome']=='failed'
    elif case=='semantic-failed':assert last['semantic_verdict']['final_verdict']['approved'] is True and all(last['semantic_verdict'][k]==[] for k in ('issues','missing_acceptance_coverage','unsupported_claims'))
    elif case=='reject-cause-relabel':assert type(last['authority_approved']) is int and last['authority_approved']==1
    else:assert last['scope_budget']['total_lines_changed']==0 and last['result']['attempt']==1
archive=captures[:12];assert all(c['actual_exit']==0 for c in archive)
assert (ROOT/archive[1]['stdout']).read_bytes()==b'' and '--template=' in archive[0]['argv']
assert set((ROOT/archive[3]['stdout']).read_text().splitlines())=={v['git_oid']+' blob '+str(v['size_bytes']) for v in inventory['objects'].values()}
assert all('GIT_ALTERNATE_OBJECT_DIRECTORIES' not in c['environment'] and 'GIT_OBJECT_DIRECTORY' not in c['environment'] for c in captures)
print('EXECUTABLE_AUDIT_OK four actual0/1/0 trios, four private new122-only AST mutants, actual intended API return traces,12freshODBcommands/8blobs, all raw/ref hashes resolved, full protected byte/mode equality')
