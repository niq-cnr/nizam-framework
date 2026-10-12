#!/usr/bin/env python3
"""Fresh evaluator-originated unlisted source-review independence spot; scratch only."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

root=Path.cwd().resolve()
e='.agent/evidence/113/'
review_path=e+'source-review.json'
original=(root/review_path).read_bytes()
review=json.loads(original)
fixed=json.loads((root/(e+'fixed-inputs.json')).read_bytes())
inputs=json.loads((root/(e+'current-source-inputs.json')).read_bytes())
assert review['actor']==fixed['actors']['final_qa']
assert review['actor']!=fixed['actors']['generator']
watched=[review_path,e+'fixed-inputs.json',e+'current-source-inputs.json']+list(inputs['source_paths'])
before={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in watched}
print('PREREGISTERED: Genuine independent review succeeds0; change only actor to Generator with all candidate/hash/evidence/approval fields retained: SOURCE_REVIEW_INDEPENDENCE exit1; restore genuine review succeeds0. Budget class evidence. Scratch component proof; no source/helper/map edits.')
child="""import importlib.util, pathlib, sys
spec=importlib.util.spec_from_file_location('qa113_checker',sys.argv[1])
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
try:
 m.source_review(pathlib.Path(sys.argv[2]))
except m.Failure as err:
 print('TARGET DIAGNOSTIC: '+str(err)); raise SystemExit(1)
print('SOURCE_REVIEW component PASS')
"""
with tempfile.TemporaryDirectory(prefix='qa113-source-review-probe-',dir='/home/cnross/.tmp') as td:
 scratch=Path(td).resolve()
 assert scratch.parent==Path('/home/cnross/.tmp') and scratch.name.startswith('qa113-source-review-probe-')
 paths=[review_path,e+'fixed-inputs.json',e+'current-source-inputs.json']+review['evidence']
 for path in paths:
  destination=scratch/path; destination.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(root/path,destination)
 def run(label,expected,diagnostic=None):
  p=subprocess.run([sys.executable,'-c',child,str(root/(e+'check_113.py')),str(scratch)],cwd=root,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
  print(label+' ACTUAL EXIT '+str(p.returncode)); print(p.stdout,end='')
  assert p.returncode==expected,(label,p.returncode,p.stdout)
  if diagnostic: assert 'TARGET DIAGNOSTIC: '+diagnostic+'\n' in p.stdout
 run('POSITIVE',0)
 bad=dict(review); bad['actor']=fixed['actors']['generator']
 assert set(bad)==set(review) and all(bad[k]==review[k] for k in review if k!='actor')
 assert (scratch/review_path).read_bytes()==original
 (scratch/review_path).write_text(json.dumps(bad,indent=2)+'\n')
 run('NEGATIVE',1,'SOURCE_REVIEW_INDEPENDENCE')
 assert json.loads((scratch/review_path).read_bytes())==bad
 (scratch/review_path).write_bytes(original)
 run('RESTORED',0)
for path,expected in before.items(): assert hashlib.sha256((root/path).read_bytes()).hexdigest()==expected,path
print('OWN SPOT PASS: Generator-authored acceptance review rejected for independence; genuine review restored; real source/fixed/review bytes unchanged.')
