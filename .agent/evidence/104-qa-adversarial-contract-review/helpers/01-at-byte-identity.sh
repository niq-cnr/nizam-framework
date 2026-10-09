# AT1-AT10 are byte-identical to the committed feature list (index 1..10), the feature list is unchanged vs <A>, S01 (the contract's own guard) passes
set -u
python3 -I - <<'PY'
import json, subprocess, hashlib, sys
A = 'f3b6dcb3a2e9c8a465e8ccb1be2e67fce721deef'
c = json.load(open('.agent/contracts/104.json'))
print('contract sha256', hashlib.sha256(open('.agent/contracts/104.json','rb').read()).hexdigest(), 'status', c['status'], 'revision', c['design_notes']['revision'][:10])
f_at_A = next(x for x in json.loads(subprocess.run(['git','show',A+':.agent/feature_list_014.json'],capture_output=True,text=True,check=True).stdout)['features'] if x['id']=='104')
f_wt = next(x for x in json.load(open('.agent/feature_list_014.json'))['features'] if x['id']=='104')
print('feature 104 acceptance_tests: working tree == <A>:', f_at_A['acceptance_tests'] == f_wt['acceptance_tests'], '| estimated_lines', f_wt['estimated_lines'], '== contract', c['estimated_lines'])
ats = [v for v in c['verification'] if not v.get('supplementary')]
ok = True
for i, v in enumerate(ats):
    same = v['acceptance_test'] == v['command'] == f_at_A['acceptance_tests'][i] and v['acceptance_test_index'] == i + 1
    ok &= same
    print('AT%-2d index=%d verbatim=%s sha256=%s' % (i+1, v['acceptance_test_index'], same, hashlib.sha256(v['command'].encode()).hexdigest()[:16]))
print('AT5 carries the A2 branch literal:', "R['headBranch']=='phase/014-104-sandbox-ci'" in ats[4]['command'], '| count AT/supplementary:', len(ats), len(c['verification'])-len(ats))
d = subprocess.run(['git','diff','--stat',A,'--','.agent/feature_list_014.json','.agent/product_spec_014.md','.github','tools','schema','standard'],capture_output=True,text=True).stdout
print('tracked planning/product files differing from <A> (must be empty):', repr(d))
sys.exit(0 if ok and not d and f_at_A['acceptance_tests']==f_wt['acceptance_tests'] else 1)
PY
echo "python rc=$?"
bash .agent/evidence/104-qa-adversarial-contract-review/helpers/cmds/S01.sh
echo "S01 rc=$?"
