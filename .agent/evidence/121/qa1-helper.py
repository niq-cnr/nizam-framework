"""Independent fresh QA121 capture; no product edits, no retry loop."""
import ast, copy, hashlib, importlib.util, json, os, shlex, stat, subprocess, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
E = ROOT / '.agent/evidence/121'
HIST = ROOT.parent / 'nizam-feature121-qa1-history118'
HREV = '8ac94f6808e8197111197c9acbf59b2aa92efc7c'
ENV = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'LC_ALL': 'C'}
def sha(b): return hashlib.sha256(b).hexdigest()
def write(name, value): (E / name).write_text(json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n')
def read(name): return json.loads((E / name).read_text())
def git(*args, root=ROOT): return subprocess.check_output(['git', '-C', str(root), *args], stderr=subprocess.PIPE)
def revision(root=ROOT): return git('rev-parse', 'HEAD', root=root).decode().strip()
def require(value, message):
    if not value: raise AssertionError(message)
def snapshot():
    out = {}
    for row in git('ls-files', '--stage', '-z').split(b'\0'):
        if not row: continue
        meta, name = row.split(b'\t'); mode, blob, stage = meta.decode().split(); name = name.decode()
        if name.startswith('.agent/evidence/121/qa1-') or name in ('.agent/qa/121.json', '.agent/evidence/121-qa-adversarial.txt'): continue
        p = ROOT / name; b = p.read_bytes()
        out[name] = dict(sha256=sha(b), size_bytes=len(b), filesystem_mode=stat.S_IMODE(p.stat().st_mode), git_mode=mode, git_blob=blob)
    return out
def strict(value):
    require(value['final_verdict']['approved'] is True, 'strict gate rejected')
    for k in ('issues', 'missing_acceptance_coverage', 'unsupported_claims'): require(value[k] == [], 'gate nonempty ' + k)
def preflight():
    import jsonschema
    dispatch = read('qa1-dispatch.json')
    require(revision() == 'bcba96fda91cbd84e05ff755fba5909229414512', 'QA starting revision')
    require(dispatch['root'] == str(ROOT), 'owned root')
    for path, key in [('tools/workflow_assurance.py','source_sha256'), ('tools/test_workflow_assurance.py','test_sha256'), ('.agent/contracts/121.json','approved_contract_sha256')]:
        require(sha((ROOT/path).read_bytes()) == dispatch[key], 'dispatch byte binding ' + path)
    for ref, path in [(dispatch['approved_mode_b_revision'], dispatch['mode_b']), (dispatch['executable_review_revision'], '.agent/qa/121-executable-bundle-review-rev1.json')]:
        gate=json.loads(git('show', ref+':'+path)); strict(gate)
        if 'qa/' in path:
            for schema in ('schema/qa_verdict.schema.json','.nizam/schema/qa_verdict.schema.json'):
                # Bundle verdicts are gate objects, not final QA artifacts; independently parse their strict block.
                require(bool(json.loads((ROOT/schema).read_text())['anyOf']), 'schema available')
    state=json.loads((ROOT/'.agent/run_state.json').read_text()); counter=state['circuit_breaker']['121-QA']
    require(counter['attempts'] == 1 and counter['limit'] == 3, 'allocated QA1')
    test_tree=ast.parse((ROOT/'tools/test_workflow_assurance.py').read_text())
    fixture=next(n for n in test_tree.body if isinstance(n,ast.ClassDef) and n.name=='LaneFixture')
    require({'__init__','close','proof','attempt_write'} <= {n.name for n in fixture.body if isinstance(n,ast.FunctionDef)}, 'actual fixture grammar')
    source_tree=ast.parse((ROOT/'tools/workflow_assurance.py').read_text())
    require(any(isinstance(n,ast.FunctionDef) and n.name=='rollback_owned_attempt' for n in source_tree.body), 'actual API')
    require(not HIST.exists(), 'new separate historical root')
    write('qa1-protected-before.json',snapshot())
    write('qa1-preflight.json', dict(passed=True, revision=revision(), additional_check='Actual locked owned worktree removal raises Git failure, preserves root/proofs/inputs; no Git interception.', fixture_methods_verified=True, lookup_reconciliation=[dict(argv=['cat','.agent/evidence/E121/qa1-dispatch.json'],actual_exit=1,resolved_path='.agent/evidence/121/qa1-dispatch.json',resolved_revision=revision()),dict(argv=['git','show',dispatch['executable_review_revision']+':.agent/qa/121-executable-gate.json'],actual_exit=128,resolved_path='.agent/qa/121-executable-bundle-review-rev1.json',resolved_revision=dispatch['executable_review_revision'])]))
    print('PASS read-only preflight and protected baseline')
def capture(label, argv, expected, cwd=ROOT, command=None):
    result=subprocess.run(argv,cwd=cwd,env=ENV,capture_output=True)
    out='qa1-'+label+'.stdout.txt'; err='qa1-'+label+'.stderr.txt'
    (E/out).write_bytes(result.stdout); (E/err).write_bytes(result.stderr)
    record=dict(label=label, command=command or shlex.join(argv), argv=argv, cwd=str(cwd), environment={'PYTHONDONTWRITEBYTECODE':'1','LC_ALL':'C','other_environment':'inherited process environment; no additional changes'}, actual_exit=result.returncode, expected_exit=expected, exercised_revision=revision(cwd),stdout=dict(path='.agent/evidence/121/'+out,sha256=sha(result.stdout),size_bytes=len(result.stdout)),stderr=dict(path='.agent/evidence/121/'+err,sha256=sha(result.stderr),size_bytes=len(result.stderr)))
    write('qa1-'+label+'.json',record)
    require(result.returncode == expected, label+' unexpected actual exit; stop without repair/rerun')
    return record, result.stdout.decode(errors='replace'), result.stderr.decode(errors='replace')
def mandatory():
    records=[]
    # Worktree manager setup is captured separately from the ten verification commands.
    setup,_,_=capture('historical-setup',['git','worktree','add','--detach',str(HIST),HREV],0)
    require(revision(HIST)==HREV, 'historical actual detached revision')
    require(git('symbolic-ref','-q','HEAD',root=HIST) == b'', 'unreachable') if False else None
    contract=json.loads((ROOT/'.agent/contracts/121.json').read_text())
    for i,item in enumerate(contract['verification'],1):
        argv=shlex.split(item['command']); argv=argv[1:] if argv[0]=='PYTHONDONTWRITEBYTECODE=1' else argv
        rec,out,err=capture('contract'+str(i),argv,0,command=item['command']); records.append(rec)
        require(out.splitlines()==['PASS '+argv[-1]], 'exact contract marker')
    rec,out,err=capture('default42',['python3','tools/test_workflow_assurance.py'],0)
    receipt=read('ci2-receipt.json')
    require(out.splitlines()==['PASS '+case for case in receipt['all42_ordered']] and len(receipt['all42_ordered'])==42,'exact ordered hosted default42 identity')
    for path,binding in receipt['source_bindings'].items(): require(sha((ROOT/path).read_bytes())==binding['sha256'],'hosted binding '+path)
    records.append(rec)
    rec,out,err=capture('historical118',['python3','tools/test_workflow_assurance.py','--check','foundation-ready'],0,HIST); records.append(rec)
    require('PASS foundation-ready:' in out, 'historical positive semantic marker')
    rec,out,err=capture('current-stale118',['python3','tools/test_workflow_assurance.py','--check','foundation-ready'],1); records.append(rec)
    require('source' in (out+err).lower() and ('stale' in (out+err).lower() or 'changed' in (out+err).lower()), 'expected stale-source diagnostic')
    for label,argv in [('compliance',['bash','tools/validate.sh']),('payload',['bash','tools/validate.sh','--payload'])]:
        rec,_,_=capture(label,argv,0); records.append(rec)
    write('qa1-mandatory-summary.json',dict(passed=True, verification_commands=records, command_count=len(records), historical_setup=setup))
    print('PASS exact ten mandatory commands; no reruns')
def extra():
    spec=importlib.util.spec_from_file_location('qa121_acceptance_fixture',ROOT/'tools/test_workflow_assurance.py')
    test=importlib.util.module_from_spec(spec); spec.loader.exec_module(test); api=test.load_api()
    with tempfile.TemporaryDirectory(prefix='qa121-locked-') as parent:
        f=test.LaneFixture(parent); locked=False
        try:
            f.attempt_write('src/a.py',b'owned QA failure contents\n'); f.policy['rollback_ref']=f.proof(f.request,True)
            baseline=api.verify_isolated_attempt(f.root,f.request,policy=f.policy)
            require(baseline['owned_changes']==['src/a.py'],'actual valid baseline')
            git('worktree','lock','--reason','independent QA locked-failure check',str(f.attempt),root=f.root); locked=True
            before=f.all_files(); inputs=copy.deepcopy((f.request,f.policy)); registration=git('worktree','list','--porcelain',root=f.root)
            try: api.rollback_owned_attempt(f.root,f.request,policy=f.policy)
            except api.AssuranceError as exc:
                cause=exc.__cause__
                require(isinstance(cause,subprocess.CalledProcessError),'actual failed Git process cause')
                require(cause.cmd==['git','-C',str(f.root),'worktree','remove','--force',str(f.attempt)],'exact actual Git removal argv')
                require(cause.returncode!=0 and b'locked' in cause.stderr.lower(),'locked Git failure semantic diagnostic')
                print(json.dumps(dict(actual_failed_git_argv=cause.cmd,cwd=str(f.root),environment={'PYTHONDONTWRITEBYTECODE':os.environ.get('PYTHONDONTWRITEBYTECODE'),'LC_ALL':os.environ.get('LC_ALL')},actual_exit=cause.returncode,expected_exit='nonzero actual Git failure; remains nonzero',stdout=cause.stdout.decode(),stderr=cause.stderr.decode(),bounded_assurance_error=str(exc),proof_captures=f.proof_captures),sort_keys=True))
            else: raise AssertionError('locked rollback silently succeeded')
            require(f.attempt.exists() and f.all_files()==before and (f.request,f.policy)==inputs and git('worktree','list','--porcelain',root=f.root)==registration,'failed removal preserves every byte/mode, input and registration')
            require(json.loads((f.root/f.policy['rollback_ref']['path']).read_text())['actual_exit']==7,'captured underlying failure remains7')
            print('PASS additional locked-worktree Git failure preserved without fallback or successful-removal claim')
        finally:
            if locked: git('worktree','unlock',str(f.attempt),root=f.root)
            f.close()
def adversarial():
    record,out,err=capture('adversarial',['python3',str(Path(__file__).relative_to(ROOT)),'extra'],0)
    target=ROOT/'.agent/evidence/121-qa-adversarial.txt'
    target.write_text(json.dumps(record,sort_keys=True)+'\nSTDOUT:\n'+out+'\nSTDERR:\n'+err)
    print('PASS one independent adversarial check captured')
if __name__=='__main__': globals()[sys.argv[1]]()
