import ast,datetime,difflib,hashlib,json,os,stat,subprocess,time
from pathlib import Path
ROOT=Path('/home/cnross/workspace02/nizam-framework');OUT=Path('/home/cnross/.tmp/nizam-feature123-fresh-qa1-run');REV='d94c880b825f3f5893941f91fea46e2564903a4f';SOURCE='9886e5fadad31845349e54235820edac71c7b7fb';DRIVER=ROOT/'.agent/evidence/123/fresh-qa-capture1.py'
source=(OUT/'setup.py').read_text();tree=ast.parse(source)
required={'sha','git','write','jwrite','rawref','setup'}
module=ast.Module(body=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name in required],type_ignores=[])
assert len(module.body)==6;exec(compile(module,str(OUT/'setup.py'),'exec'))
recovery_ref=dict(path='.agent/evidence/123/root-fresh-qa-extra2-setup-recovery-release.json',revision='72605b4a977df01b4820a46215455729d1593a14')
recovery_bytes=git(ROOT,'show',recovery_ref['revision']+':'+recovery_ref['path']);recovery=json.loads(recovery_bytes);assert recovery['extra_setup_attempt']==2 and recovery['immutable_base']==REV
release=json.loads(git(ROOT,'show',REV+':.agent/evidence/123/root-fresh-qa1-release.json'));evidence=json.loads(rawref(release['evidence_ref']));packs=[json.loads(rawref(evidence['verify_selection_ref']))['capture_pack_ref'],evidence['pack_ref']]
assert sha(DRIVER.read_bytes())==release['capture_driver_ref']['sha256']
original=(OUT/'adversarial.py').read_bytes();assert sha(original)==recovery['original_failure']['script_ref']['sha256']
old=original.decode();assert old.count("out=Path('/home/cnross/.tmp/nizam-feature123-fresh-qa1-run/core')")==1
new=old.replace("out=Path('/home/cnross/.tmp/nizam-feature123-fresh-qa1-run/core')","out=Path('/home/cnross/.tmp/nizam-feature123-fresh-qa1-run/extra2')",1)
new=new.replace('from pathlib import Path\n','from pathlib import Path\nimport sys\n',1)
needle="root=Path.cwd();out=Path('/home/cnross/.tmp/nizam-feature123-fresh-qa1-run/extra2')\n"
assert new.count(needle)==1;new=new.replace(needle,needle+"sys.path.insert(0, str(root / 'tools'))\n",1)
reversed_source=new.replace("sys.path.insert(0, str(root / 'tools'))\n",'',1).replace('import sys\n','',1).replace("out=Path('/home/cnross/.tmp/nizam-feature123-fresh-qa1-run/extra2')","out=Path('/home/cnross/.tmp/nizam-feature123-fresh-qa1-run/core')",1)
assert reversed_source==old;ast.parse(new)
corrected=OUT/'adversarial2.py';write(corrected,new.encode());diff=''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='adversarial.py',tofile='adversarial2.py'));write(OUT/'adversarial2.permitted-delta.diff',diff.encode())
jwrite(OUT/'adversarial2-freeze.json',dict(recovery_release_ref=dict(recovery_ref,sha256=sha(recovery_bytes)),original_sha256=sha(original),corrected_sha256=sha(new.encode()),all_assertions_unchanged=True,only_whitelisted_delta=True,at=datetime.datetime.now(datetime.timezone.utc).isoformat(),setup_definition_reused_from='setup.py',setup_source_sha256=sha(source.encode())))
repo,directory,sentinel=setup('extra2')
argv=['python3',str(DRIVER),'--repo',str(repo),'--output',str(directory),'--name','adversarial2','--sentinel',str(sentinel),'--stdin',str(corrected),'--','python3','-']
with (directory/'adversarial2.wrapper.stdout.txt').open('xb') as stdout,(directory/'adversarial2.wrapper.stderr.txt').open('xb') as stderr:
 child=subprocess.Popen(argv,cwd=repo,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),stdout=stdout,stderr=stderr,start_new_session=True)
 jwrite(directory/'adversarial2.wrapper-started.json',dict(argv=argv,wrapper_pid=child.pid));print(json.dumps(dict(wrapper_pid=child.pid,repo=str(repo),output=str(directory),corrected_sha256=sha(new.encode()))),flush=True);rc=child.wait()
print('Corrected same extra wrapper actual exit:',rc,flush=True)
assert rc==0,rc
