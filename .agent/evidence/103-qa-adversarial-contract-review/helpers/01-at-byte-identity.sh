python3 -I -c "
import json
c=json.load(open('.agent/contracts/103.json')); f=next(x for x in json.load(open('.agent/feature_list_014.json'))['features'] if x['id']=='103')
v=[x for x in c['verification'] if 'acceptance_test_index' in x]
assert len(v)==len(f['acceptance_tests'])==8, (len(v), len(f['acceptance_tests']))
for i in range(8): print('AT%d'%(i+1), 'acceptance_test==feature_list:', v[i]['acceptance_test']==f['acceptance_tests'][i], 'command==feature_list:', v[i]['command']==f['acceptance_tests'][i], 'index_ok:', v[i]['acceptance_test_index']==i+1)
assert all(v[i]['acceptance_test']==f['acceptance_tests'][i]==v[i]['command'] for i in range(8))
print('ALL 8 BYTE-IDENTICAL')
print('feature_list is the shared-tree working copy; also vs base:')
import subprocess
b=json.loads(subprocess.run(['git','show','88959c9:.agent/feature_list_014.json'],capture_output=True,text=True,check=True).stdout)
fb=next(x for x in b['features'] if x['id']=='103')
assert fb['acceptance_tests']==f['acceptance_tests']
print('working-copy feature 103 acceptance_tests == 88959c9 version: True; status now:', f['status'], 'base status:', fb['status'])
print('estimated_lines', c['estimated_lines'], f['estimated_lines'])
"
