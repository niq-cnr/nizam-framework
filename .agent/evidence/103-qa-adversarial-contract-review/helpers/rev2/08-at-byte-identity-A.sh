python3 -I -c "
import json, subprocess
A='64444289ad3e183dab60f3307da1c8d70a68ebd0'
c=json.load(open('.agent/contracts/103.json'))
fl_A=json.loads(subprocess.run(['git','show',A+':.agent/feature_list_014.json'],capture_output=True,text=True,check=True).stdout)
fl_W=json.load(open('.agent/feature_list_014.json'))
fA=next(x for x in fl_A['features'] if x['id']=='103'); fW=next(x for x in fl_W['features'] if x['id']=='103')
fb=next(x for x in json.loads(subprocess.run(['git','show','88959c9:.agent/feature_list_014.json'],capture_output=True,text=True,check=True).stdout)['features'] if x['id']=='103')
v=[x for x in c['verification'] if 'acceptance_test_index' in x]
assert len(v)==len(fA['acceptance_tests'])==8
for i in range(8): print('AT%d'%(i+1),'acceptance_test==<A>:',v[i]['acceptance_test']==fA['acceptance_tests'][i],'command==<A>:',v[i]['command']==fA['acceptance_tests'][i],'index_ok:',v[i]['acceptance_test_index']==i+1,'differs_from_88959c9:',fA['acceptance_tests'][i]!=fb['acceptance_tests'][i])
assert all(v[i]['acceptance_test']==fA['acceptance_tests'][i]==v[i]['command'] for i in range(8))
assert fA['acceptance_tests']==fW['acceptance_tests']
print('ALL 8 BYTE-IDENTICAL to <A>; working-copy feature list AT strings == <A>; contract status:', c['status'], 'revisions:', c['approvals'], 'estimated_lines', c['estimated_lines'], fA['estimated_lines'])
print('verification entries:', len(c['verification']), 'ATs', len(v), 'supplementary', len(c['verification'])-len(v))
"
