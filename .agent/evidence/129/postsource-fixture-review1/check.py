import ast,gzip,hashlib,json,subprocess
from pathlib import Path
root=Path.cwd();area=root/'.agent/evidence/129/implementation2/public-validation1'
sha=lambda raw:hashlib.sha256(raw).hexdigest()
source2=subprocess.check_output(['git','show','2e8c92d11c36525c3b73b8cfb23822c4507835cb:tools/runtime_session.py'])
baseline=(root/'tools/runtime_session.py').read_bytes();runner=(root/'tools/test_runtime_session.py').read_bytes()
assert sha(baseline)=='fe5917389ee3bdec342bd440d7ce48adf7d7e933cb4cf3f4dc1d1bbb1cecb345'
assert sha(source2)=='aae6a5cbe09435e39c29153469a9ca13f45065e6248ff70ca44f6ce9bc5d8fa5'
assert sha(runner)=='81a7299120ad79cca1765e6c4c47f0d8907bfa6e593804a9ffd97210700dffe4'
guard=b'insist(release.is_absolute() and release.resolve().is_relative_to(self.root))'
assert guard in baseline and guard in source2
assert b"release = stub.home / 'release-stub'" in runner and b"self.state = self.home / 'state'" in runner
tree=ast.parse(runner);function=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='LiveSession')
assert "'--root', str(self.state)" in ast.get_source_segment(runner.decode(),function)
frame=json.loads((area/'admission.execution.json').read_bytes())
assert frame['actual_exit']==2 and frame['child_pid']==3726996 and not frame['timed_out']
for key in ('stdout','stderr'):
    data=(area/Path(frame[key]['path']).name).read_bytes()
    assert len(data)==frame[key]['bytes'] and sha(data)==frame[key]['sha256']
lines=(area/'admission.stdout.txt').read_text().splitlines()
commands=[json.loads(line.removeprefix('LIVE_COMMAND ')) for line in lines if line.startswith('LIVE_COMMAND ')]
failed=next(row for row in commands if row['pid']==3731082)
assert failed['exit']==64 and json.loads(failed['stdout'])=={'ok':False,'error':'usage'}
requests=[json.loads(line.removeprefix('LIVE_REQUEST ')) for line in lines if line.startswith('LIVE_REQUEST ')]
request=next(row['request'] for row in requests if row['action']=='submit-operation' and row['request']['operation_id']=='op-10' and 'release-stub' in row['request']['payload']['expression'])
release=Path(json.loads(request['payload']['expression'])['release_path']);cli_root=Path(failed['argv'][failed['argv'].index('--root')+1])
assert release.is_absolute() and not release.is_relative_to(cli_root) and release.parent==cli_root.parent
before=gzip.decompress((area/'admission.preservation-before.json.gz').read_bytes())
assert before==gzip.decompress((area/'admission.preservation-after.json.gz').read_bytes())
rows={row['path']:row for row in json.loads(before)['rows']}
assert rows['tools/runtime_session.py']['sha256']==sha(source2) and rows['tools/test_runtime_session.py']['sha256']==sha(runner)
print('CONFIRMED fixture sibling release path outside actual CLI state root; original/current containment guard identical; actual submit3731082=64usage/selector3726996=2; Source2/runner bound to unchanged physical inventory. Static diagnosis only; no runtime/test/product execution.')
