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
PREFIX = '.agent/evidence/122/controls1-'
SOURCE = 'e4d17fb258bbcf19d1b6c7011661368dbe196323c4bb1f94af6540296d204e46'
TEST = '8b0b8f2d3e2bea397eaf8b9bc6761aaedd38ba3bcdc5f47d7b62e0bec9938fa4'
CONTRACT = '13dc45d0daf41fc9af4828ec0b84b1a05ded39f51b2e1fc5b903831e557d42c5'
CASES = ('infrastructure-failed','semantic-failed','reject-cause-relabel','counter-continuity')
def sha(data): return hashlib.sha256(data).hexdigest()
def identity(data): return dict(git_oid=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest(),sha256=sha(data),size_bytes=len(data),type='blob')
def write(path, data):
    with Path(path).open('xb') as handle: handle.write(data)
def git(*args): return subprocess.check_output(['git','-C',str(ROOT),*args],stderr=subprocess.PIPE).decode().strip()
def snapshot(paths):
    values = {}
    for path in paths:
        target = ROOT/path
        values[path] = dict(mode=stat.S_IMODE(target.lstat().st_mode), kind='symlink' if target.is_symlink() else 'file',
            sha256=sha(os.readlink(target).encode()) if target.is_symlink() else sha(target.read_bytes()))
    return values

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
    protected = snapshot(sorted(paths)); records = []; complete = False
    prefix = ROOT/(PREFIX+args.run_id); result_path = str(prefix)+'-result.json'; assert not Path(result_path).exists()
    revision = git('rev-parse','HEAD')
    def capture(label,argv,expected,cwd,env,data=None,marker=None,case=None):
        assert snapshot(protected) == protected
        result = subprocess.run(argv,cwd=cwd,env=env,input=data,capture_output=True)
        out = str(prefix)+'-'+label+'.stdout'; err = str(prefix)+'-'+label+'.stderr'
        write(out,result.stdout); write(err,result.stderr)
        row = dict(label=label,argv=argv,cwd=str(cwd),environment=env,exercised_revision=revision,release_revision=args.release_revision,
            actual_exit=result.returncode,expected_exit=expected,expected_assertion=marker,stdout=str(Path(out).relative_to(ROOT)),stderr=str(Path(err).relative_to(ROOT)),
            stdout_sha256=sha(result.stdout),stderr_sha256=sha(result.stderr),protected_unchanged=snapshot(protected)==protected)
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
        with tempfile.TemporaryDirectory(prefix='nizam122-controls1-') as directory:
            private = Path(directory); home = private/'home'; home.mkdir(); bare = private/'empty.git'
            env = dict(PATH=os.defpath,HOME=str(home),LC_ALL='C',PYTHONDONTWRITEBYTECODE='1',GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL='/dev/null',GIT_CONFIG_SYSTEM='/dev/null')
            capture('archive-init',['git','init','--bare','--template=',str(bare)],0,private,env)
            def archive(label,*argv,data=None): return capture(label,['git','--git-dir',str(bare),*argv],0,private,env,data)
            assert archive('archive-empty','cat-file','--batch-all-objects','--batch-check') == b''
            assert not (bare/'objects/info/alternates').exists()
            archive('archive-import','index-pack','--stdin','--strict',data=pack)
            rows = archive('archive-inventory','cat-file','--batch-all-objects','--batch-check').decode().splitlines()
            assert {r.split()[0] for r in rows} == {v['git_oid'] for v in inventory['objects'].values()}
            recovered = {}
            for label,expected in inventory['objects'].items():
                recovered[label] = archive('archive-blob-'+label,'cat-file','blob',expected['git_oid'])
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
            exercised_revision=revision,release_revision=args.release_revision,inputs=inventory,protected_before=protected,protected_after=snapshot(protected),captures=records),indent=2)+'\n').encode())

if __name__ == '__main__': main()
