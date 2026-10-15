"""Independent empty-ODB archive restoration and append-only preservation proof."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
ROOT=Path(__file__).resolve().parents[3];PREFIX=ROOT/'.agent/evidence/120/identity-archive-review1-'
SEAL_REV='0edf4c64496e145d4b936292d72e6f14827ce845';BEFORE='faee538eee21421791eb49b1e9f03e132dfd8809';PACK='.agent/evidence/120/retained-identities.pack'
GIT=shutil.which('git');assert GIT;GIT=str(Path(GIT).resolve());records=[]
def write(suffix,value):Path(str(PREFIX)+suffix).write_text(json.dumps(value,indent=2)+'\n')
def source(*args):return subprocess.check_output([GIT,'-C',str(ROOT),*args])
def git_oid(data):return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
def preserved():
    paths=['tools/workflow_assurance.py','tools/test_workflow_assurance.py','tools/README.md','CHANGELOG.md','schema','.nizam','.agent/contracts/120.json','.agent/qa/120.json','.agent/evidence/120']
    def tree(revision):
        result={}
        for item in source('ls-tree','-rz',revision,'--',*paths).split(b'\0'):
            if not item:continue
            meta,path=item.split(b'\t',1);mode,kind,oid=meta.decode().split();result[path.decode()]=(mode,kind,oid)
        return result
    old,current=tree(BEFORE),tree('HEAD');rows={}
    for path,row in old.items():
        assert current.get(path)==row,path
        mode,kind,oid=row;target=ROOT/path;assert kind=='blob' and mode in ('100644','100755') and not target.is_symlink(),path
        data=target.read_bytes();assert git_oid(data)==oid and bool(target.stat().st_mode&0o111)==(mode=='100755'),path
        rows[path]={'git_blob':oid,'sha256':hashlib.sha256(data).hexdigest(),'mode':mode}
    assert len([p for p in rows if p.startswith('.nizam/')])==239
    return rows
revision=source('rev-parse','HEAD').decode().strip();before=preserved()
seal_bytes=source('show',SEAL_REV+':.agent/evidence/120/executable-review1-seal.json')
assert (ROOT/'.agent/evidence/120/executable-review1-seal.json').read_bytes()==seal_bytes
seal=json.loads(seal_bytes);objects=seal['identity_objects'];assert len(objects)==17
pack=(ROOT/PACK).read_bytes();assert pack==source('show','778fa42290ceeab3097fe4156c82211928b99a69:'+PACK)
assert len(pack)==48005 and hashlib.sha256(pack).hexdigest()=='fa3c700f3cadfb9859e1eab70cd9f6a00c75e12d13c469e44f01ce95e79ae256'
with tempfile.TemporaryDirectory(prefix='nizam120-identity-review1-',dir='/home/cnross/.tmp') as scratch_name:
    scratch=Path(scratch_name);bare=scratch/'empty.git';home=scratch/'home';home.mkdir()
    env={'PATH':os.defpath,'HOME':str(home),'GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_SYSTEM':'/dev/null','GIT_CONFIG_GLOBAL':'/dev/null','GIT_TERMINAL_PROMPT':'0','LC_ALL':'C'}
    def command(name,args,data=None,expected=0,raw=True):
        argv=[GIT,*args];p=subprocess.run(argv,cwd=scratch,env=env,input=data,capture_output=True,timeout=30)
        row={'name':name,'argv':argv,'cwd':str(scratch),'environment':env,'exit_code':p.returncode,'expected_exit_code':expected,'stdout_bytes':len(p.stdout),'stdout_sha256':hashlib.sha256(p.stdout).hexdigest(),'stderr':p.stderr.decode(errors='replace')}
        records.append(row)
        if raw:
            Path(str(PREFIX)+name+'.stdout.txt').write_bytes(p.stdout);Path(str(PREFIX)+name+'.stderr.txt').write_bytes(p.stderr)
        write('commands.json',records);assert p.returncode==expected,row
        return p.stdout
    command('init',['init','--bare','--template=',str(bare)])
    assert not (bare/'objects/info/alternates').exists() and not (bare/'objects/info/http-alternates').exists()
    empty=command('empty-inventory',['--git-dir',str(bare),'cat-file','--batch-all-objects','--batch-check'])
    assert empty==b''
    ids=('\n'.join(objects)+'\n').encode()
    missing=command('absent-before',['--git-dir',str(bare),'cat-file','--batch-check'],ids)
    assert missing.decode().splitlines()==[oid+' missing' for oid in objects]
    command('import',['--git-dir',str(bare),'index-pack','--stdin','--strict'],pack)
    inventory=command('restored-inventory',['--git-dir',str(bare),'cat-file','--batch-all-objects','--batch-check'])
    rows={parts[0]:(parts[1],int(parts[2])) for parts in (line.split() for line in inventory.decode().splitlines())}
    assert set(rows)==set(objects)
    observed={}
    for oid,expected in objects.items():
        assert rows[oid]==(expected['type'],expected['size_bytes']) and expected['type']=='blob'
        data=command('blob-'+oid,['--git-dir',str(bare),'cat-file','blob',oid],raw=False)
        assert len(data)==expected['size_bytes'] and hashlib.sha256(data).hexdigest()==expected['sha256'] and git_oid(data)==oid
        observed[oid]={'type':'blob','size_bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'git_oid':git_oid(data),'actual_exit_code':0}
        print('VERIFIED',oid,'blob',len(data),observed[oid]['sha256'],flush=True)
    assert not (bare/'objects/info/alternates').exists() and not (bare/'objects/info/http-alternates').exists()
    fresh_info={'bare_root':str(bare),'empty_before':True,'missing_before':17,'restored_exactly':17,'alternate_files_absent':True,'environment_object_or_alternate_overrides_absent':True,'source_object_database_never_mounted_or_linked':True,'owned_temporary_root':str(scratch)}
    assert scratch.parent==Path('/home/cnross/.tmp') and scratch.name.startswith('nizam120-identity-review1-')
assert not scratch.exists()
after=preserved();assert after==before
write('result.json',{'reviewer':'/root/qa119','exercised_revision':revision,'actual_exit_code':0,'seal_revision':SEAL_REV,'seal_sha256':hashlib.sha256(seal_bytes).hexdigest(),'archive_path':PACK,'archive_sha256':hashlib.sha256(pack).hexdigest(),'archive_bytes':len(pack),'fresh_database':fresh_info,'verified_objects':observed,'preservation_baseline':BEFORE,'preserved_existing_files':len(before),'preserved_existing_files_manifest_sha256':hashlib.sha256(json.dumps(before,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'installed_files':239,'all_original_paths_objects_bytes_modes_unchanged':True,'runtime_bank_rerun':False,'commands':'.agent/evidence/120/identity-archive-review1-commands.json'})
print('PASS independent exact17 archive restore in empty no-alternate ODB; existing proof/Source/test/schema/installed bytes+modes unchanged')
