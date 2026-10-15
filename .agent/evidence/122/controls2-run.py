"""Frozen four-case controls; prepare-check restores bytes only, behavior needs Root release."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
PREFIX = '.agent/evidence/122/controls2-'
SOURCE = 'fff790d700daa6247557851c6988f8f6e7465ec291907992374d00e3c9d886b6'
TEST = 'e251283add498c699f6c90fd7934f92dcffe570e6c3fdda51326c6dc0e504c21'
CONTRACT = '13dc45d0daf41fc9af4828ec0b84b1a05ded39f51b2e1fc5b903831e557d42c5'
CASES = ('infrastructure-failed','semantic-failed','reject-cause-relabel','counter-continuity')
def sha(data): return hashlib.sha256(data).hexdigest()
def identity(data): return dict(git_oid=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest(),sha256=sha(data),size_bytes=len(data),type='blob')
def write(path, data):
    with Path(path).open('xb') as handle: handle.write(data)
def git(*args): return subprocess.check_output(['git','-C',str(ROOT),*args],stderr=subprocess.PIPE).decode().strip()
def snapshot(paths):
    rows = []; pins = {}
    selected = ('tools/workflow_assurance.py','tools/test_workflow_assurance.py','.agent/contracts/122.json','.agent/run_state.json',
        '.agent/evidence/122/api-interface.json',PREFIX+'run.py',PREFIX+'worker.py',PREFIX+'identities.json',PREFIX+'identities.pack')
    for path in sorted(paths):
        target = ROOT/path
        data = os.readlink(target).encode() if target.is_symlink() else target.read_bytes()
        row = [path,stat.S_IMODE(target.lstat().st_mode),'symlink' if target.is_symlink() else 'file',sha(data)]
        rows.append(row)
        if path in selected: pins[path] = dict(mode=row[1],kind=row[2],sha256=row[3],git_blob=identity(data)['git_oid'],executable=bool(target.lstat().st_mode & 0o111))
    return dict(count=len(rows),all_bytes_modes_sha256=sha(json.dumps(rows,separators=(',',':')).encode()),pins=pins)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare-check',action='store_true'); parser.add_argument('--release-revision'); parser.add_argument('--run-id',required=True)
    args = parser.parse_args(); assert re.fullmatch('[a-z0-9][a-z0-9-]*',args.run_id)
    assert bool(args.prepare_check) != bool(args.release_revision), 'preparation or explicit Root release required'
    assert os.environ.get('PYTHONDONTWRITEBYTECODE') == '1'
    assert not any(os.environ.get(k) for k in ('GIT_OBJECT_DIRECTORY','GIT_ALTERNATE_OBJECT_DIRECTORIES','GIT_DIR','GIT_WORK_TREE','GIT_INDEX_FILE'))
    os.chdir(ROOT)
    for path, expected in (('tools/workflow_assurance.py',SOURCE),('tools/test_workflow_assurance.py',TEST),('.agent/contracts/122.json',CONTRACT)):
        assert sha((ROOT/path).read_bytes()) == expected
        if args.release_revision:
            assert re.fullmatch('[0-9a-f]{40}',args.release_revision)
            assert subprocess.check_output(['git','-C',str(ROOT),'show',args.release_revision+':'+path]) == (ROOT/path).read_bytes()
    if args.release_revision: subprocess.run(['git','-C',str(ROOT),'merge-base','--is-ancestor',args.release_revision,'HEAD'],check=True)
    inventory = json.loads((ROOT/(PREFIX+'identities.json')).read_bytes())
    pack = (ROOT/(PREFIX+'identities.pack')).read_bytes(); assert sha(pack) == inventory['pack_sha256']
    paths = set(subprocess.check_output(['git','-C',str(ROOT),'ls-files','-z']).decode().split('\0'))- {''}
    paths.update(str(p.relative_to(ROOT)) for base in ('.nizam','.agent') for p in (ROOT/base).rglob('*') if p.is_file() and not p.is_symlink())
    protected_paths = sorted(paths); protected = snapshot(protected_paths); records = []; complete = False
    prefix = ROOT/(PREFIX+args.run_id); result_path = str(prefix)+'-result.json'; assert not Path(result_path).exists()
    revision = git('rev-parse','HEAD')
    def capture(label,argv,expected,cwd,env,data=None,marker=None,case=None,payload_ref=None):
        assert snapshot(protected_paths) == protected
        result = subprocess.run(argv,cwd=cwd,env=env,input=data,capture_output=True)
        out = str(prefix)+'-'+label+'.stdout'; err = str(prefix)+'-'+label+'.stderr'
        storage = 'raw'
        if payload_ref is not None and identity(result.stdout) == payload_ref:
            storage = 'portable-pack-object'; out += '.ref.json'
            write(out,(json.dumps(dict(storage=storage,pack=PREFIX+'identities.pack',identity=payload_ref),sort_keys=True)+'\n').encode())
        else: write(out,result.stdout)
        write(err,result.stderr)
        row = dict(label=label,argv=argv,cwd=str(cwd),environment=env,exercised_revision=revision,release_revision=args.release_revision,
            actual_exit=result.returncode,expected_exit=expected,expected_assertion=marker,stdout=str(Path(out).relative_to(ROOT)),stderr=str(Path(err).relative_to(ROOT)),
            stdout_sha256=sha(result.stdout),stdout_size_bytes=len(result.stdout),stdout_storage=storage,stderr_sha256=sha(result.stderr),protected_unchanged=snapshot(protected_paths)==protected)
        records.append(row)
        assert row['protected_unchanged'] and result.returncode == expected, row
        if marker:
            assert [s for s in result.stderr.decode().splitlines() if s.startswith('AssertionError: POLICY_ASSERTION:')] == [marker]
            assert not any(s.startswith('PASS ') for s in result.stdout.decode().splitlines()) and b'FIXTURE_TRACE ' in result.stdout
            traces = [json.loads(s[10:]) for s in result.stdout.decode().splitlines() if s.startswith('API_TRACE ')]
            assert traces and traces[-1].get('returned') is True, 'actual API must return before intended assertion'
            last = traces[-1]; row['intended_api_trace'] = last
            if case == 'infrastructure-failed': assert last['result']['route'] == 'infrastructure-repair' and last['result']['outcome'] == 'failed'
            elif case == 'semantic-failed': assert last['semantic_verdict']['final_verdict']['approved'] is True and all(last['semantic_verdict'][k] == [] for k in ('issues','missing_acceptance_coverage','unsupported_claims'))
            elif case == 'reject-cause-relabel': assert type(last['authority_approved']) is int and last['authority_approved'] == 1
            elif case == 'counter-continuity': assert last['scope_budget']['total_lines_changed'] == 0 and last['result']['attempt'] == 1
        elif case: assert result.stdout.decode().splitlines() == ['PASS '+case]
        return result.stdout
    try:
        with tempfile.TemporaryDirectory(prefix='nizam122-controls2-') as directory:
            private = Path(directory); home = private/'home'; home.mkdir(); bare = private/'empty.git'
            env = dict(PATH=os.defpath,HOME=str(home),LC_ALL='C',PYTHONDONTWRITEBYTECODE='1',GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL='/dev/null',GIT_CONFIG_SYSTEM='/dev/null')
            capture('archive-init',['git','init','--bare','--template=',str(bare)],0,private,env)
            def archive(label,*argv,data=None,payload_ref=None): return capture(label,['git','--git-dir',str(bare),*argv],0,private,env,data,payload_ref=payload_ref)
            assert archive('archive-empty','cat-file','--batch-all-objects','--batch-check') == b''
            assert not (bare/'objects/info/alternates').exists()
            archive('archive-import','index-pack','--stdin','--strict',data=pack)
            rows = archive('archive-inventory','cat-file','--batch-all-objects','--batch-check').decode().splitlines()
            assert {r.split()[0] for r in rows} == {v['git_oid'] for v in inventory['objects'].values()}
            assert {r.split()[0]:(r.split()[1],int(r.split()[2])) for r in rows} == {v['git_oid']:(v['type'],v['size_bytes']) for v in inventory['objects'].values()}
            recovered = {}
            for label,expected in inventory['objects'].items():
                recovered[label] = archive('archive-blob-'+label,'cat-file','blob',expected['git_oid'],payload_ref=expected)
                assert identity(recovered[label]) == expected
            assert not any((bare/('objects/info/'+name)).exists() for name in ('alternates','http-alternates'))
            for label,path in (('source','tools/workflow_assurance.py'),('tests','tools/test_workflow_assurance.py'),('helper',str(Path(__file__).relative_to(ROOT))),('worker',PREFIX+'worker.py')):
                assert recovered[label] == (ROOT/path).read_bytes()
            if not args.prepare_check:
                for case in CASES:
                    command = [sys.executable,'tools/test_workflow_assurance.py','--case',case]
                    capture(case+'-positive',command,0,ROOT,env,case=case)
                    mutant = private/(case+'.py'); write(mutant,recovered[case]); mutant.chmod(0o600)
                    assert stat.S_IMODE(mutant.stat().st_mode) == 0o600
                    marker = inventory['controls'][case]['assertion']
                    capture(case+'-semantic-red',[sys.executable,str(ROOT/(PREFIX+'worker.py')),'--case',case,'--source',str(mutant)],1,ROOT,env,marker=marker,case=case)
                    capture(case+'-restored',command,0,ROOT,env,case=case)
            complete = True
    finally:
        write(result_path,(json.dumps(dict(role='independent controls author',complete=complete,preparation_only=args.prepare_check,
            exercised_revision=revision,release_revision=args.release_revision,inputs=inventory,protected_before=protected,protected_after=snapshot(protected_paths),captures=records),indent=2)+'\n').encode())

if __name__ == '__main__': main()
