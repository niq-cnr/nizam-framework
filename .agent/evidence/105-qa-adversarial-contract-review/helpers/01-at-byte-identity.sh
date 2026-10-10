# AT1-AT5 byte-identical and in order to feature_list_014.json features[105].acceptance_tests at <A>; feature list at working tree == <A>; estimated_lines.
python3 - <<'PY'
import json, subprocess
A='2a537644dc93cc71786e6468c8f4295079d1c973'
c=json.load(open('.agent/contracts/105.json'))
fl=json.loads(subprocess.run(['git','show',A+':.agent/feature_list_014.json'],capture_output=True,text=True,check=True).stdout)
f=next(x for x in fl['features'] if x['id']=='105')
ats=[v for v in c['verification'] if not v.get('supplementary')]
print('AT count contract/feature-list:',len(ats),len(f['acceptance_tests']))
for i,(v,a) in enumerate(zip(ats,f['acceptance_tests']),1):
    print('AT%d acceptance_test==feature-list:'%i, v['acceptance_test']==a, ' command==feature-list:', v['command']==a, ' index field:', v['acceptance_test_index'])
print('feature list working tree == A:', json.load(open('.agent/feature_list_014.json'))==fl)
print('estimated_lines contract/feature-list:', c['estimated_lines'], f['estimated_lines'])
print('supplementary count:', sum(1 for v in c['verification'] if v.get('supplementary')))
print('status feature list 105:', f.get('status'))
PY
