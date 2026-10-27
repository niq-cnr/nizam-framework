import json, os, subprocess, tempfile, shutil
from pathlib import Path
source=Path.cwd()
script=(source/'tools/validate.sh').read_text()
script=script[:script.rfind('main "$@"')]
with tempfile.TemporaryDirectory(prefix='nf-c13-envelope-') as tmp:
 root=Path(tmp)
 for name in ('schema','standard','methodology','templates','tools','ecosystem'):
  shutil.copytree(source/name,root/name,ignore=shutil.ignore_patterns('fixtures','__pycache__'))
 shutil.copy2(source/'NIZAM.json',root/'NIZAM.json')
 (root/'docs').mkdir()
 manifest=json.loads((root/'tools/skill.json').read_text())
 manifest['capabilities'][0]['module']='docs/envelope.md'
 index=json.loads((root/'NIZAM.json').read_text())
 index['capabilities'].append({'id':'adversarial-envelope','summary':'envelope','authoritative_source':'docs/envelope.md'})
 (root/'NIZAM.json').write_text(json.dumps(index))
 (root/'tools/skill.json').write_text(json.dumps(manifest))
 def check():return subprocess.run(['bash','-c',script+'\ncheck_c13_skill_index payload'],cwd=root,text=True,capture_output=True)
 absent=check()
 assert absent.returncode==0,absent.stdout+absent.stderr
 (root/'docs/envelope.md').symlink_to(source/'tools/SKILL.md')
 escaped=check()
 assert escaped.returncode==1,escaped.stdout+escaped.stderr
 assert '[C13] FAIL' in escaped.stdout and 'symlink escape' in escaped.stdout,escaped.stdout+escaped.stderr
 print('Payload absent envelope control PASS; same indexed envelope escaping symlink FAILS C13 before carveout.')
