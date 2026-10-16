"""Reuse pinned existing capture.execute for focused static rereview only."""
import hashlib,runpy,sys
from pathlib import Path
root=Path.cwd();driver=root/'.agent/evidence/123/fresh-qa-capture1.py'
assert hashlib.sha256(driver.read_bytes()).hexdigest()=='e9e9417c39548919b892f0b7436b885b72a26b781d15455e62daebe9367c5ac0'
area=root/'.agent/evidence/phase020-candidate-accounting-review2';out=Path('/tmp/nizam-020-accounting-closure-review2-capture');out.mkdir(exist_ok=False)
r=runpy.run_path(str(driver))['execute'](root,out,'static1',[sys.executable,'-'],60,Path('/tmp/nizam-020-accounting-review2-static.py').read_bytes())
for p in out.iterdir():(area/p.name).write_bytes(p.read_bytes())
print(r['actual_exit'],r['child_pid']);raise SystemExit(r['actual_exit'])
