"""Generator development captures for immutable initial Source119."""
import ast,hashlib,json,os,pathlib,subprocess,sys
root=pathlib.Path(__file__).resolve().parents[3];os.chdir(root)
os.environ['PYTHONDONTWRITEBYTECODE']='1'
base='0d5a1eea9b961e5c4261268bd2b9e946c6ed70c3'
git=lambda *a:subprocess.check_output(['git',*a],text=True).strip()
paths=('tools/workflow_assurance.py','tools/test_workflow_assurance.py','tools/convergent_review.py','.agent/contracts/119.json')
identities={p:dict(sha256=hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest(),git_blob=git('hash-object',p)) for p in paths}
functions=lambda s:{n.name:ast.dump(n,include_attributes=False) for n in ast.parse(s).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))}
old=functions(subprocess.check_output(['git','show',base+':tools/workflow_assurance.py'],text=True));new=functions(pathlib.Path(paths[0]).read_text())
assert all(new.get(k)==v for k,v in old.items()) and set(new)-set(old)=={'convergent_agf_verdict'}
assert git('diff',base,'HEAD','--','tools/test_workflow_assurance.py','tools/convergent_review.py','.nizam')==''
pathlib.Path('.agent/evidence/119/source1-preservation.txt').write_text('PASS all '+str(len(old))+' old top-level function/class ASTs unchanged; only convergent_agf_verdict added; tests/convergence/installed unchanged\nBASE: '+base+'\nREVISION: '+git('rev-parse','HEAD')+'\nEXIT: 0\n')
cases=('approve-empty','advisory-visible','block-carried','reject-issues','reject-missing-coverage','reject-unsupported')
commands=[(n,['python3','tools/test_workflow_assurance.py','--case',n]) for n in cases]
commands.append(('default26',['python3','tools/test_workflow_assurance.py']))
checks=('test_ledger_count_mutation_is_rejected','test_consensus_invalid_lifecycle_cannot_render_an_approval','test_standalone_ledger_enforces_lifecycle_consensus_and_evidence_relations','test_initial_suppressed_heads_rejected_by_validator_and_renderer','test_generated_prior_suppressed_carry_and_resolution_validate_and_render')
commands.append(('convergence',['python3','tools/test_convergent_review.py',*('SemanticMutationTests.'+n for n in checks)]))
records=[]
for label,argv in commands:
    result=subprocess.run(argv,capture_output=True);prefix='.agent/evidence/119/source1-'+label
    pathlib.Path(prefix+'.stdout.txt').write_bytes(result.stdout);pathlib.Path(prefix+'.stderr.txt').write_bytes(result.stderr)
    records.append(dict(label=label,argv=argv,cwd=str(root),revision=git('rev-parse','HEAD'),environment={'PYTHONDONTWRITEBYTECODE':'1'},exit=result.returncode,inputs=identities,stdout=prefix+'.stdout.txt',stderr=prefix+'.stderr.txt'))
    pathlib.Path('.agent/evidence/119/source1-results.json').write_text(json.dumps(records,indent=2)+'\n')
    print(label,'actual_exit',result.returncode,flush=True)
    if result.returncode:raise SystemExit(result.returncode)
assert identities=={p:dict(sha256=hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest(),git_blob=git('hash-object',p)) for p in paths}
print('PASS Source119 development six/default26/convergence and immutable inputs')
