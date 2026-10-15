"""Final static scope/pin checks; no acceptance rerun."""
import json
from pathlib import Path
import subprocess

BASE='ef3a25d02aa5b0d5fdc0403216c502b13f4995fd'
def git(*args):
    return subprocess.run(['git',*args],check=True,capture_output=True).stdout.decode()
prior=set(git('ls-tree','-r','--name-only',BASE).splitlines())
changed=git('diff','--name-only',BASE).splitlines()
assert all(p=='tools/workflow_assurance.py' if p in prior else p.startswith('.agent/evidence/122/source2-') for p in changed)
assert all(p.startswith('.agent/evidence/122/source2-') for p in git('ls-files','--others','--exclude-standard').splitlines())
for label in ('compatibility','default'):
    r=json.loads(Path('.agent/evidence/122/source2-'+label+'-execution.json').read_text())
    assert r['actual_exit']==0 and r['protected_preserved']
    if label=='default': assert r['order_exact'] and len(r['ordered_passes'])==46
check=subprocess.run(['git','diff','--check'],capture_output=True)
Path('.agent/evidence/122/source2-diff-check.stdout.txt').write_bytes(check.stdout)
Path('.agent/evidence/122/source2-diff-check.stderr.txt').write_bytes(check.stderr)
assert check.returncode==0
print(json.dumps({'static_checks':'passed','baseline':BASE,'baseline_paths':len(prior),'only_prior_path_changed':'tools/workflow_assurance.py','all_prior_proof_and_dispatch_preserved':True,'diff_check_actual_exit':check.returncode,'behavior_rerun':False}))
