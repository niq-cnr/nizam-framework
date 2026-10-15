"""Independent static fixture/portable-bundle audit, no acceptance/API execution."""
import ast,copy,hashlib,json,subprocess
from pathlib import Path
root=Path.cwd();E=root/'.agent/evidence/122'
git=lambda *args:subprocess.check_output(['git',*args])
sha=lambda data:hashlib.sha256(data).hexdigest()
freeze=json.loads((E/'author4-freeze.json').read_bytes())
for ref in freeze['refs']:
    raw=git('show',ref['revision']+':'+ref['path']);row=git('ls-tree',ref['revision'],'--',ref['path']).decode().split()
    assert sha(raw)==ref['sha256'] and (root/ref['path']).read_bytes()==raw
    assert row[:3]==[ref['git_mode'],'blob',ref['git_blob']] and bool((root/ref['path']).stat().st_mode&0o111)==(row[0]=='100755')
base='d96cc8295f79bccd990041375b92e4e03a71012d'
old=ast.parse(git('show',base+':tools/test_workflow_assurance.py'));new=ast.parse((root/'tools/test_workflow_assurance.py').read_bytes())
fixture=next(n for n in new.body if isinstance(n,ast.ClassDef) and n.name=='FailureFixture')
hook=next(n for n in fixture.body if isinstance(n,ast.FunctionDef) and n.name=='commit');fixture.body.remove(hook)
assert ast.dump(new)==ast.dump(old),'Existing tests/assertions/inventories/snapshots changed'
expected=ast.parse("""def commit(self, message):
    if not getattr(self, '_fixture_housekeeping_disabled', False):
        for key, value in (('gc.auto', '0'), ('maintenance.auto', 'false')):
            git(self.root, 'config', '--local', key, value)
        self._fixture_housekeeping_disabled = True
    return super().commit(message)
""").body[0]
assert ast.dump(hook)==ast.dump(expected)
assert (root/'tools/workflow_assurance.py').read_bytes()==git('show',base+':tools/workflow_assurance.py')
assert not git('diff','--diff-filter=MD','--name-only',base,'HEAD','--','.agent/evidence/122')
inventory=json.loads((E/'controls3-identities.json').read_bytes());assert sha((E/'controls3-identities.pack').read_bytes())==inventory['pack_sha256']==freeze['pack_sha256']
assert len(inventory['objects'])==8
for label,item in inventory['objects'].items():
    raw=git('cat-file','blob',item['git_oid']);assert sha(raw)==item['sha256'] and len(raw)==item['size_bytes'] and item['type']=='blob'
    if label in ('source','tests','helper','worker'):
        path={'source':'tools/workflow_assurance.py','tests':'tools/test_workflow_assurance.py','helper':'.agent/evidence/122/controls3-run.py','worker':'.agent/evidence/122/controls3-worker.py'}[label]
        assert raw==(root/path).read_bytes()
archive=json.loads((E/'controls3-archive1-result.json').read_bytes())
assert archive['complete'] is True and archive['preparation_only'] is True and archive['protected_before']==archive['protected_after']
assert len(archive['captures'])==12 and all(c['actual_exit']==c['expected_exit']==0 and c['protected_unchanged'] for c in archive['captures'])
for capture in archive['captures']:
    assert sha((root/capture['stderr']).read_bytes())==capture['stderr_sha256']
    if capture['stdout_storage']=='portable-pack-object':
        ref=json.loads((root/capture['stdout']).read_bytes());assert ref['pack']=='.agent/evidence/122/controls3-identities.pack'
        item=ref['identity'];raw=git('cat-file','blob',item['git_oid'])
        assert sha(raw)==item['sha256']==capture['stdout_sha256'] and len(raw)==item['size_bytes']==capture['stdout_size_bytes']
    else:assert sha((root/capture['stdout']).read_bytes())==capture['stdout_sha256']
for path in ('author4-scope.execution.json','controls3-prepare-build.execution.json','controls3-prepare-archive.execution.json'):
    assert json.loads((E/path).read_bytes())['actual_exit']==0
print('STATIC_OK18refs; only7-line FailureFixture.commit addition; inherited42/all assertions/fullsnapshots unchanged; Source/priorproof preserved')
print('CONFIG_TIMING reviewed ReceiptFixture creates root before dynamic self.commit; new local gc.auto0/maintenance.autofalse runs before first supercommit')
print('ARCHIVE_COHERENCE8objects/current source,test,helper,worker; frozen freshODB12commands all0; raw/ref stdout+stderr hashes resolved; protectedsnapshot equality; APIcalls0')
