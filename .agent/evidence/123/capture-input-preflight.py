#!/usr/bin/env python3
"""Engineering-only Root-selected input constructibility; no hosted/gate claim.

Invoke externally to a new clean owned Source059f checkout; capture streams
outside it. Root supplies the exact draft Ref and authorizes execution later.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import stat
import subprocess
import sys
import time

SOURCE='059f12dfe8e3827ebe0d10af27d79c08fb9fd98c'
PINS={'tools/workflow_assurance.py':'2579b0d94598621acccc6e257408e80a0657834393a6f30be878da94967e70b8',
      'tools/workflow_assurance_ci.py':'7ab3b092188383897900b7f84af2c22156d662ebe355e25b837b250123b49905',
      'tools/test_workflow_assurance.py':'9bafd83bb18933bf103930d461fe681e42804f45ec7cdd065d74a7ffb5c75d00',
      '.agent/contracts/123.json':'64afcf8dd7ad872b06aac480c5ed4fc1dbb6abdf2495256fbc646ee2782cfbd5'}
SELECTION_REF={'path': '.agent/evidence/123/capture-selection-preparation2.json', 'revision': '349181f3186d853c88ab36702f9930dd670c05c9', 'sha256': '5584220b1b5e038bda1169cc14cea4bb2a526494a98af31b2618e9fcabb93de9'}
LIMIT=2*1024*1024


def require(value,message):
    if not value:raise RuntimeError(message)


def git(root,*args):
    return subprocess.check_output(['git','--no-optional-locks','-C',str(root),*args],stderr=subprocess.PIPE)


def snapshot(root):
    require(git(root,'rev-parse','HEAD').decode().strip()==SOURCE,'Source HEAD changed')
    require(not git(root,'status','--porcelain','--untracked-files=all'),'Source checkout is not clean')
    require(not git(root,'ls-files','--others','-z'),'untracked/ignored Source contamination')
    rows={};installed=0
    for entry in git(root,'ls-tree','-rz',SOURCE).split(b'\0'):
        if not entry:continue
        metadata,name=entry.split(b'\t',1);mode,kind,oid=metadata.decode().split();path=name.decode()
        require(kind=='blob' and mode in ('100644','100755'),'unsupported Source tree mode')
        target=root
        for part in path.split('/'):
            target=target/part;require(not target.is_symlink(),'Source component symlink')
        state=target.lstat();require(stat.S_ISREG(state.st_mode) and state.st_nlink==1,'Source regular/single-link invariant')
        data=target.read_bytes();require(bool(state.st_mode&0o111)==(mode=='100755'),'Source executable drift')
        require(hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==oid,'Source immutable bytes drift')
        rows[path]=(state.st_mode,state.st_nlink,len(data),hashlib.sha256(data).hexdigest())
        installed+=path.startswith('.nizam/')
    require(installed==239,'installed inventory count changed')
    return rows,git(root,'remote','get-url','origin')


def summary_hash(snapshot_value):
    digest=hashlib.sha256()
    for path,value in sorted(snapshot_value[0].items()):digest.update(json.dumps([path,value],separators=(',',':')).encode()+b'\n')
    digest.update(snapshot_value[1]);return digest.hexdigest()


def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec)
    sys.modules[name]=module;spec.loader.exec_module(module);return module


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root',required=True)
    parser.add_argument('--selection-path',required=True)
    parser.add_argument('--selection-revision',required=True)
    parser.add_argument('--selection-sha256',required=True)
    args=parser.parse_args();started=time.monotonic()
    require(os.environ.get('PYTHONDONTWRITEBYTECODE')=='1','PYTHONDONTWRITEBYTECODE=1 required')
    def timeout(signum,frame):
        os.write(2,b'ENGINEERING_INPUT_TIMEOUT: 180s wall bound; preservation audit/result incomplete; no success claim\n')
        os._exit(124)
    signal.signal(signal.SIGALRM,timeout);signal.setitimer(signal.ITIMER_REAL,180)
    root=Path(args.source_root);require(root.is_absolute() and not root.is_symlink(),'explicit owned Source root required')
    root=root.resolve(strict=True)
    require(not Path(__file__).resolve().is_relative_to(root),'helper must remain outside Source checkout')
    require(git(root,'rev-parse','--show-toplevel').decode().strip()==str(root),'Source must be Git toplevel')
    before=snapshot(root)
    try:
        for path,digest in PINS.items():require(before[0][path][3]==digest,'frozen Source/runner/test/contract mismatch: '+path)
        reference=dict(path=args.selection_path,revision=args.selection_revision,sha256=args.selection_sha256)
        require(reference==SELECTION_REF,'exact Root-selected preparation2 Ref required')
        # Imports happen only under an explicit later Root behavioral release.
        sys.path.insert(0,str(root/'tools'))
        wa=load(root/'tools/workflow_assurance.py','wa123_engineering_input')
        cr=load(root/'tools/convergent_review.py','wa123_engineering_packet')
        proof=wa._ControlsProof(root);selection=proof.selection(reference,'capture')
        require(selection['source_commit']==SOURCE and selection['source_tree']==git(root,'rev-parse',SOURCE+'^{tree}').decode().strip(),'selected Source/tree binding')
        candidate=wa.assess_repository(root,SOURCE,selection['inputs'],['PYTHONDONTWRITEBYTECODE'],{})
        proof.identity(candidate,selection['inputs']);proof.prerequisites(selection,candidate)
        proof.authority(selection);proof.shadow(selection)
        packet=cr.build_packet_from_git(root,selection['review_repository'],'wa123-controls','ordinary',selection['packet_base'],SOURCE)
        packet_raw=cr.canonical_json_bytes(packet)
        require(packet['head_sha']==SOURCE and packet['base_sha']==selection['packet_base'],'packet exact Source/base binding')
        require(len(packet_raw)<=LIMIT,'packet exceeds approved2MiB retained-payload bound')
        result=dict(kind='Engineering input constructibility only; not hosted candidate, execution, review or gate approval',
            source_commit=SOURCE,selection_ref=reference,selected_paths=sum(len(selection['inputs'][k]) for k in wa.CATEGORIES),
            local_candidate_sha256=candidate['identity_sha256'],local_candidate_bytes=len(wa.canonical(candidate))+1,
            observed_local_environment=candidate['environment'],packet_base=packet['base_sha'],packet_head=packet['head_sha'],
            packet_bytes=len(packet_raw),packet_sha256=hashlib.sha256(packet_raw).hexdigest(),packet_changed_paths=len(packet['delta']))
    finally:
        after=snapshot(root);require(after==before,'tracked Source full bytes/modes/nlinks/origin changed')
    signal.setitimer(signal.ITIMER_REAL,0)
    result.update(preserved_tracked_paths=len(before[0]),preserved_installed_files=239,snapshot_sha256=summary_hash(before),
        wall_limit_seconds=180,elapsed_seconds=time.monotonic()-started)
    print(json.dumps(result,sort_keys=True),flush=True)


if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('ENGINEERING_INPUT_FAILURE: '+type(exc).__name__+': '+str(exc)[:1000],file=sys.stderr,flush=True)
        raise SystemExit(1)
