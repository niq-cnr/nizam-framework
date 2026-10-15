"""Root transport for observed final-head run IDs, without launching CI."""
import datetime
import json
from pathlib import Path
import subprocess
import sys

prefix,head,run_id,closeout_id,job_id = sys.argv[1:]
E = Path('.agent/evidence/122')
assert prefix == 'ci3'
assert not (E/(prefix+'-fetch-results.json')).exists()
revision = subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
records = []
def capture(label, argv):
    p = subprocess.run(argv,capture_output=True)
    out,err = E/(prefix+'-'+label+'.stdout.txt'),E/(prefix+'-'+label+'.stderr.txt')
    out.write_bytes(p.stdout);err.write_bytes(p.stderr)
    records.append({'argv':argv,'cwd':str(Path.cwd()),'actual_exit':p.returncode,'stdout':str(out),'stderr':str(err),'revision':revision,'at':datetime.datetime.now(datetime.timezone.utc).isoformat()})
    (E/(prefix+'-fetch-results.json')).write_text(json.dumps(records,indent=2)+'\n')
    assert p.returncode == 0,label
repo = 'niq-cnr/nizam-framework'
capture('run',['gh','run','view',run_id,'--repo',repo,'--json','databaseId,headSha,status,conclusion,jobs'])
capture('closeout',['gh','run','view',closeout_id,'--repo',repo,'--json','databaseId,headSha,status,conclusion,jobs'])
capture('job-log',['gh','run','view',run_id,'--repo',repo,'--job',job_id,'--log'])
capture('checkout',['git','fetch','origin','refs/pull/103/merge'])
argv = ['python3',str(E/'capture-hosted.py'),prefix,head,run_id,closeout_id,job_id,head,'103']
p = subprocess.run(argv,capture_output=True)
(E/(prefix+'-parser.stdout.txt')).write_bytes(p.stdout)
(E/(prefix+'-parser.stderr.txt')).write_bytes(p.stderr)
(E/(prefix+'-parser.json')).write_text(json.dumps({'argv':argv,'cwd':str(Path.cwd()),'actual_exit':p.returncode,'revision':revision},indent=2)+'\n')
print(p.stdout.decode(),end='');print(p.stderr.decode(),end='')
assert p.returncode == 0
