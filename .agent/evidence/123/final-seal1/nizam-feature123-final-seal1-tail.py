import ast,datetime,gzip,hashlib,json,stat,subprocess,sys,time
from pathlib import Path
R=Path('/home/cnross/.tmp/nizam-feature123-final-seal1');O=Path('/home/cnross/.tmp/nizam-feature123-final-seal1-captures')
def enc(x):return json.dumps(x,sort_keys=True,separators=(',',':')).encode()+b'\n'
def sha(b):return hashlib.sha256(b).hexdigest()
def git(*a):return subprocess.check_output(['git',*a],cwd=R)
def read(p):return json.loads((R/p).read_bytes())
def snap():
 rows=[]
 for p in git('ls-files','-z').decode().split('\0'):
  if not p:continue
  q=R/p;s=q.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1,p;rows.append([p,s.st_mode,s.st_nlink,sha(q.read_bytes())])
 return dict(rows=rows,head=git('rev-parse','HEAD').decode().strip(),origin=git('remote','get-url','origin').decode().strip(),refs=git('show-ref').decode(),status=git('status','--porcelain','--untracked-files=all').decode())
def ref(r):
 raw=git('show',r['revision']+':'+r['path']);assert sha(raw)==r['sha256'],r['path'];return raw
before=snap();(O/'seal-tail.before.json.gz').write_bytes(gzip.compress(enc(before),mtime=0))
witness=read('.agent/evidence/123/restored-default-witness-capture2-review.json');review_raw=git('show','5fffe43e74ef96f7fbf618d36a6cb372dfb13e7c:.agent/evidence/123/restored-default-witness-capture2-review.json');assert sha(review_raw)=='27c205062a62ab195792585219ef59174f0260dc9e594c19db3f624ae58b17e6'
assert json.loads(review_raw)==witness
rangefact=json.loads((O/'seal-supplemental.failure-observation.json').read_bytes());assert rangefact['raw_log_sha256']==witness['raw_log_ref']['sha256'] and rangefact['default_range_exact_order_equal'] and rangefact['documented_range']==[791,1189] and rangefact['default_range_terminal_matches']==48
assert sha(ref(witness['raw_log_ref']))==rangefact['raw_log_sha256']
binding=witness['external_result_binding'];jobs=json.loads(ref(binding['job_metadata_ref']));job=next(j for j in jobs['jobs'] if j['id']==binding['job_id'])
assert job['id']==116427391522 and job['run_id']==38736608742 and job['run_attempt']==1 and job['name']=='fixtures_self_test' and job['status']=='completed' and job['conclusion']=='success' and job['head_sha']==witness['actual_execution']['pr_head']
step=next(s for s in job['steps'] if s['name']=='Run PYTHONDONTWRITEBYTECODE=1 python3 tools/test_workflow_assurance.py');assert step['number']==8 and step['status']=='completed' and step['conclusion']=='success'
for key in ('started_at','completed_at'):assert step[key]==witness['actual_execution'][key]
when=lambda s:datetime.datetime.fromisoformat(s.replace('Z','+00:00'))
assert all(when(step['started_at'])>when(v['finished_at']) for v in witness['negative_predecessors'].values())
checkout=witness['actual_execution']['checkout_sha'];assert checkout=='b843f86f6c104810b307f110f9fa956f3d4b451a'
assert git('show','-s','--format=%P',checkout).decode().strip().split()==['79811ef76df950b8151e2af62637ab7d1df34305',witness['actual_execution']['pr_head']]
code=[]
for path,r in witness['immutable_code_refs'].items():
 raw=ref(r);assert raw==git('show','9886e5fadad31845349e54235820edac71c7b7fb:'+path)==(R/path).read_bytes();code.append(r)
ready=[]
for stage,expected in [('positive',0),('semantic-negative',1),('restored',0)]:
 frame=json.loads((O/(stage+'.execution.json')).read_bytes());assert frame['actual_exit']==expected and frame['accepted'] and frame['preservation_equal'] and frame['stop_reason'] is None and frame['installed_count']==239
 snapshots=[]
 for key in ('before','after'):
  b=(O/frame[key]['path']).read_bytes();assert sha(b)==frame[key]['sha256'];snapshots.append(json.loads(gzip.decompress(b)))
 assert snapshots[0]==snapshots[1] and snapshots[0]['head']=='f3a9fffa0a5ad5ff002097a1be810e798988247a'
 for name,v in frame['streams'].items():
  b=(O/v['path']).read_bytes();assert sha(b)==v['sha256'] and len(b)==v['bytes']==v['observed_bytes'] and v['complete'];b.decode('utf-8')
 ready.append(dict(stage=stage,actual_exit=expected,child_pid=frame['child_pid'],started_at=frame['started_at'],finished_at=frame['finished_at'],elapsed_seconds=frame['elapsed_seconds'],frame=stage+'.execution.json',preservation_equal=True,tracked_count=frame['tracked_count'],installed_count=239))
contract=read('.agent/contracts/123.json');catalog=contract['protocol']['payload_catalog'];methods={n.name:n.lineno for c in ast.parse((R/'tools/workflow_assurance.py').read_bytes()).body if isinstance(c,ast.ClassDef) and c.name=='_ControlsProof' for n in c.body if isinstance(n,ast.FunctionDef)}
mapping={
'policy.selection_ref':('selection','Root committed actual verify Selection'),
'policy.evidence_ref / hosted_review.evidence_ref':('verify','Root actual two-pass Evidence committed before independent HostedReview'),
'policy.hosted_review_ref':('verify','Distinct hosted Evaluator actual strict HostedReview before final Root policy'),
'selection.contract_ref':('prerequisites','Root approved metadata after actual independent dual pre-code gates'),
'selection.authority_ref':('authority','Root bounded ExperimentAuthority from immutable standing instruction'),
'selection.prerequisites[].artifact':('prerequisites','Actual ModeA/contract-review/approved metadata/provisional4'),
'selection.prior_ledger':('replay','Root selected existing ledger or explicit null'),
'selection.report_ref':('replay','Independent Report4 before capture; run_map composes existing convergence'),
'selection.prompt_ref':('replay','Protected Source prompt; evaluator.render_prompt per actual trial'),
'selection.runner_ref / adapter_ref / evaluator_ref':('selection','Protected executable Source selected by Root; existing enforced evaluator'),
'selection.shadow_state_ref':('shadow','Root explicit experiment-only ShadowState before capture'),
'selection.candidate':('identity','run_capture clean Source assess_repository; exact verify selection'),
'selection.a10_policy_ref':('a10','Root actual capture receipt/policy/recovery before verify selection'),
'selection.capture_pack_ref / evidence.pack_ref':('pack','run_capture/run_verify bundle_outputs actual output-only Git bundle'),
'evidence.evaluation_ref / Trial.evaluation_receipt_ref':('replay','Existing evaluator actual prompt-evaluation.json and per-trial exit/digests'),
'evidence.replay_ref':('replay','Existing convergence/replay after exactly three enforced trials'),
'Trial.packet_ref / prompt_ref / output_ref':('replay','Existing evaluator exclusive real input/output per-trial files'),
'Trial.stdout_ref / stderr_ref':('replay','Existing evaluator captured actual adapter process streams'),
'evidence.capability_ref / Trial.boundary_ref':('capability','run_capture actual existing boundary+isolation Process captures'),
'Process.stdout / stderr':('capability','stage_command actual bounded subprocess output committed first'),
'evidence.a11_result_ref':('replay','run_map exact existing convergent_agf_verdict mapped result'),
'evidence.a11_capture_ref / a10_capture_ref':('capture','capture_record actual command/cwd/executionrevision/producer/exit/rawrefs'),
'evidence.a10_receipt_ref':('a10','Root selected earlier committed receipt then actual run_verify unchanged A10'),
'evidence.a10_result_ref':('a10','run_verify matching-runtime unchanged A10 APIs and exact shadow proposals'),
'evidence.capture_host.metadata_ref / verify_host.metadata_ref':('host','Root normalization of original five actual raw Fetches per selected run'),
'evidence.capture_host.job_log_ref / verify_host.job_log_ref':('host','Original full genuine gh log bytes and exact unique Invocation marker'),
'HostMetadata.selection_ref / invocation_ref / archive_ref':('host','Root earlier Selection / extracted actual Invocation / downloaded actual ZIP'),
'HostMetadata.fetches[].stdout / stderr':('host','Original actual REST JSON/log/ZIP and complete captured stderr per Fetch kind'),
'ExperimentAuthority.source_authority_ref':('authority','Original immutable repository-local activation authority preserved whole'),
'bundle manifest / invocation wrapper':('host','bundle_outputs exact three-entry actual archive, closed manifest/Invocation'),
'experiment copied inputs':('host','prepare/run_capture/run_verify stage-distinct exact earlier Root bytes')}
assert set(mapping)==set(catalog) and len(mapping)==31
grammar=[dict(group=k,producer=mapping[k][1],parser_consumer='tools/workflow_assurance.py:'+str(methods[mapping[k][0]])+' _ControlsProof.'+mapping[k][0],obligation=catalog[k],acceptance='Immutable current test06eba controls_defects/controls_call/controls_observer/run_controls_ready, current freeze4/provisional4; actual original synthetic0/1 and admitted postnegative default48 restoration; new readiness0/1/0',actual_chain='P a8b7b902 -> HostedReview855fb7c + E cfb84f1d -> original capture2+verify1 five-Fetch/three-trial/A11/A10 proof') for k in catalog]
after=snap();assert before==after;(O/'seal-tail.after.json.gz').write_bytes(gzip.compress(enc(after),mtime=0))
facts=dict(role='Independent final executable acceptance Evaluator',reviewer='/root/final_seal123',feature_id='123',release_revision=before['head'],source_commit='9886e5fadad31845349e54235820edac71c7b7fb',readiness=ready,external_default_job=job['id'],external_default_step=step,restoration=dict(review_sha256=sha(review_raw),raw_log_sha256=rangefact['raw_log_sha256'],documented_default_interval=[791,1189],ordered_selectors=48,after_both_negatives=True,scope='Both synthetic lanes semantic restoration only; no literal restored wrapper, same-runtime or full hosted filesystem claim'),code_binding=code,payload_catalog=grammar,prior_static_control_flow=dict(original_static1='All inherited functions/classes, Source main/assignments, actual rawRef hashes/98Hostedrawfiles passed before false one-assignment assumption at CASES; original actual1 retained, exact PID/start/end missing and not invented',supplemental1='Ordered inherited test assignment sequences/currentfreeze/Sourceanchor/rawRefs and four original0/1 frames+streams/snapshots passed before wholejob55vsdefault48 extraction mismatch; original actual1 retained',range_diagnosis='Readonly retained fulljob1204lines/55terminalPASS; independently documented default791..1189 exactly48orderedPASS, Root admits narrow final tail only'),preservation=dict(equal=True,tracked_count=len(before['rows']),installed_count=sum(x[0].startswith('.nizam/') for x in before['rows']),scope='Own fullphysical bytes/fullmodes/nlinks/HEAD/origin/allrefs/coordination; Root shared refs not claimed frozen'),limitations=['No final QA/ModeB/feature closure verdict','No local namespace/model/historical A10 execution','No interim scope measurement','Original static1 and supplemental1 remain actual1; third final capture records only unexecuted tail0'],no_source_test_helper_contract_policy_edits=True)
(O/'final-seal1-report.json').write_bytes(enc(facts));print(json.dumps(dict(status='PASS final static tail',catalog_groups=31,readiness=[x['actual_exit'] for x in ready],restoration=48,preservation_equal=True)),flush=True)
