"""Root closeout transport: both compliance modes and maintained whitespace."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

E = Path('.agent/evidence/122')
revision = subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
def snapshot():
    paths = subprocess.check_output(['git','ls-files','-z']).decode().split('\0')
    rows = []
    for p in paths:
        if p:
            f = Path(p)
            rows.append([p,f.lstat().st_mode,hashlib.sha256(f.read_bytes()).hexdigest()])
    return hashlib.sha256(json.dumps(rows,separators=(',',':')).encode()).hexdigest(), len(rows)
before = snapshot()
records = []
for label,argv in [
    ('default',['bash','tools/validate.sh']),
    ('payload',['bash','tools/validate.sh','--payload']),
    ('maintained-diff',['git','diff','--check','3ee2b39b75fa5e2bc645e52c7b02f185d5d84e03..HEAD','--','.',':(exclude).agent/evidence/**']),
]:
    p = subprocess.run(argv,capture_output=True)
    out,err = E / ('final-validation1-'+label+'.stdout.txt'),E / ('final-validation1-'+label+'.stderr.txt')
    out.write_bytes(p.stdout);err.write_bytes(p.stderr)
    records.append({'argv':argv,'cwd':str(Path.cwd()),'revision':revision,'environment':{'PYTHONDONTWRITEBYTECODE':os.environ['PYTHONDONTWRITEBYTECODE']},'actual_exit':p.returncode,'stdout':str(out),'stderr':str(err)})
    (E/'final-validation1-records.json').write_text(json.dumps(records,indent=2)+'\n')
    assert p.returncode == 0,(label,p.stderr.decode()[-1000:])
after = snapshot()
assert before == after
assert len(subprocess.check_output(['git','ls-files','.nizam'],text=True).splitlines()) == 239
print(json.dumps({'role':'Root','passed':True,'actual_exit':0,'exercised_revision':revision,'commands':3,'installed_count':239,'protected_before_after_equal':True,'protected_snapshot':before,'records':str(E/'final-validation1-records.json')},indent=2))
