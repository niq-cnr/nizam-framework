#!/usr/bin/python3
"""Bounded deterministic observations and actual same-candidate CI dogfood.

Root supplies the fixed selection. This runner creates experiment outputs only;
Root independently selects transported captures before the verification pass.
"""
import argparse
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile

PREFIX = '.agent/evidence/123/experiment/'
SELECTION = '.agent/evidence/123/selection.json'
ORIGIN = 'https://github.com/niq-cnr/nizam-framework.git'
REPOSITORY = 'niq-cnr/nizam-framework'


def encoded(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()+b'\n'


def observe(args):
    """Stdlib-only observation inside the existing enforced evaluator boundary."""
    packet_raw=Path(args.packet).read_bytes();packet=json.loads(packet_raw)
    observations=[]
    workflow='.github/workflows/compliance.yml'
    for change in packet['delta']:
        if change['path']!=workflow or change['new_digest'] is None:continue
        entry=next(x for x in packet['review_files'] if x['path']==workflow)
        content=entry['content'];current=content.splitlines();old=(change['old_content'] or '').splitlines()
        added=set()
        for tag,a,b,c,d in difflib.SequenceMatcher(a=old,b=current,autojunk=False).get_opcodes():
            if tag in ('replace','insert'):added.update(range(c,d))
        for index in sorted(added):
            line=current[index];match=re.match(r'^\s*continue-on-error\s*:\s*(.*?)\s*$',line)
            if not match:continue
            # This bounded rule accepts only the unquoted literal false.
            value=match[1].split('#',1)[0].strip()
            if value=='false':continue
            observations.append(dict(action='active',finding=dict(severity='important',category='workflow',path=workflow,
                symbol='continue-on-error:'+str(index+1),rule='gate-disable',title='Workflow disables a required failure gate',
                description='Changed continue-on-error value is not literal false.'),evidence=[dict(path=workflow,start_line=index+1,
                    end_line=index+1,excerpt=line,content_digest=entry['content_digest'])]))
    trial=dict(schema_version='1.0.0',review_id=packet['review_id'],trial_number=args.trial_number,
        packet_digest=hashlib.sha256(packet_raw).hexdigest(),head_sha=packet['head_sha'],observations=observations)
    output=Path(args.output)
    with output.open('xb') as stream:stream.write(encoded(trial))
    # Private production trace retained by the existing evaluator as raw stdout.
    print('WA123_OBSERVER_FRAME='+encoded(dict(argv=sys.argv,cwd=os.getcwd())).decode().rstrip('\n'))
    return 0


def api_module():
    import workflow_assurance
    return workflow_assurance


def command(argv,cwd):
    return subprocess.run([str(x) for x in argv],cwd=cwd,capture_output=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})


def checked(argv,cwd):
    process=command(argv,cwd)
    if process.returncode:raise RuntimeError('command failed '+repr(argv)+': '+process.stderr.decode(errors='replace')[:600])
    return process.stdout


def git(root,*args):
    return checked(['git','-C',str(root),*args],root).decode().strip()


def reference(root,path,revision=None):
    revision=revision or git(root,'rev-parse','HEAD')
    raw=checked(['git','-C',str(root),'show',revision+':'+path],root)
    return dict(path=path,revision=revision,sha256=hashlib.sha256(raw).hexdigest())


def put(root,path,value):
    target=root/path;target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():raise RuntimeError('experiment output already exists: '+path)
    raw=value if type(value) is bytes else encoded(value)
    target.write_bytes(raw)
    return target


def commit(root,message):
    git(root,'add','--',PREFIX)
    if git(root,'diff','--cached','--name-only'):git(root,'commit','--quiet','-m',message)
    return git(root,'rev-parse','HEAD')


def current_checkout(root):
    revision=git(root,'rev-parse','HEAD');event=os.environ.get('GITHUB_EVENT_NAME')
    if event not in ('push','pull_request'):raise RuntimeError('actual hosted push/pull_request event required')
    event_data=json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_bytes())
    if event=='pull_request':head=event_data['pull_request']['head']['sha'];base=event_data['pull_request']['base']['sha']
    else:head=event_data['after'];base=None
    return dict(sha=revision,tree=git(root,'rev-parse',revision+'^{tree}'),event=event,event_head=head,event_base=base,
        parents=git(root,'show','-s','--format=%P',revision).split())


def capture_record(candidate,producer,argv,cwd,revision,stdout,stderr):
    wa=api_module()
    return dict(schema_version=1,argv=[str(x) for x in argv],cwd=str(cwd),revision=revision,
        candidate_sha256=wa.sha(wa.canonical(candidate)),environment=candidate['environment'],producer=producer,
        executed=True,outcome='success',exit_code=0,stdout=stdout,stderr=stderr)


def inventory(root,source,tip):
    wa=api_module();rows=[]
    for revision in git(root,'rev-list','--reverse',source+'..'+tip).splitlines():
        for path in git(root,'diff-tree','--no-commit-id','--name-only','-r',revision).splitlines():
            fields=git(root,'ls-tree',revision,'--',path).split()
            if not path.startswith(PREFIX) or fields[0] not in ('100644','100755') or fields[1]!='blob':raise RuntimeError('experiment output scope/mode')
            rows.append(dict(path=path,revision=revision,git_blob=fields[2],git_mode=fields[0],sha256=reference(root,path,revision)['sha256']))
    return sorted(rows,key=lambda row:(row['revision'],row['path']))


def bundle_outputs(root,output,selection_ref,selection,checkout,candidate,result_refs,outer_argv,outer_cwd):
    wa=api_module();tip=git(root,'rev-parse','HEAD');git(root,'update-ref','refs/wa123/proof',tip)
    bundle=output/'proof.bundle'
    checked(['git','-C',str(root),'bundle','create','--version=2',str(bundle),'refs/wa123/proof','^'+selection['source_commit']],root)
    raw=bundle.read_bytes();manifest=dict(schema_version=1,mode=selection['mode'],source_commit=selection['source_commit'],
        output_tip=tip,bundle_sha256=wa.sha(raw),bundle_size=len(raw),inventory=inventory(root,selection['source_commit'],tip))
    # The same read-only strict parser checks the produced object set before upload.
    wa._ControlsProof(root).pack(raw,selection['source_commit'])
    manifest_raw=encoded(manifest);(output/'manifest.json').write_bytes(manifest_raw)
    invocation=dict(schema_version=1,mode=selection['mode'],producer=selection['producer'],selection_ref=selection_ref,
        source_commit=selection['source_commit'],checkout=checkout,environment=candidate['environment'],argv=outer_argv,cwd=str(outer_cwd),
        output_tip=tip,bundle_sha256=wa.sha(raw),manifest_sha256=wa.sha(manifest_raw),result_refs=result_refs,actual_exit=0)
    (output/'invocation.json').write_bytes(encoded(invocation))
    print('WA123_INVOCATION='+encoded(invocation).decode().rstrip('\n'))


def prepare(root,output,selection,checkout):
    wa=api_module();scratch=Path(tempfile.mkdtemp(prefix='wa123-experiment-',dir=output.parent))
    experiment=scratch/'repo'
    checked(['git','clone','--quiet','--shared','--no-checkout',str(root),str(experiment)],root)
    setup=[]
    for args in [('remote','get-url','origin'),('remote','set-url','origin',ORIGIN),('checkout','--quiet','--detach',selection['source_commit']),
        ('config','user.name','WA123 isolated CI experiment'),('config','user.email','wa123@example.invalid'),('config','gc.auto','0'),('config','maintenance.auto','false')]:
        argv=['git','-C',str(experiment),*args];process=command(argv,root)
        setup.append(dict(argv=argv,cwd=str(root),actual_exit=process.returncode,stdout=process.stdout.decode(),stderr=process.stderr.decode()))
        if process.returncode:raise RuntimeError('isolated selected-origin setup failed')
    candidate=wa.assess_repository(experiment,selection['source_commit'],selection['inputs'],['PYTHONDONTWRITEBYTECODE'],{})
    if selection['mode']=='verify' and not wa.compare_identity(candidate,selection['candidate']):raise RuntimeError('actual verify runtime/candidate differs from capture')
    if selection['mode']=='capture':
        put(experiment,PREFIX+'inputs/selection-capture.json',selection)
        put(experiment,PREFIX+'setup.txt',encoded(dict(observed_checkout_origin=git(root,'remote','get-url','origin'),commands=setup)))
        commit(experiment,'WA123 selected capture input and owned origin setup')
    return experiment,candidate,scratch


def run_map(args):
    wa=api_module();import convergent_review as cr
    root=Path.cwd();selection=wa.parse_json(Path(args.selection).read_bytes());evaluation=Path(args.evaluation)
    cr.verify_replay_directory(evaluation/'review/replay.json')
    ledger=wa.parse_json((evaluation/'review/ledger.json').read_bytes())
    report=wa.parse_json(wa._receipt_artifact(root,selection['report_ref']))
    result=wa.convergent_agf_verdict(ledger,report,expected_repository=selection['review_repository'],expected_head_sha=selection['source_commit'])
    wa._receipt_gate(result)
    Path(args.output).parent.mkdir(parents=True,exist_ok=True)
    Path(args.output).write_bytes(encoded(result))
    print('WA123_A11_APPROVED')
    return 0


def run_capture(root,output,selection_ref,selection,checkout,outer_argv):
    wa=api_module();experiment,candidate,scratch=prepare(root,output,selection,checkout)
    proof=wa._ControlsProof(experiment);proof.selection(selection_ref,'capture');proof.identity(candidate,selection['inputs'])
    proof.checkout(checkout,selection_ref,candidate);proof.prerequisites(selection,candidate);proof.authority(selection);proof.shadow(selection)
    put(experiment,PREFIX+'candidate.json',candidate)
    process_rows={}
    for label,path in [('boundary','.github/scripts/test_sandbox_boundaries.py'),('isolation','tools/test_convergent_review.py')]:
        argv=[sys.executable,path];revision=git(experiment,'rev-parse','HEAD');process=command(argv,experiment)
        put(experiment,PREFIX+label+'/stdout',process.stdout);put(experiment,PREFIX+label+'/stderr',process.stderr)
        if process.returncode:
            (output/(label+'-failure.stdout')).write_bytes(process.stdout);(output/(label+'-failure.stderr')).write_bytes(process.stderr)
            raise RuntimeError('actual '+label+' failed exit '+str(process.returncode))
        process_rows[label]=(argv,revision)
    evaluation=experiment/(PREFIX+'evaluation/run');packet=evaluation.parent/'packet.json';packet.parent.mkdir(parents=True,exist_ok=True)
    checked([sys.executable,'tools/convergent_review.py','build-packet','--repo',str(experiment),'--repository',REPOSITORY,
        '--review-id','wa123-controls','--mode','ordinary','--base',selection['packet_base'],'--head',selection['source_commit'],'--output',str(packet)],experiment)
    prompt=experiment/'templates/convergent-review-prompt.md';runner=experiment/'tools/workflow_assurance_ci.py';adapter=experiment/'tools/linux_trial_sandbox.sh'
    argv=[sys.executable,'tools/evaluate_convergent_review_prompt.py','--packet',str(packet),'--prompt-template',str(prompt),
        '--runner',str(runner),'--isolation-adapter',str(adapter),'--output-dir',str(evaluation),'--timeout-seconds','120']
    if selection['prior_ledger'] is not None:
        prior=evaluation.parent/'prior-ledger.json';prior.write_bytes(wa._receipt_artifact(experiment,selection['prior_ledger']));argv+=['--prior-ledger',str(prior)]
    process=command(argv,experiment)
    put(experiment,PREFIX+'evaluation/stdout',process.stdout);put(experiment,PREFIX+'evaluation/stderr',process.stderr)
    if process.returncode:raise RuntimeError('actual enforced three-trial evaluator failed exit '+str(process.returncode)+': '+process.stderr.decode(errors='replace')[:600])
    mapped=experiment/(PREFIX+'map/result.json')
    argv=[sys.executable,'tools/workflow_assurance_ci.py','map','--selection',PREFIX+'inputs/selection-capture.json','--evaluation',str(evaluation),'--output',str(mapped)]
    revision=git(experiment,'rev-parse','HEAD');process=command(argv,experiment)
    put(experiment,PREFIX+'map/stdout',process.stdout);put(experiment,PREFIX+'map/stderr',process.stderr)
    if process.returncode:raise RuntimeError('actual A11 map rejected exit '+str(process.returncode))
    outputs=commit(experiment,'WA123 actual capability/evaluator/map outputs')
    process_values={}
    for label,(command_argv,execution) in process_rows.items():
        process_values[label]=dict(argv=command_argv,cwd=str(experiment),revision=execution,executed=True,actual_exit=0,
            stdout=reference(experiment,PREFIX+label+'/stdout',outputs),stderr=reference(experiment,PREFIX+label+'/stderr',outputs))
    capability=dict(schema_version=1,source_commit=selection['source_commit'],checkout_sha=checkout['sha'],environment=candidate['environment'],producer=selection['producer'],**process_values)
    put(experiment,PREFIX+'capability.json',capability)
    put(experiment,PREFIX+'map/capture.json',capture_record(candidate,selection['producer'],argv,experiment,revision,
        reference(experiment,PREFIX+'map/stdout',outputs),reference(experiment,PREFIX+'map/stderr',outputs)))
    tip=commit(experiment,'WA123 actual immutable captures')
    result_refs=[reference(experiment,PREFIX+'candidate.json',outputs),reference(experiment,PREFIX+'capability.json',tip),
        reference(experiment,PREFIX+'evaluation/run/prompt-evaluation.json',outputs),reference(experiment,PREFIX+'evaluation/run/review/replay.json',outputs),
        reference(experiment,PREFIX+'map/result.json',outputs),reference(experiment,PREFIX+'map/capture.json',tip)]
    # Actual observer stdout records original pre-publication trial paths.
    trials=[]
    for n in (1,2,3):
        trial_dir=evaluation/'evaluation'/('trial-'+str(n));raw=(trial_dir/'runner.stdout').read_text()
        frames=re.findall(r'^WA123_OBSERVER_FRAME=(\{.*\})$',raw,re.M)
        if len(frames)!=1:raise RuntimeError('actual observer frame missing/duplicate')
        frame=json.loads(frames[0]);observer_argv=frame['argv'];trial_root=frame['cwd']
        invocation=[str(adapter),'--root',trial_root,'--runner',str(runner),'--',*observer_argv]
        row=dict(number=n,packet_ref=reference(experiment,str((trial_dir/'packet.json').relative_to(experiment)),outputs),
            prompt_ref=reference(experiment,str((trial_dir/'prompt.md').relative_to(experiment)),outputs),output_ref=reference(experiment,str((trial_dir/'trial.json').relative_to(experiment)),outputs),
            stdout_ref=reference(experiment,str((trial_dir/'runner.stdout').relative_to(experiment)),outputs),stderr_ref=reference(experiment,str((trial_dir/'runner.stderr').relative_to(experiment)),outputs),
            evaluation_receipt_ref=result_refs[2],invocation=invocation,runner_ref=selection['runner_ref'],adapter_ref=selection['adapter_ref'],evaluator_ref=selection['evaluator_ref'],boundary_ref=result_refs[1])
        trials.append(row)
    put(experiment,PREFIX+'trial-provenance.json',trials);commit(experiment,'WA123 actual per-trial execution provenance')
    bundle_outputs(experiment,output,selection_ref,selection,checkout,candidate,result_refs,outer_argv,root)
    return scratch


def run_verify(root,output,selection_ref,selection,checkout,outer_argv):
    wa=api_module();experiment,candidate,scratch=prepare(root,output,selection,checkout)
    proof=wa._ControlsProof(experiment);proof.selection(selection_ref,'verify');proof.identity(candidate,selection['inputs']);proof.checkout(checkout,selection_ref,candidate)
    # Existing output branch is imported separately from immutable Root C/V history.
    bundle=output.parent/(output.name+'-capture.bundle');bundle.write_bytes(wa._receipt_artifact(root,selection['capture_pack_ref']))
    checked(['git','-C',str(experiment),'bundle','verify',str(bundle)],experiment)
    git(experiment,'fetch','--no-tags','--no-write-fetch-head',str(bundle),'refs/wa123/proof:refs/wa123/import-capture')
    git(experiment,'checkout','--quiet','--detach','refs/wa123/import-capture')
    put(experiment,PREFIX+'inputs/selection-verify.json',selection)
    policy=wa.parse_json(wa._receipt_artifact(root,selection['a10_policy_ref']))
    receipt=wa.parse_json(wa._receipt_artifact(root,policy['recovery']))
    put(experiment,PREFIX+'inputs/policy-verify.json',policy);put(experiment,PREFIX+'inputs/receipt-verify.json',receipt)
    commit(experiment,'WA123 independently selected verification inputs')
    verified=wa.verify_stage_receipt(experiment,receipt,policy=policy)
    state=wa.parse_json(wa._receipt_artifact(root,selection['shadow_state_ref']))
    advance=wa.plan_receipt_transition(experiment,state,receipt,policy=policy)
    noop=wa.plan_receipt_transition(experiment,advance['state'],receipt,policy=policy)
    republish=wa.plan_receipt_transition(experiment,state,None,policy=policy)
    import copy
    absent=copy.deepcopy(policy);absent['recovery']['path']+='.missing-wa123'
    if git(experiment,'ls-tree',absent['recovery']['revision'],'--',absent['recovery']['path']):raise RuntimeError('selected missing recovery path exists')
    rerun=wa.plan_receipt_transition(experiment,state,None,policy=absent)
    conflicting=copy.deepcopy(advance['state']);conflicting['history'].append(copy.deepcopy(conflicting['history'][-1]))
    try:wa.plan_receipt_transition(experiment,conflicting,receipt,policy=policy)
    except wa.AssuranceError:pass
    else:raise RuntimeError('actual A10 duplicate advancement accepted')
    result=dict(receipt=verified,advance=advance,noop=noop,republish=republish,rerun_required=rerun,conflict_rejected=True)
    if [advance['action'],noop['action'],republish['action'],rerun['action']]!=['advance','noop','republish','rerun-required']:raise RuntimeError('actual A10 transition actions')
    put(experiment,PREFIX+'verify/result.json',result);put(experiment,PREFIX+'verify/stdout',encoded(result));put(experiment,PREFIX+'verify/stderr',b'')
    outputs=commit(experiment,'WA123 actual matching-runtime A10 results')
    capture=capture_record(candidate,selection['producer'],outer_argv,root,checkout['sha'],reference(experiment,PREFIX+'verify/stdout',outputs),reference(experiment,PREFIX+'verify/stderr',outputs))
    put(experiment,PREFIX+'verify/capture.json',capture);tip=commit(experiment,'WA123 actual verification wrapper capture')
    results=[policy['recovery'],reference(experiment,PREFIX+'verify/result.json',outputs),reference(experiment,PREFIX+'verify/capture.json',tip)]
    bundle_outputs(experiment,output,selection_ref,selection,checkout,candidate,results,outer_argv,root)
    return scratch


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',nargs='?',choices=('capture','verify','map'))
    for name in ('selection','evaluation','output','prompt','packet','prior-ledger'):parser.add_argument('--'+name)
    parser.add_argument('--trial-number',type=int,choices=(1,2,3))
    args=parser.parse_args()
    if args.trial_number is not None:
        if args.mode is not None or not all((args.prompt,args.packet,args.output)):parser.error('observer requires prompt/packet/trial/output')
        return observe(args)
    if args.mode=='map':return run_map(args)
    if args.mode not in ('capture','verify') or not args.selection or not args.output:parser.error('stage requires selection/output')
    if os.environ.get('PYTHONDONTWRITEBYTECODE')!='1':raise RuntimeError('PYTHONDONTWRITEBYTECODE=1 required')
    root=Path.cwd().resolve();output=Path(args.output).resolve()
    if output.exists():raise RuntimeError('artifact output must be new')
    output.mkdir(parents=True)
    checkout=current_checkout(root)
    if args.selection!=SELECTION:raise RuntimeError('only fixed independently selected Root input permitted')
    wa=api_module();raw=Path(args.selection).read_bytes();selection=wa.parse_json(raw)
    if raw!=encoded(selection) or selection['mode']!=args.mode:raise RuntimeError('canonical selected stage input required')
    selection_ref=reference(root,SELECTION,checkout['sha'])
    outer_argv=[sys.executable,'tools/workflow_assurance_ci.py',args.mode,'--selection',SELECTION,'--output',str(output)]
    # Policy-producing ownership stays outside this process. Only selected bytes
    # and actual runtime/commands are emitted; Root reviews before selection.
    scratch=None
    try:
        function=run_capture if args.mode=='capture' else run_verify
        scratch=function(root,output,selection_ref,selection,checkout,outer_argv)
        return 0
    except Exception as exc:
        (output/'failure.txt').write_text(type(exc).__name__+': '+str(exc)+'\n')
        raise
    finally:
        if scratch is not None:
            import shutil
            if scratch.parent!=output.parent or not scratch.name.startswith('wa123-experiment-'):raise RuntimeError('unowned cleanup refused')
            shutil.rmtree(scratch)


if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as exc:
        print(type(exc).__name__+': '+str(exc),file=sys.stderr);raise SystemExit(1)
