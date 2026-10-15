"""Root final whole-feature measurement using the unchanged frozen classifier."""
import json
import os
from pathlib import Path
import re
import subprocess

E = Path('.agent/evidence/122')
revision = subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
base = '3ee2b39b75fa5e2bc645e52c7b02f185d5d84e03'
argv = ['python3','.agent/evidence/scope-budget-014/measure.py','--range','122='+base+'..'+revision,'--files']
p = subprocess.run(argv,capture_output=True)
(E/'scope-measurement-final.txt').write_bytes(p.stdout)
(E/'scope-measurement-final.stderr.txt').write_bytes(p.stderr)
(E/'scope-measurement-final-result.json').write_text(json.dumps({'role':'Root','argv':argv,'cwd':str(Path.cwd()),'actual_exit':p.returncode,'revision':revision,'environment':{'PYTHONDONTWRITEBYTECODE':os.environ['PYTHONDONTWRITEBYTECODE']},'stdout':str(E/'scope-measurement-final.txt'),'stderr':str(E/'scope-measurement-final.stderr.txt')},indent=2)+'\n')
assert p.returncode == 0,p.stderr.decode()
text = p.stdout.decode()
def total(name):
    value, = re.findall(r'^\s*'+name+r'=(\d+)',text,re.M)
    return int(value)
budget,evidence,excluded = [total(k) for k in ('BUDGET_COUNTED_LINES','EVIDENCE_LINES','EXCLUDED_LINES')]
assert total('UNCLASSIFIED_LINES') == 0
rows = subprocess.check_output(['git','diff','--numstat',base,revision,'--','tools/workflow_assurance.py','tools/test_workflow_assurance.py','methodology/03_circuit_breaker.md','tools/README.md','CHANGELOG.md'],text=True).splitlines()
counts = {r.split('\t',2)[2]:sum(map(int,r.split('\t')[:2])) for r in rows}
tests = counts.get('tools/test_workflow_assurance.py',0)
source = sum(v for k,v in counts.items() if k != 'tools/test_workflow_assurance.py')
assert budget == total('PRODUCT_LINES') + total('PROCESS_OVERHEAD_LINES')
assert source + tests == total('PRODUCT_LINES')
state = json.loads(Path('.agent/run_state.json').read_text())
b = state['scope_budget']
assert b['original_estimate_lines'] == 7200 and b['ceiling_130pct'] == 9360
assert [r['id'] for r in b['per_feature']] == ['119','120','121']
assert b['total_lines_changed'] == 3364
assert 3364 + budget <= 9360
average = sum(r['actual'] for r in b['per_feature'][-3:])/3
assert budget <= 3*average
result = {'id':'122','estimated':950,'actual':budget,'product_lines':source+tests,'source_lines':source,'independent_test_lines':tests,'process_overhead_lines':total('PROCESS_OVERHEAD_LINES'),'evidence_lines':evidence,'excluded_lines':excluded,'range':base+'..'+revision,'evidence':str(E/'scope-measurement-final.txt'),'measurement_status':'final whole122 before PR103, append once','measurement_revision':revision,'baseline':{'prior_features':['119','120','121'],'rolling_average':average,'three_times_threshold':3*average,'first_feature_exception':False,'flagged':False},'note':'Includes all contract/review/fixture/hosted-failure recoveries, current controls, QA/capture/canonical closure and independently reviewed current docs.42 adjacent prior-feature evidence files remain counted as raw evidence, exact attribution preserved. Original7200/9360 unchanged.'}
(E/'scope-budget-row-final.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'passed':True,'actual_exit':0,'row':result,'phase_total':3364+budget,'ceiling':9360},indent=2))
