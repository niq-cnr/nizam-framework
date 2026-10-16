"""Reuse existing capture.execute by reference for read-only metadata review."""
import hashlib,runpy,sys
from pathlib import Path
root=Path.cwd();driver=root/'.agent/evidence/123/fresh-qa-capture1.py'
assert hashlib.sha256(driver.read_bytes()).hexdigest()=='e9e9417c39548919b892f0b7436b885b72a26b781d15455e62daebe9367c5ac0'
area=root/'.agent/evidence/phase020-candidate-accounting-review1'
output=Path('/tmp/nizam-020-accounting-closure-review1-capture2');output.mkdir(exist_ok=False)
result=runpy.run_path(str(driver))['execute'](root,output,'static2',[sys.executable,'-'],60,(area/'static2.input.py').read_bytes())
for p in output.iterdir():(area/p.name).write_bytes(p.read_bytes())
print(result['actual_exit'],result['child_pid'])
raise SystemExit(result['actual_exit'])
