"""PRIVATE branch mechanics only: scripted outcomes do not implement readiness."""
import ast
import contextlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import importlib.util

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('private_fixture_branch',HERE/'foundation-fixtures.py');f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)

def main():
    text=(HERE/'foundation-fixtures.py').read_text();tree=ast.parse(text)
    calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='symlink_to'];f.require(len(calls)==1,'one exercised symlink target')
    expression=ast.Expression(calls[0].args[0]);ast.fix_missing_locations(expression)
    root=Path('/private-path-audit');target=eval(compile(expression,'typed-path-audit','eval'),{'root':root,'E':f.E})
    f.require(isinstance(target,Path) and target==root/(f.E+'api-interface.json'),'typed symlink target')
    try: root/f.E+'api-interface.json'
    except TypeError: pass
    else:f.require(False,'historical Path+str defect must reject')
    with tempfile.TemporaryDirectory(prefix='nizam118-private-branch-') as parent:
        private=Path(parent)/'repo';subprocess.run(['git','clone','-q','--shared',str(f.ROOT),str(private)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        manifest=f.read(f.ROOT,f.E+'runtime-inputs.json');interface=f.read(f.ROOT,f.E+'api-interface.json')
        for path in set(manifest['core_paths'])|set(manifest['runtime_paths'])|set(interface['historical_paths']):
            dest=private/path;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f.ROOT/path,dest)
        revision=f.git(private,'rev-parse','HEAD');candidate=f.binding(private,revision);checks=[]
        for i,item in enumerate(interface['current_cases']):
            path=f.E+'PRIVATE-branch-proof-'+str(i);raw=('COMMAND: '+item['command']+'\nREVISION: '+revision+'\nEXIT: 0\nSTDOUT:\nPRIVATE SCRIPTED FIXTURE; NOT EXECUTED QA\nSTDERR:\n').encode();f.write(private,path,raw);checks.append(dict(item,exit_code=0,evidence=path,sha256=f.sha(raw)))
        good=dict(candidate,feature='118',actor='private-scripted-actor',session_id='private-scripted-session',passed=True,checks_run=20,checks_passed=20,checks=checks)
        f.write(private,f.E+'source-candidate.json',candidate);f.write(private,f.E+'prerequisite20.json',good)
        good=f.read(private,f.E+'prerequisite20.json')
        watched=[list(good['source_sha256'])[0],f.E+'foundation-fixtures.py',list(good['historical_sha256'])[0]];saved={p:((private/p).read_bytes(),bool((private/p).stat().st_mode&0o111)) for p in watched}
        class Scripted:
            class AssuranceError(ValueError): pass
            def __init__(self):self.visits=[]
            def verify_foundation_ready(self,repo,receipt):
                n=len(self.visits)+1;repo=Path(repo);self.visits.append(n)
                f.require(1<=n<=41,'expected bounded branch visits')
                if n in (1,23):return True
                if 28<=n<=30:f.require((repo/checks[0]['evidence']).is_file(),'malformed proof branch reached')
                if n==31:f.require(not (repo/checks[0]['evidence']).exists(),'missing proof branch reached')
                if 32<=n<=40:
                    path=watched[(n-32)//3];phase=(n-32)%3;p=repo/path
                    if phase==0:f.require(p.read_bytes()!=saved[path][0],'actual input bytes mutated')
                    elif phase==1:f.require(bool(p.stat().st_mode&0o111)!=saved[path][1],'actual executable mode flipped')
                    else:f.require(p.is_symlink() and p.readlink()==repo/(f.E+'api-interface.json'),'actual typed symlink created')
                if n==41:
                    f.require(f.git(repo,'rev-parse','HEAD')!=revision,'real record-only Git advance')
                    for path,(raw,executable) in saved.items():f.require((repo/path).read_bytes()==raw and bool((repo/path).stat().st_mode&0o111)==executable,'actual restoration '+path)
                    return True
                raise self.AssuranceError('PRIVATE scripted expected rejection; no readiness judgment')
        double=Scripted();prior=f.ROOT;f.ROOT=private
        try:
            with contextlib.redirect_stdout(io.StringIO()):f.run_foundation(double)
        finally:f.ROOT=prior
        f.require(double.visits==list(range(1,42)),'full existing run_foundation branch completed')
    print('PASS PRIVATE fixture mechanics: 41 visits; malformed/missing proofs, 3 byte/mode/symlink/restoration branches, real record-only HEAD advance')
    print('PASS typed-path audit: actual symlink expression yields Path; historical Path+str rejected')
    print('LIMIT: scripted outcome double; no product readiness, actual prerequisite, QA or capture claim')

if __name__=='__main__': main()
