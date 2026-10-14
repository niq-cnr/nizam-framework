"""Root evidence capture: inspect actual receipts; never synthesize test results."""
import hashlib
import importlib.util
import json
import pathlib
import re
import subprocess
import jsonschema

root = pathlib.Path(__file__).resolve().parents[3]
def read(path):
    target = root / path
    assert target.is_file() and not target.is_symlink(), path
    for parent in target.parents:
        if parent == root: break
        assert not parent.is_symlink(), path
    return target.read_bytes()
def obj(path): return json.loads(read(path))
def sha(path): return hashlib.sha256(read(path)).hexdigest()
def git(*args): return subprocess.check_output(['git','-C',str(root),*args])
def strict(value):
    assert value['final_verdict']['approved'] is True
    assert all(type(value[k]) is list and value[k] == [] for k in ('issues','missing_acceptance_coverage','unsupported_claims'))

contract = obj('.agent/contracts/117.json')
candidate = obj('.agent/evidence/117/source-candidate.json')
mode = obj('.agent/validator/117-mode-b.json')
qa = obj('.agent/qa/117.json')
bundle = obj('.agent/evidence/117/acceptance-bundle.json')
revision = candidate['revision']
assert revision == '2ab311bde4e104ec4a2b1b739fe8fa91b48fe5b7'
assert git('rev-parse', revision+'^{tree}').decode().strip() == candidate['tree']
strict(mode); strict(qa)
assert mode['actor'] == '/root/wa_validator' and qa['actor'] == '/root/wa_acceptance117'
assert qa['qa_pass'] is True and qa['required_fixes'] == []
assert type(qa['checks_run']) is int and qa['checks_run'] == 12
assert type(qa['checks_passed']) is int and qa['checks_passed'] == 12
assert contract['status'] == 'approved'
jsonschema.validate(qa, obj('.nizam/schema/qa_verdict.schema.json'))
dependencies = {row['path']:row['sha256'] for row in bundle['inputs']}
assert len(dependencies) == 27
for value in (candidate, mode, qa):
    assert value['revision'] == revision
    assert value['source_sha256'] == candidate['source_sha256']
    assert value['sealed_dependencies_sha256'] == dependencies
for path, digest in {**dependencies, **candidate['source_sha256']}.items():
    assert sha(path) == digest
    assert hashlib.sha256(git('show',revision+':'+path)).hexdigest() == digest
    mode_text = git('ls-tree',revision,path).decode().split()[0]
    assert mode_text in ('100644','100755')
    assert bool((root/path).stat().st_mode & 0o111) == (mode_text == '100755')
print('PASS actual SourceC/tree/four core and all27 current/Git dependency bytes and modes')
assert len(qa['checks']) == len(contract['verification']) == 12
for expected, actual in zip(contract['verification'],qa['checks']):
    assert all(actual[k] == v for k,v in expected.items())
    assert type(actual['exit_code']) is int and actual['exit_code'] == 0
    assert actual['evidence'] in qa['evidence_files'] and sha(actual['evidence']) == actual['sha256']
    text = read(actual['evidence']).decode()
    for key,value in [('COMMAND',expected['command']),('REVISION',revision),('EXIT','0')]:
        assert re.findall('^'+key+': (.*)$',text,re.M) == [value]
    assert 'STDOUT:\n' in text and 'STDERR:\n' in text
print('PASS all12 ordered exact QA command/revision/exit/raw SHA records')
spot = qa['adversarial']
assert spot['performed'] is True and spot['command'] not in [r['command'] for r in qa['checks']]
assert spot['evidence'] in qa['evidence_files']
assert qa['adversarial_check']['result'] == 'pass' and qa['adversarial_check']['evidence'] == spot['evidence']
text = read(spot['evidence']).decode()
for key,value in [('COMMAND',spot['command']),('REVISION',revision),('EXIT','0')]:
    assert re.findall('^'+key+': (.*)$',text,re.M) == [value]
assert 'VALID CONTROL:' in text and 'ADVERSARIAL CONTROL:' in text and 'RESTORED CONTROL:' in text
assert 'symlink write-intent path' in text
assert len(qa['evidence_files']) == len(set(qa['evidence_files'])) == 13
print('PASS distinct fresh QA actor and actual additional symlink adversary with valid/restored controls')
spec = importlib.util.spec_from_file_location('capture117guard',root/'.agent/evidence/117/scope-guard.py')
guard = importlib.util.module_from_spec(spec); spec.loader.exec_module(guard)
guard.sealed_inputs()
print('PASS actual independent bundle gate, baseline Git/input/mode/seal and twelve behavioral proof bindings')
receipt = {'feature':'117','owner':'/root','passed':True,'revision':revision,
           'source_sha256':candidate['source_sha256'],'sealed_dependencies_sha256':dependencies,
           'qa_ref':'.agent/qa/117.json','mode_b_ref':'.agent/validator/117-mode-b.json',
           'qa_sha256':sha('.agent/qa/117.json'),'mode_b_sha256':sha('.agent/validator/117-mode-b.json'),
           'checks_captured':12,'adversarial_captured':True,
           'evidence_sha256':{p:sha(p) for p in qa['evidence_files']},
           'capture_helper':'.agent/evidence/117/capture-attempt1.py'}
target=root/'.agent/evidence/117/evidence-capture.json'
assert not target.exists()
target.write_text(json.dumps(receipt,indent=2)+'\n')
guard.completed_receipts(contract)
print('PASS independent Root capture; lifecycle still in_progress')
