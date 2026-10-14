"""Read immutable completed proof; no runtime control or preservation command is rerun."""
import copy, hashlib, importlib.util, json, os, pathlib, subprocess
ROOT = pathlib.Path(__file__).resolve().parents[3]; os.chdir(ROOT)
INPUT = '610b959b981be45fb20e90db683ee3f49319ec70'
AUTHOR = 'f4c1f3f2e3b7d0db407853dd23953ac139aab3fa'
PROOF = '37cddf0d8339ee5f0f267be9cb9a310ac5fc5d2a'
PREFIX = '.agent/evidence/120/executable-review2-'
def git(*args): return subprocess.check_output(['git', *args]).decode().strip()
def blob(revision, path): return subprocess.check_output(['git','show',revision+':'+path])
def sha(raw): return hashlib.sha256(raw).hexdigest()
def load(path): return json.loads(pathlib.Path(path).read_text())
assert os.environ['PYTHONDONTWRITEBYTECODE']=='1'
subprocess.run(['git','merge-base','--is-ancestor',INPUT,'HEAD'],check=True)
seal=load('.agent/evidence/120/controls1-executable-seal.json')
assert len(seal['files'])==80
for path,pin in seal['files'].items():
    assert sha(pathlib.Path(path).read_bytes())==pin['sha256']
    assert git('hash-object',path)==pin['git_blob']==git('rev-parse',AUTHOR+':'+path)
spec=importlib.util.spec_from_file_location('transport',ROOT/'.agent/evidence/120/controls1-run.py')
t=importlib.util.module_from_spec(spec); spec.loader.exec_module(t)
tests_spec=importlib.util.spec_from_file_location('acceptance_inventory',ROOT/'tools/test_workflow_assurance.py')
tests=importlib.util.module_from_spec(tests_spec); tests_spec.loader.exec_module(tests)
author=load('.agent/evidence/120/controls1-author1-controls-manifest.json')
reviewer=load('.agent/evidence/120/controls1-reviewer1-controls-manifest.json')
preservation=load('.agent/evidence/120/controls1-reviewer1-preservation-manifest.json')
assert author['completed'] is reviewer['completed'] is preservation['completed'] is True
assert len(author['captures'])==len(reviewer['captures'])==33 and len(preservation['captures'])==30
assert reviewer['protected']==preservation['protected']
assert {p for p in author['protected'] if author['protected'][p]!=reviewer['protected'][p]}=={'.agent/run_state.json'}
source=pathlib.Path('tools/workflow_assurance.py').read_text(); identities={}
def verify_record(row, session):
    assert row['actual_exit']==row['expected_exit']
    assert row['protected_before']==row['protected_after']==session['protected']
    for stream in ('stdout','stderr'):
        assert sha(pathlib.Path(row[stream]).read_bytes())==row[stream+'_sha256']
    for path,pin in row['inputs'].items():
        raw=subprocess.check_output(['git','cat-file','blob',pin['git_blob']])
        assert sha(raw)==pin['sha256']
        item=identities.setdefault(pin['git_blob'],dict(sha256=pin['sha256'],type='blob',size_bytes=len(raw),exercised_revisions=[]))
        assert item['sha256']==pin['sha256']
        if row['revision'] not in item['exercised_revisions']: item['exercised_revisions'].append(row['revision'])
def verify_controls(session):
    for i,(case,before,after,marker) in enumerate(t.CONTROLS):
        assert source.count(before)==1
        for j,suffix in enumerate(('positive','semantic-red','restored')):
            row=session['captures'][i*3+j]; verify_record(row,session)
            assert row['label']==case+'-'+suffix and row['actual_exit']==(1 if j==1 else 0)
            assert row['revision']==session['actual_helper_revision']
            source_pin=next(pin for path,pin in row['inputs'].items() if path.endswith('/workflow_assurance.py'))
            raw=subprocess.check_output(['git','cat-file','blob',source_pin['git_blob']])
            assert raw==(source.replace(before,after,1) if j==1 else source).encode()
            if j==1:
                assert row['mutation']==dict(before=before,after=after)
                assert pathlib.Path(row['stdout']).read_bytes()==b'' and row['expected_assertion_line']==marker
                err=pathlib.Path(row['stderr']).read_text()
                assert 'SETUP_ERROR' not in err and 'ModuleNotFoundError' not in err
                assert [line for line in err.splitlines() if line.startswith('AssertionError: POLICY_ASSERTION:')]==[marker]
            else:
                assert pathlib.Path(row['stdout']).read_bytes()==('PASS '+case+'\n').encode()
                assert pathlib.Path(row['stderr']).read_bytes()==b''
verify_controls(author); verify_controls(reviewer)
assert [r['label'] for r in preservation['captures'][:26]]==list(tests.CASES+tests.AGF_CASES)
for i,row in enumerate(preservation['captures']):
    verify_record(row,preservation)
    if i<26:
        assert row['actual_exit']==0 and pathlib.Path(row['stdout']).read_bytes()==('PASS '+row['label']+'\n').encode()
        assert pathlib.Path(row['stderr']).read_bytes()==b''
expected_tail=['live-stale118','history-clone','history-checkout','historical-foundation-ready']
assert [r['label'] for r in preservation['captures'][26:]]==expected_tail
live=preservation['captures'][26]; assert live['actual_exit']==1
assert pathlib.Path(live['stdout']).read_bytes()==b''
assert pathlib.Path(live['stderr']).read_text().splitlines()==['AssuranceError: pinned entry bytes/mode changed: tools/workflow_assurance.py']
assert all(r['actual_exit']==0 for r in preservation['captures'][27:])
historical=preservation['captures'][-1]
assert historical['revision']=='8ac94f6808e8197111197c9acbf59b2aa92efc7c'
assert pathlib.Path(historical['stdout']).read_text().splitlines()==['PASS foundation-ready: valid current20 receipt and independent typed/proof/identity/continuity attacks']
for path,pin in historical['inputs'].items():
    if path.endswith('/tools/workflow_assurance.py') or path.endswith('/tools/test_workflow_assurance.py'):
        relative='tools/'+path.rsplit('/',1)[-1]
        assert git('rev-parse',historical['revision']+':'+relative)==pin['git_blob']
sessions={'author':author,'reviewer':reviewer}
state_refs={}
for name,session in sessions.items():
    rev=session['actual_helper_revision']
    for path,pin in session['protected'].items():
        assert sha(blob(rev,path))==pin['sha256']
        if path!='.agent/run_state.json': assert sha(pathlib.Path(path).read_bytes())==pin['sha256']
    assert git('rev-parse',rev+':.agent/evidence/120/controls1-run.py')==seal['files']['.agent/evidence/120/controls1-run.py']['git_blob']
    state_refs[name]=dict(revision=rev,git_blob=git('rev-parse',rev+':.agent/run_state.json'),sha256=session['protected']['.agent/run_state.json']['sha256'])
old=json.loads(blob(state_refs['author']['revision'],'.agent/run_state.json'))
new=json.loads(blob(state_refs['reviewer']['revision'],'.agent/run_state.json'))
dispatch=load('.agent/evidence/120/executable-review1-dispatch.json')
assert len(new['history'])==len(old['history'])+1 and new['history'][:-1]==old['history']
assert new['history'][-1]['event']=='120-final-bundle-review-dispatch' and new['history'][-1]['at']==dispatch['at']
expected=copy.deepcopy(old)
expected['circuit_breaker']['120-final-bundle-review']={'attempts':1,'limit':3}
expected['history'].append(new['history'][-1]); expected['updated_at']=dispatch['at']
assert expected==new
assert blob(state_refs['reviewer']['revision'],'.agent/evidence/120/executable-review1-dispatch.json')==pathlib.Path('.agent/evidence/120/executable-review1-dispatch.json').read_bytes()
old_paths=git('ls-tree','-r','--name-only',PROOF,'.agent/evidence/120').splitlines()
review_paths=[p for p in old_paths if '/controls1-reviewer1-' in p or '/executable-review1-' in p]
assert review_paths
for path in review_paths: assert pathlib.Path(path).read_bytes()==blob(PROOF,path)
failure=load('.agent/evidence/120/executable-review1-verifier1.json'); assert failure['actual_exit']==1
proof=dict(reviewed_revision=INPUT,actual_executed_revision=git('rev-parse','HEAD'),auxiliary_attempt=2,runtime_rerun=False,author_controls_verified=33,reviewer_controls_verified=33,preservation_verified=30,session_local_snapshots_exact=True,shared_protected_inputs_exact=True,root_dispatch_state_provenance=state_refs,root_dispatch_event=new['history'][-1],reviewer_proof_commit=PROOF,reviewer_files_preserved=len(review_paths),author_file_pins=seal['files'],reviewer_paths=review_paths,identity_objects=identities,private_mutants_each_exactly_one_declared_replacement=True,verifier1_failure_preserved=True)
path=pathlib.Path(PREFIX+'proof.json'); assert not path.exists(); path.write_text(json.dumps(proof,indent=2)+'\n')
print('PASS author33/reviewer33/preservation30; session-local exact snapshots; cross-session protected inputs; immutable Root dispatch provenance; private blobs; no runtime reruns')
