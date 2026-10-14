import copy, hashlib, importlib.util, json, os, pathlib, subprocess, tempfile
ROOT=pathlib.Path.cwd(); OUT=ROOT/'.agent/evidence/126/mode-b2-controls'; OUT.mkdir(exist_ok=False)
SRC='d965c2ca9dd845f9a094153c7328d90a5398d06f'; BASE='3f0e11b23367c17b1d8c2086011dc0c078441509'
def git(*args): return subprocess.check_output(['git',*args])
def sha(raw):return hashlib.sha256(raw).hexdigest()
def save(name,value): (OUT/name).write_text(json.dumps(value,indent=2)+'\n')
head=git('rev-parse','HEAD').decode().strip(); seal=json.loads((ROOT/'.agent/evidence/126/test-seal-b3.json').read_text()); contract=json.loads((ROOT/'.agent/contracts/126.json').read_text())
assert sha((ROOT/'.agent/contracts/126.json').read_bytes())==seal['contract_sha256']
for item in [seal['test'],*seal['source_stub_harness_docs'],*seal['normative_inputs']]:
 assert sha((ROOT/item['path']).read_bytes())==item['sha256']
 assert git('show',item.get('revision','HEAD')+':'+item['path'])==(ROOT/item['path']).read_bytes()
changes=git('diff','--name-only',BASE,head).decode().splitlines()
products=[x for x in changes if not x.startswith('.agent/') and x!='tools/test_runtime_session.py']
assert sorted(products)==sorted(x['path'] for x in seal['source_stub_harness_docs'])
assert not git('diff',BASE,head,'--','.nizam','.agent/contracts/126.json')
assert not git('diff','b6c0b097ecf2e12ee638a60273af568a8b86523a',head,'--',*[x for x in products if x!='tools/runtime_session.py'])
assert all(x in products or x=='tools/test_runtime_session.py' or x=='.agent/run_state.json' or x.startswith(('.agent/evidence/126/','.agent/validator/126-')) for x in changes)
save('scope.json',{'reviewed_commit':head,'source_candidate':SRC,'source_baseline':BASE,'product_paths':products,'source_hashes':{x:sha((ROOT/x).read_bytes()) for x in products},'test_sha256':seal['test']['sha256'],'bundle_sha256':sha((ROOT/'.agent/evidence/126/test-seal-b3.json').read_bytes()),'overlays':'Independent acceptance runner and role-owned126 evidence/verdicts; Root run_state separately attributed. Installed payload, approved contract and other product paths unchanged.','tracked_paths':changes,'initial_status':'Clean observed before review-owned proof creation.','actual_exit':0})
spec=importlib.util.spec_from_file_location('acceptance',ROOT/'tools/test_runtime_session.py'); t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)
observations=[]
for mode in ('metadata-generation','orphan-result','live-disk-disagreement'):
 with tempfile.TemporaryDirectory(prefix='n126-modeb2-') as home:
  s=t.Session(home,candidate=ROOT)
  try:
   s.open(); assert s.execute('set','positive')=='positive';assert s.execute('get')=='positive'
   t.restart(s);assert s.execute('set','restarted')=='restarted'
   assert s.execute('get')=='restarted'
   state=s.runstate.read_bytes(); sessionpath=s.directory/'runtime_session.json';meta=s.directory/'controller.json'
   if mode!='live-disk-disagreement':s.close()
   if mode=='metadata-generation':
    value=t.load(meta);value['generation']['counter']+=1;value['generation']['nonce']='e'*32;meta.write_text(json.dumps(value))
   elif mode=='orphan-result':
    (s.directory/'operations/orphan.result.json').write_text(json.dumps({'type':'result','operation_id':'orphan','generation':s.record['generation'],'status':'completed','result':'untrusted','image_consistent':True}))
   else:
    value=t.load(sessionpath);value['lease_epoch']+=1;sessionpath.write_text(json.dumps(value))
   paths=[sessionpath,meta,*sorted((s.directory/'operations').iterdir())]; before={str(p.relative_to(s.directory)):sha(p.read_bytes()) for p in paths}
   if mode=='live-disk-disagreement':
    req=s.request('set','must-not-execute'); response=s.call('submit-operation',req,70);s.no_dispatch(req['operation_id']);assert not s.operation(req['operation_id']).exists()
   else:response=s.call('open-session',s.opening(),70)
   assert response['error']=='ambiguous_state', response
   after={str(p.relative_to(s.directory)):sha(p.read_bytes()) for p in paths}
   assert before==after and s.runstate.read_bytes()==state
   observations.append({'mode':mode,'working_transport_and_clean_restart':True,'response':response,'actual_cli_exit':70,'durable_before':before,'durable_after':after,'attempt_state_sha256':sha(state),'state_unchanged':True,'interpretation':'Synthetic publication disagreement in private scratch state; actual controller unchanged.'})
   print('PASS',mode,'exit70 state-preserved')
  finally:s.cleanup()
save('observations.json',{'reviewed_commit':head,'source_candidate':SRC,'controller_sha256':sha((ROOT/'tools/runtime_session.py').read_bytes()),'test_helper_sha256':sha((ROOT/'tools/test_runtime_session.py').read_bytes()),'observations':observations,'actual_exit':0,'boundary':'Bounded Mode B probes, not complete QA or its required additional evaluator spot-check.'})
