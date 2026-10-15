#!/usr/bin/env python3
"""Root transport normalization only; never a gate or provenance verdict.

Extract exact archive members, let Root commit them, then normalize metadata
using that immutable transport revision. No Git writes or external API calls.
"""
import argparse
import hashlib
import io
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import zipfile

MIB=1024*1024
REPOSITORY='niq-cnr/nizam-framework'
KINDS=('run','jobs','artifacts','job-log','archive')


def require(value,message):
    if not value:raise ValueError(message)


def positive(value,label):
    require(type(value) is int and value>0,label+' positive integer')
    return value


def hex_value(value,length,label):
    require(type(value) is str and re.fullmatch('[0-9a-f]{'+str(length)+'}',value),label+' exact hex')
    return value


def path_value(value):
    require(type(value) is str and value and not any(ord(c)<32 or ord(c)==127 for c in value),'safe path text')
    parsed=PurePosixPath(value)
    require(not parsed.is_absolute() and str(parsed)==value and all(p not in ('.','..') for p in parsed.parts),'safe relative path')
    return value


def closed(value,keys,label):
    require(type(value) is dict and set(value)==set(keys.split()),label+' closed keys')
    return value


def encoded(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()+b'\n'


def decoded(raw,canonical=False):
    def pairs(rows):
        out={}
        for k,v in rows:
            require(k not in out,'duplicate JSON key');out[k]=v
        return out
    def constant(value):raise ValueError('nonfinite JSON constant '+value)
    def number(text):
        value=float(text);require(math.isfinite(value),'nonfinite JSON number');return value
    value=json.loads(raw,object_pairs_hook=pairs,parse_constant=constant,parse_float=number)
    if canonical:require(encoded(value)==raw,'canonical JSON bytes required')
    return value


def digest(raw):return hashlib.sha256(raw).hexdigest()


class GitBytes:
    def __init__(self,root):self.root=root;self.commits=set()
    def git(self,*args):
        return subprocess.check_output(['git','--no-optional-locks','-C',str(self.root),*args],stderr=subprocess.PIPE)
    def commit(self,revision):
        hex_value(revision,40,'Git revision')
        if revision not in self.commits:
            require(self.git('rev-parse','--verify',revision+'^{commit}').decode().strip()==revision,'actual immutable commit')
            self.commits.add(revision)
        return revision
    def read(self,revision,path,maximum):
        self.commit(revision);path_value(path)
        rows=self.git('--literal-pathspecs','ls-tree','-z',revision,'--',path).split(b'\0')
        require(len(rows)==2 and not rows[1],'missing/duplicate immutable path')
        metadata,name=rows[0].split(b'\t',1);mode,kind,oid=metadata.decode().split()
        require(name.decode()==path and kind=='blob' and mode in ('100644','100755'),'regular immutable blob required')
        size=int(self.git('cat-file','-s',oid));require(0<=size<=maximum,'Git payload bound before allocation')
        raw=self.git('cat-file','blob',oid);require(len(raw)==size,'Git blob actual size')
        return raw
    def reference(self,revision,path,raw):return dict(path=path,revision=revision,sha256=digest(raw))


def reference_shape(value):
    closed(value,'path revision sha256','Ref');path_value(value['path'])
    hex_value(value['revision'],40,'Ref revision');hex_value(value['sha256'],64,'Ref digest')


def archive_entries(raw):
    require(len(raw)<=32*MIB,'archive bound')
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        infos=archive.infolist();expected={'proof.bundle':16*MIB,'manifest.json':2*MIB,'invocation.json':2*MIB}
        require(len(infos)==3 and {i.filename for i in infos}==set(expected),'ZIP exact unique three names')
        require(sum(i.file_size for i in infos)<=20*MIB,'ZIP total decompression bound')
        for info in infos:
            require(not info.is_dir() and not info.flag_bits&1 and stat.S_IFMT(info.external_attr>>16) in (0,stat.S_IFREG),'ZIP regular nonencrypted entry')
            require(0<=info.file_size<=expected[info.filename],'ZIP entry bound before decompression')
        result={}
        for info in infos:
            with archive.open(info) as stream:entry=stream.read(expected[info.filename]+1)
            require(len(entry)==info.file_size and len(entry)<=expected[info.filename],'ZIP exact decompressed size')
            result[info.filename]=entry
    return result


def facts(reader,mode,operation,fetch_revision):
    prefix='.agent/evidence/123/hosted-'+mode+str(operation)+'-fetch'
    raw=reader.read(fetch_revision,prefix+'.execution.json',2*MIB);record=decoded(raw)
    closed(record,'role mode operation_attempt records boundary','fetch execution')
    require(record['role']=='Root transport' and record['mode']==mode and type(record['operation_attempt']) is int and record['operation_attempt']==operation,'selected fetch operation binding')
    require(type(record['records']) is list and len(record['records'])==5,'five complete fetch records')
    outputs={};fetches=[];frames=[]
    for kind,row,bound in zip(KINDS,record['records'],(2,2,2,16,32)):
        closed(row,'kind argv cwd revision actual_exit started_at finished_at stdout_path stderr_path stdout_bytes stdout_sha256 stderr_sha256 within_size_bound','raw Fetch frame')
        require(row['kind']==kind and type(row['actual_exit']) is int and row['actual_exit']==0 and row['within_size_bound'] is True,'actual ordered fetch exit/bound')
        require(type(row['cwd']) is str and Path(row['cwd']).is_absolute() and '\0' not in row['cwd'],'actual Fetch cwd')
        require(all(type(row[k]) is str and row[k] for k in ('started_at','finished_at')),'actual fetch timestamps')
        reader.commit(row['revision']);reader.git('merge-base','--is-ancestor',row['revision'],fetch_revision)
        require(row['stdout_path']==prefix+'-'+kind+'.stdout' and row['stderr_path']==prefix+'-'+kind+'.stderr','exact fetch capture paths')
        stdout=reader.read(fetch_revision,row['stdout_path'],bound*MIB);stderr=reader.read(fetch_revision,row['stderr_path'],2*MIB)
        require(type(row['stdout_bytes']) is int and row['stdout_bytes']==len(stdout),'actual fetched byte count')
        require(row['stdout_sha256']==digest(stdout) and row['stderr_sha256']==digest(stderr),'actual raw fetch digests')
        outputs[kind]=stdout;frames.append(row)
        fetches.append(dict(kind=kind,argv=row['argv'],cwd=row['cwd'],revision=row['revision'],actual_exit=row['actual_exit'],
            stdout=reader.reference(fetch_revision,row['stdout_path'],stdout),stderr=reader.reference(fetch_revision,row['stderr_path'],stderr)))
    require(len({(r['cwd'],r['revision']) for r in frames})==1,'single actual fetch execution frame')
    entries=archive_entries(outputs['archive']);manifest=decoded(entries['manifest.json'],True);invocation=decoded(entries['invocation.json'],True)
    closed(manifest,'schema_version mode source_commit output_tip bundle_sha256 bundle_size inventory','manifest')
    closed(invocation,'schema_version mode producer selection_ref source_commit checkout environment argv cwd output_tip bundle_sha256 manifest_sha256 result_refs actual_exit','Invocation')
    for value in (manifest,invocation):
        require(type(value['schema_version']) is int and value['schema_version']==1 and value['mode']==mode,'actual archive schema/mode')
        hex_value(value['source_commit'],40,'actual Source');hex_value(value['output_tip'],40,'actual output tip')
    require(type(invocation['actual_exit']) is int and invocation['actual_exit']==0,'actual Invocation exit')
    require(type(manifest['bundle_size']) is int and manifest['bundle_size']==len(entries['proof.bundle']),'manifest bundle byte count')
    require(manifest['bundle_sha256']==digest(entries['proof.bundle'])==invocation['bundle_sha256'],'actual bundle hash binding')
    require(invocation['manifest_sha256']==digest(entries['manifest.json']) and invocation['source_commit']==manifest['source_commit'] and invocation['output_tip']==manifest['output_tip'],'Invocation manifest/source/tip binding')
    producer=closed(invocation['producer'],'agent_id session_id','producer')
    require(producer==dict(agent_id='wa123-capable-ci',session_id='123-ci-'+mode+'-attempt'+str(operation)),'actual allocated producer binding')
    reference_shape(invocation['selection_ref'])
    markers=re.findall(r'WA123_INVOCATION=(\{[^\r\n]*\})$',outputs['job-log'].decode('utf8'),re.M)
    require(len(markers)==1 and markers[0].encode()+b'\n'==entries['invocation.json'],'unique actual job-log Invocation bytes')
    run=decoded(outputs['run']);jobs=decoded(outputs['jobs']);artifacts=decoded(outputs['artifacts'])
    require(type(run) is dict and type(run.get('repository')) is dict and run['repository'].get('full_name')==REPOSITORY,'actual run repository')
    run_id=positive(run.get('id'),'run id');attempt=positive(run.get('run_attempt'),'run attempt')
    checkout=closed(invocation['checkout'],'sha tree event event_head event_base parents','Invocation checkout')
    for key in ('sha','tree','event_head'):hex_value(checkout[key],40,'Invocation checkout '+key)
    require(checkout['event'] in ('push','pull_request') and run.get('event')==checkout['event'] and run.get('head_sha')==checkout['event_head'],'actual run/Invocation event head binding')
    require(type(jobs) is dict and type(jobs.get('total_count')) is int and jobs['total_count']==5 and type(jobs.get('jobs')) is list and len(jobs['jobs'])==5,'actual complete five-job response')
    require({j.get('name') for j in jobs['jobs']}=={'validate','e2e_bootstrap','fixtures_self_test','convergent_review','self_governance'},'actual five job names')
    ids=[]
    for job in jobs['jobs']:
        ids.append(positive(job.get('id'),'job id'))
        require(job.get('run_id')==run_id and type(job.get('run_id')) is int and job.get('run_attempt')==attempt and type(job.get('run_attempt')) is int and job.get('head_sha')==run['head_sha'],'actual job run/attempt/head binding')
    require(len(set(ids))==5,'unique actual job IDs')
    job=next(j for j in jobs['jobs'] if j['name']=='convergent_review');job_id=job['id']
    require(type(artifacts) is dict and type(artifacts.get('total_count')) is int and 1<=artifacts['total_count']<=100 and type(artifacts.get('artifacts')) is list and len(artifacts['artifacts'])==artifacts['total_count'],'complete bounded artifact response')
    argv=frames[4]['argv'];require(type(argv) is list and len(argv)==3,'actual archive fetch argv')
    match=re.fullmatch('repos/'+REPOSITORY+r'/actions/artifacts/([1-9][0-9]*)/zip',argv[2]);require(match is not None,'actual archive endpoint ID')
    artifact_id=int(match[1]);artifact_name='wa123-'+mode+'-'+producer['session_id']
    selected=[a for a in artifacts['artifacts'] if a.get('id')==artifact_id or a.get('name')==artifact_name]
    require(len(selected)==1,'unique selected actual artifact')
    artifact=selected[0];require(type(artifact.get('id')) is int and artifact['id']==artifact_id and artifact.get('name')==artifact_name and artifact.get('expired') is False,'actual artifact ID/name/expiry')
    require(type(artifact.get('size_in_bytes')) is int and artifact['size_in_bytes']==len(outputs['archive']),'actual archive size binding')
    expected=[['gh','api',f'repos/{REPOSITORY}/actions/runs/{run_id}'],
        ['gh','api',f'repos/{REPOSITORY}/actions/runs/{run_id}/attempts/{attempt}/jobs?per_page=100'],
        ['gh','api',f'repos/{REPOSITORY}/actions/runs/{run_id}/artifacts?per_page=100'],
        ['gh','run','view',str(run_id),'--repo',REPOSITORY,'--job',str(job_id),'--log'],
        ['gh','api',f'repos/{REPOSITORY}/actions/artifacts/{artifact_id}/zip']]
    require([r['argv'] for r in frames]==expected,'actual five Fetch argv/IDs binding')
    return dict(entries=entries,invocation=invocation,fetches=fetches,run_id=run_id,attempt=attempt,job_id=job_id,
        artifact_id=artifact_id,artifact_name=artifact_name,archive_sha256=digest(outputs['archive']))


def exclusive(root,path,raw):
    path_value(path);parts=path.split('/');fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY)
    try:
        for part in parts[:-1]:
            try:os.mkdir(part,mode=0o700,dir_fd=fd)
            except FileExistsError:pass
            child=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd);os.close(fd);fd=child
        target=os.open(parts[-1],os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=fd)
        with os.fdopen(target,'wb') as stream:
            require(stat.S_ISREG(os.fstat(stream.fileno()).st_mode) and os.fstat(stream.fileno()).st_nlink==1,'owned new regular file')
            stream.write(raw)
    finally:os.close(fd)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('stage',choices=('extract','metadata'))
    parser.add_argument('--mode',required=True,choices=('capture','verify'));parser.add_argument('--operation-attempt',required=True,type=int,choices=(1,2,3))
    parser.add_argument('--fetch-revision',required=True);parser.add_argument('--transport-revision')
    args=parser.parse_args()
    require((args.stage=='metadata')==(args.transport_revision is not None),'transport revision only and required for metadata stage')
    root=Path.cwd().resolve(strict=True);reader=GitBytes(root)
    require(reader.git('rev-parse','--show-toplevel').decode().strip()==str(root),'owned Git toplevel required')
    observed=facts(reader,args.mode,args.operation_attempt,args.fetch_revision)
    prefix='.agent/evidence/123/hosted-'+args.mode+str(args.operation_attempt)+'-transport/'
    report=dict(kind='Root transport normalization only; no gate or provenance verdict',stage=args.stage,mode=args.mode,
        operation_attempt=args.operation_attempt,fetch_revision=args.fetch_revision,source_commit=observed['invocation']['source_commit'],
        run_id=observed['run_id'],attempt=observed['attempt'],job_id=observed['job_id'],artifact_id=observed['artifact_id'],archive_sha256=observed['archive_sha256'])
    if args.stage=='extract':
        require(not (root/prefix).exists() and not (root/prefix).is_symlink(),'new mode-attempt transport directory required')
        for name,raw in observed['entries'].items():exclusive(root,prefix+name,raw)
        report['entries']=[dict(path=prefix+name,sha256=digest(raw),bytes=len(raw)) for name,raw in observed['entries'].items()]
        report['commit_boundary']='Root must commit exact extracted bytes before metadata; no future revision claimed'
    else:
        reader.commit(args.transport_revision);reader.git('merge-base','--is-ancestor',args.fetch_revision,args.transport_revision)
        entry_refs={}
        for name,raw in observed['entries'].items():
            actual=reader.read(args.transport_revision,prefix+name,16*MIB if name=='proof.bundle' else 2*MIB)
            require(actual==raw,'committed transport bytes differ from exact downloaded archive')
            entry_refs[name]=reader.reference(args.transport_revision,prefix+name,actual)
        invocation=observed['invocation']
        metadata=dict(schema_version=1,mode=args.mode,source_commit=invocation['source_commit'],producer=invocation['producer'],
            selection_ref=invocation['selection_ref'],invocation_ref=entry_refs['invocation.json'],run_id=observed['run_id'],attempt=observed['attempt'],
            job_id=observed['job_id'],artifact_id=observed['artifact_id'],artifact_name=observed['artifact_name'],archive_ref=observed['fetches'][4]['stdout'],fetches=observed['fetches'])
        raw=encoded(metadata);require(len(raw)<=2*MIB,'metadata payload bound');exclusive(root,prefix+'metadata.json',raw)
        report.update(metadata_path=prefix+'metadata.json',metadata_sha256=digest(raw),metadata_bytes=len(raw),committed_entry_refs=entry_refs,
            commit_boundary='Root must commit metadata before constructing Host metadata_ref; no Host/Evidence/policy/approval emitted')
    print(encoded(report).decode().rstrip('\n'))


if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('TRANSPORT_NORMALIZATION_FAILURE: '+type(exc).__name__+': '+str(exc)[:1000],file=__import__('sys').stderr)
        raise SystemExit(1)
