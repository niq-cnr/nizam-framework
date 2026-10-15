#!/usr/bin/env python3
"""Engineering-only Root-selected input constructibility; no hosted/gate claim.

Invoke externally to the later exact clean SourceS2 checkout; capture streams
outside it. Required CLI binds actual Root preparation Ref and Source only after
Root freezes concrete arguments in a separate execution release.
"""
import argparse
import hashlib
import importlib.util
import json
import os
import re
from pathlib import Path
import signal
import stat
import subprocess
import sys
import time

BASE='40285cd344ed92bfed5345185c7d46b8c41c007b'
CHECKPOINT='d1fd767bca33f7e54486ebc8542811315fe48bde'
TREE='3b2ec9a0db8efc2b0f8fb61a87dbed88b1df46f1'
ORIGIN='https://github.com/niq-cnr/nizam-framework.git'
PINS={'tools/workflow_assurance.py':'2579b0d94598621acccc6e257408e80a0657834393a6f30be878da94967e70b8',
      'tools/workflow_assurance_ci.py':'7ab3b092188383897900b7f84af2c22156d662ebe355e25b837b250123b49905',
      'tools/test_workflow_assurance.py':'06eba273dbfd615df7f0ea3b6b52592ed208f9ec267b52a1e06996488b850f13',
      '.agent/contracts/123.json':'64afcf8dd7ad872b06aac480c5ed4fc1dbb6abdf2495256fbc646ee2782cfbd5'}
# Fixed complete537 path/category map only; no historical digest/Source/Ref reuse.
INPUTS_SHA256='61860d409625edd1bbb31667cc9580f0009cfd431fccc532f807d51fd1cf8bf1'
REPAIR_PATHS=['.agent/evidence/123/author4-checkpoint-preparation.json','tools/test_workflow_assurance.py']
LIMIT=2*1024*1024


def require(value,message):
    if not value:raise RuntimeError(message)


def git(root,*args):
    return subprocess.check_output(['git','--no-optional-locks','-C',str(root),*args],stderr=subprocess.PIPE)


def snapshot(root,source):
    require(git(root,'rev-parse','HEAD').decode().strip()==source,'Source HEAD changed')
    require(not git(root,'status','--porcelain','--untracked-files=all'),'Source checkout is not clean')
    require(not git(root,'ls-files','--others','-z'),'untracked/ignored Source contamination')
    rows={};installed=0
    for entry in git(root,'ls-tree','-rz',source).split(b'\0'):
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
    parser.add_argument('--expected-source',required=True)
    parser.add_argument('--selection-path',required=True)
    parser.add_argument('--selection-revision',required=True)
    parser.add_argument('--selection-sha256',required=True)
    args=parser.parse_args();started=time.monotonic()
    require(os.environ.get('PYTHONDONTWRITEBYTECODE')=='1','PYTHONDONTWRITEBYTECODE=1 required')
    def timeout(signum,frame):
        os.write(2,b'ENGINEERING_INPUT_TIMEOUT: 180s wall bound; preservation audit/result incomplete; no success claim\n')
        os._exit(124)
    signal.signal(signal.SIGALRM,timeout);signal.setitimer(signal.ITIMER_REAL,180)
    source=args.expected_source
    require(re.fullmatch('[0-9a-f]{40}',source) is not None,'actual full expected Source SHA required')
    require(re.fullmatch('[0-9a-f]{40}',args.selection_revision) is not None,'actual full preparation revision required')
    require(re.fullmatch('[0-9a-f]{64}',args.selection_sha256) is not None,'actual raw preparation SHA256 required')
    path=args.selection_path
    require(path.startswith('.agent/evidence/123/') and '\\' not in path and ':' not in path and all(part not in ('','.','..') for part in path.split('/')) and not any(ord(c)<32 or 127<=ord(c)<=159 for c in path),'safe actual preparation path required')
    root=Path(args.source_root);require(root.is_absolute() and not root.is_symlink(),'explicit owned Source root required')
    root=root.resolve(strict=True)
    require(not Path(__file__).resolve().is_relative_to(root),'helper must remain outside Source checkout')
    require(git(root,'rev-parse','--show-toplevel').decode().strip()==str(root),'Source must be Git toplevel')
    require(git(root,'rev-parse','--verify',source+'^{commit}').decode().strip()==source,'expected Source must be an actual exact commit')
    require(git(root,'show','-s','--format=%P',source).decode().strip()==CHECKPOINT,'SourceS2 must have exactly K as parent')
    require(git(root,'rev-parse',source+'^{tree}').decode().strip()==TREE,'SourceS2 must retain exact K tree')
    require(git(root,'diff','--name-only',BASE,source).decode().splitlines()==REPAIR_PATHS,'actual B2..Source must retain exactly both K repair paths')
    require(git(root,'remote','get-url','origin').decode().strip()==ORIGIN,'owned Source origin must be independently selected exact origin before snapshot')
    before=snapshot(root,source)
    try:
        for path,digest in PINS.items():require(before[0][path][3]==digest,'frozen Source/runner/test/contract mismatch: '+path)
        reference=dict(path=args.selection_path,revision=args.selection_revision,sha256=args.selection_sha256)
        require(git(root,'rev-parse','--verify',reference['revision']+'^{commit}').decode().strip()==reference['revision'],'actual Root preparation must name an exact commit')
        raw_size=int(git(root,'cat-file','-s',reference['revision']+':'+reference['path']))
        require(0<raw_size<=LIMIT,'preparation payload bound before allocation')
        raw=git(root,'show',reference['revision']+':'+reference['path'])
        require(len(raw)==raw_size and hashlib.sha256(raw).hexdigest()==reference['sha256'],'actual Root preparation raw size/digest mismatch')
        # Imports happen only under an explicit later Root behavioral release.
        sys.path.insert(0,str(root/'tools'))
        wa=load(root/'tools/workflow_assurance.py','wa123_engineering_input')
        cr=load(root/'tools/convergent_review.py','wa123_engineering_packet')
        proof=wa._ControlsProof(root);selection=proof.selection(reference,'capture')
        require(selection['source_commit']==source and selection['source_tree']==TREE and selection['packet_base']==BASE,'selected new Source/tree/B2 binding')
        require(hashlib.sha256(wa.canonical(selection['inputs'])).hexdigest()==INPUTS_SHA256,'complete protected537 category/path map binding')
        selected_paths=[path for category in wa.CATEGORIES for path in selection['inputs'][category]]
        require(len(selected_paths)==537 and len(set(selected_paths))==537,'exact537 unique protected paths required')
        require(sum(path.startswith('.nizam/') for path in selected_paths)==239,'protected map must include all239 installed files')
        candidate=wa.assess_repository(root,source,selection['inputs'],['PYTHONDONTWRITEBYTECODE'],{})
        proof.identity(candidate,selection['inputs']);proof.prerequisites(selection,candidate)
        proof.authority(selection);proof.shadow(selection)
        candidate_bytes=len(wa.canonical(candidate))+1
        require(candidate_bytes<=LIMIT,'local candidate exceeds retained-payload2MiB bound')
        packet=cr.build_packet_from_git(root,selection['review_repository'],'wa123-controls','ordinary',selection['packet_base'],source)
        packet_raw=cr.canonical_json_bytes(packet)
        require(packet['head_sha']==source and packet['base_sha']==selection['packet_base'],'packet exact Source/base binding')
        require(0<len(packet_raw)<=LIMIT,'packet exceeds approved2MiB retained-payload bound')
        require(packet['mode']=='ordinary' and packet['scope_commitment'] is None,'actual trusted ordinary packet only')
        require([row['path'] for row in packet['delta']]==REPAIR_PATHS and sorted(row['path'] for row in packet['review_files'])==REPAIR_PATHS,'trusted packet must retain both complete repair paths')
        require(all(row['old_digest']!=row['new_digest'] for row in packet['delta']),'actual packet must contain meaningful nonempty repair delta')
        result=dict(kind='Engineering input constructibility only; not hosted candidate, execution, review or gate approval',
            source_commit=source,source_parent=CHECKPOINT,source_tree=TREE,selection_ref=reference,selected_paths=sum(len(selection['inputs'][k]) for k in wa.CATEGORIES),
            local_candidate_sha256=candidate['identity_sha256'],local_candidate_bytes=candidate_bytes,
            observed_local_environment=candidate['environment'],packet_base=packet['base_sha'],packet_head=packet['head_sha'],
            packet_bytes=len(packet_raw),packet_sha256=hashlib.sha256(packet_raw).hexdigest(),packet_changed_paths=len(packet['delta']))
    finally:
        after=snapshot(root,source);require(after==before,'tracked Source full bytes/modes/nlinks/origin changed')
    signal.setitimer(signal.ITIMER_REAL,0)
    result.update(preserved_tracked_paths=len(before[0]),preserved_installed_files=239,snapshot_sha256=summary_hash(before),
        wall_limit_seconds=180,elapsed_seconds=time.monotonic()-started)
    print(json.dumps(result,sort_keys=True),flush=True)


if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('ENGINEERING_INPUT_FAILURE: '+type(exc).__name__+': '+str(exc)[:1000],file=sys.stderr,flush=True)
        raise SystemExit(1)
