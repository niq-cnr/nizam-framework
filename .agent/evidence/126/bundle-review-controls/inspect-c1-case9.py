"""Inspect the rejected record behind the sealed C1 case9 failure; no repairs."""
import hashlib,json,os,pathlib,runpy,subprocess,sys,tempfile
root=pathlib.Path.cwd();out=root/'.agent/evidence/126/bundle-review-controls';manifest=json.load(open(out/'manifest.json'));c1=manifest['c1_commit']
with tempfile.TemporaryDirectory(prefix='n126-c9-src-') as source_home, tempfile.TemporaryDirectory(prefix='n126-c9-run-') as state_home:
 candidate=pathlib.Path(source_home)
 for name,identity in manifest['files'].items():
  raw=subprocess.check_output(['git','show',c1+':'+name]);assert hashlib.sha256(raw).hexdigest()==identity['sha256'];p=candidate/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
 m=runpy.run_path(str(candidate/'tools/test_runtime_session.py'));s=m['Session'](state_home,candidate=candidate)
 try:
  s.open();old=m['restart'](s)
  request=s.request('set','same-attempt');s.submit(request);assert s.finish(request)=='same-attempt'
  good=s.operation(request['operation_id']);(out/'case9-current-record.json').write_bytes(good.read_bytes())
  bad=s.request('set','forbidden-attempt');bad['attempt']=1;m['refused'](s,bad,'attempt_mismatch')
  rejected=s.operation(bad['operation_id']);(out/'case9-rejected-record.json').write_bytes(rejected.read_bytes())
  records={}
  for label,path,expected in [('current',good,0),('rejected',rejected,1)]:
   argv=['bash','-c','source "$1"; vlib_runtime_record_relations "$2" "$3"','_',str(candidate/'tools/verify_lib.sh'),'runtime_operation',str(path)]
   p=subprocess.run(argv,text=True,capture_output=True,timeout=8)
   (out/f'case9-{label}-c12.stdout.txt').write_text(p.stdout);(out/f'case9-{label}-c12.stderr.txt').write_text(p.stderr)
   records[label]={'argv':argv,'cwd':str(root),'actual_exit':p.returncode,'stdout':f'.agent/evidence/126/bundle-review-controls/case9-{label}-c12.stdout.txt','stderr':f'.agent/evidence/126/bundle-review-controls/case9-{label}-c12.stderr.txt'}
   assert p.returncode==expected
   if expected:assert 'runtime_operation:attempt_continuity' in p.stdout
  r=json.loads(rejected.read_text());assert r['executed'] is False and r['status']=='rejected' and r['rejection_reason']=='attempt_mismatch' and r['attempt']==1 and r['previous_attempt']==2
  assert s.execute('get')=='same-attempt'
  (out/'case9-record-inspection.json').write_text(json.dumps({'c1_commit':c1,'manifest':'.agent/evidence/126/bundle-review-controls/manifest.json','sealed_test_sha256':manifest['test_sha256'],'results':records,'observed_current_attempt':r['attempt'],'observed_previous_attempt':r['previous_attempt'],'rejection_status':r['status'],'executed':r['executed'],'classification':'Actual C1 record provenance violates existing C12 attempt_continuity even though admission was correctly refused. Same-generation current record validates; working replacement process and legitimate memory value confirmed. No source/test repair.'},indent=2)+'\n')
  print('PASS inspection: current record C12 exit0; rejected mismatch record C12 exit1, attempted1/previous2; refused operation never dispatched; legitimate value remains')
 finally:s.cleanup()
