import gzip, hashlib, json, subprocess
from pathlib import Path
R=Path.cwd()
p=R/'.agent/evidence/129/source3-B2-diagnostic1'
sha=lambda b:hashlib.sha256(b).hexdigest()
load=lambda p:json.loads(p.read_bytes())
o=load(p/'outcome.json')
assert sha((p/'outcome.json').read_bytes())=='9fcf56aac19495735f4a708d842686774ce588e222176c64e705f8fc7b92ac4f'
assert sha((p/'raw-index.json').read_bytes())=='11545b82532efcc8cb7b7c06e2d01375c2bb88b0ea963877974e0b988561f967'
for row in load(p/'raw-index.json')['files']:
 b=(R/row['path']).read_bytes();assert sha(b)==row['sha256'] and len(b)==row['bytes']
f=load(p/'raw/probe1.execution.json');summary=load(p/'raw/probe1.capture-summary.json')
assert f['actual_exit']==1 and f['child_pid']==314499 and f['timed_out'] is False
assert f['exercised_revision']==o['candidate']['head']=='0697bfe5e121543b2aa8ed8c8607d0c50e99b413'
assert f['checkout_tree']==o['candidate']['tree']=='b7153f05a157213f8e6739780fb1e95c92a750d8'
assert f['argv']==o['execution']['argv'] and 'TMPDIR=/tmp' in f['argv']
assert 0<f['elapsed_seconds']<270 and summary['success'] is True and summary['expected_exit']==1
for stream in ['stdout','stderr']:
 b=(p/'raw'/Path(f[stream]['path']).name).read_bytes();assert len(b)==f[stream]['bytes'] and sha(b)==f[stream]['sha256']
assert (p/'raw/probe1.stderr.txt').read_text()=='BEHAVIOR_ASSERTION: B2_VALID_COMPLETED_HISTORY_DISABLES_IDLE_CLOSE\n'
a=(p/'raw/probe1.preservation-before.json.gz').read_bytes();b=(p/'raw/probe1.preservation-after.json.gz').read_bytes();assert a==b
inv=json.loads(gzip.decompress(a));assert len(inv['rows'])==16455
assert sum(x['path'].startswith('.nizam/') for x in inv['rows'])==239
assert inv['head']==f['exercised_revision'] and inv['tree']==f['checkout_tree']
assert inv['status']=='' and inv['untracked']==[] and inv['origin']=='https://github.com/niq-cnr/nizam-framework.git'
rows={x['path']:x for x in inv['rows']}
for path,digest in o['inputs']['pins'].items():
 assert rows[path]['sha256']==digest
 assert sha(subprocess.check_output(['git','show',f['exercised_revision']+':'+path]))==digest
assert sha((R/'.agent/evidence/129/source3-semantic-diagnostics1/probe.py').read_bytes())==o['inputs']['probe_sha256']
assert sha((R/'.agent/evidence/129/source3-semantic-diagnostics1/intent.json').read_bytes())==o['inputs']['intent_sha256']
assert sha((R/'.agent/evidence/123/fresh-qa-capture1.py').read_bytes())==o['inputs']['capture_sha256']
markers={}
for line in (p/'raw/probe1.stdout.txt').read_text().splitlines():
 tag,_,rest=line.partition(' ')
 if tag in ['B2_OBSERVATION','B2_CLOSE_RESPONSE','B2_NATIVE_POSITIVE','B2_CLEANUP']:
  markers.setdefault(tag,[]).append(json.loads(rest))
obs,=markers['B2_OBSERVATION'];assert obs['completed_operations']==151 and len(obs['record_hashes'])==302
assert obs['before_cleanup'] and obs['attempt_equal'] and obs['sentinel_equal'] and not obs['close_succeeded']
assert obs['admission_refusal']==o['failure_before_cleanup']['public_submit'] and obs['admission_refusal']['exit']==70
assert markers['B2_CLOSE_RESPONSE']==[o['native_positives']['small_history_close'],o['failure_before_cleanup']['idle_close']]
assert markers['B2_NATIVE_POSITIVE']==o['native_positives']['actual_session_identities']
assert markers['B2_CLEANUP']==o['cleanup']['owned'] and all(not x['remaining'] for x in markers['B2_CLEANUP'])
history=next(x for x in markers['B2_NATIVE_POSITIVE'] if x['session']=='history')['controller']
cleanup=next(x for x in markers['B2_CLEANUP'] if x['session']=='history')
assert cleanup['owned_tokens_before']=={str(history['child_pid']):history['child_token'],str(history['supervisor_pid']):history['supervisor_token']}
u=o['cleanup']['unrelated_after_owned_cleanup'];assert u['pid']==obs['unrelated_pid'] and u['original_token']==u['observed_token']==obs['unrelated_token'] and u['sentinel_equal']
assert o['cleanup']['qualified_cleanup_complete'] and all(x['state']=='absent' and not x['same_original_live'] for x in o['cleanup']['post_exit_processes'])
for path in ['.agent/validator/129-source3-diagnostic1.json','.agent/validator/129-source4-architecture1.json']:
 v=load(R/path);assert v['final_verdict']['approved'] is True and all(v[x]==[] for x in ['issues','missing_acceptance_coverage','unsupported_claims'])
assert sha((R/'.agent/evidence/129/implementation4/architecture-preparation1.json').read_bytes())=='a3d9831d2e5fc65c8bb523b9b2c5fe87a7a84060bd3510643fbe0bd9e52cbdc0'
print('B2 intended semantic red admitted: exact candidate, streams, probe, 151 genuine history operations, 302 records, small close positive, owned cleanup and 16455/239 preservation. B1 remains static only; no QA/cost/Source4 qualification inferred.')
