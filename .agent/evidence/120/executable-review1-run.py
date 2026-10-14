"""Independent wrapper for the unchanged frozen control transport, one stage at a time."""
import hashlib, importlib.util, json, os, pathlib, subprocess, sys
ROOT = pathlib.Path(__file__).resolve().parents[3]; os.chdir(ROOT)
PREFIX = '.agent/evidence/120/executable-review1-'
INPUT = 'a67d67f1b82c54118d6023a2f7092f93bf4f90c0'
AUTHOR = 'f4c1f3f2e3b7d0db407853dd23953ac139aab3fa'
HELPER = '.agent/evidence/120/controls1-run.py'
def sha(data): return hashlib.sha256(data).hexdigest()
def git(*args): return subprocess.check_output(['git', *args]).decode().strip()
def write(path, raw):
    with pathlib.Path(path).open('xb') as handle: handle.write(raw)
stage = sys.argv[1]; assert stage in ('controls', 'preservation')
assert os.environ['PYTHONDONTWRITEBYTECODE'] == '1'
subprocess.run(['git','merge-base','--is-ancestor',INPUT,'HEAD'],check=True)
seal = json.loads(pathlib.Path('.agent/evidence/120/controls1-executable-seal.json').read_text())
assert len(seal['files']) == 80
for path, pin in seal['files'].items():
    assert sha(pathlib.Path(path).read_bytes()) == pin['sha256'], path
    assert git('hash-object',path) == pin['git_blob'] == git('rev-parse',AUTHOR+':'+path), path
spec = importlib.util.spec_from_file_location('frozen_controls', ROOT / HELPER)
transport = importlib.util.module_from_spec(spec); spec.loader.exec_module(transport)
source = pathlib.Path('tools/workflow_assurance.py').read_text()
manifest = json.loads(pathlib.Path('.agent/evidence/120/controls1-author1-controls-manifest.json').read_text())
assert manifest['completed'] is True and len(manifest['captures']) == 33
private_blobs = []
for index, (case, before, after, marker) in enumerate(transport.CONTROLS):
    assert source.count(before) == 1 and before != after
    for offset, suffix in enumerate(('positive','semantic-red','restored')):
        row = manifest['captures'][index*3+offset]
        assert row['label'] == case+'-'+suffix and row['actual_exit'] == (1 if offset==1 else 0)
        for stream in ('stdout','stderr'): assert sha(pathlib.Path(row[stream]).read_bytes()) == row[stream+'_sha256']
        raw = subprocess.check_output(['git','cat-file','blob',next(pin['git_blob'] for path,pin in row['inputs'].items() if path.endswith('/workflow_assurance.py'))])
        expected = source.replace(before,after,1) if offset==1 else source
        assert raw == expected.encode() and row['protected_before'] == row['protected_after'] == manifest['protected']
        if offset==1:
            assert row['mutation'] == {'before':before,'after':after} and row['expected_assertion_line'] == marker
            assert pathlib.Path(row['stdout']).read_bytes() == b''
            assert [line for line in pathlib.Path(row['stderr']).read_text().splitlines() if line.startswith('AssertionError: POLICY_ASSERTION:')] == [marker]
            private_blobs.append(dict(case=case, source_sha256=sha(raw), source_git_blob=next(pin['git_blob'] for path,pin in row['inputs'].items() if path.endswith('/workflow_assurance.py')), assertion=marker))
        else:
            assert pathlib.Path(row['stdout']).read_bytes() == ('PASS '+case+'\n').encode() and pathlib.Path(row['stderr']).read_bytes() == b''
revision = git('rev-parse','HEAD'); protected = transport.snapshot()
if stage=='controls': write(PREFIX+'preflight.json',(json.dumps(dict(reviewed_revision=INPUT, actual_executed_revision=revision, author_commit=AUTHOR, author_pins=seal['files'], private_mutants=private_blobs, author_controls_checked=33),indent=2)+'\n').encode())
argv = ['python3',HELPER,stage,'--run-id','reviewer1']
process = subprocess.run(argv,capture_output=True,env=os.environ)
out=PREFIX+stage+'.stdout.txt'; err=PREFIX+stage+'.stderr.txt'
write(out,process.stdout); write(err,process.stderr)
record=dict(argv=argv,cwd=str(ROOT),environment={'PYTHONDONTWRITEBYTECODE':'1'},actual_executed_revision=revision,actual_exit=process.returncode,stdout=out,stderr=err,stdout_sha256=sha(process.stdout),stderr_sha256=sha(process.stderr),helper_sha256=sha(pathlib.Path(HELPER).read_bytes()),protected_before=protected,protected_after=transport.snapshot())
write(PREFIX+stage+'.json',(json.dumps(record,indent=2)+'\n').encode())
print('actual_exit:',process.returncode); print(process.stdout.decode(),end=''); print(process.stderr.decode(),end='')
assert record['protected_after']==protected
sys.exit(process.returncode)
