"""Independent serial execution and full raw capture of the approved 112 commands."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
E = ROOT / '.agent/evidence/112'
seal = json.loads((E / 'qa-inputs.json').read_text())
contract = json.loads((ROOT / '.agent/contracts/112.json').read_text())
environment = os.environ.copy()
environment['PYTHONDONTWRITEBYTECODE'] = '1'
results = []
for index, required in enumerate(contract['verification'], 1):
    candidate = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    if candidate != seal['candidate_sha']:
        raise RuntimeError('HEAD changed before command ' + str(index))
    command = required['command']
    target = ROOT / required['evidence']
    with target.open('x') as capture:
        start = datetime.now(timezone.utc).isoformat()
        capture.write('COMMAND: ' + command + '\nCANDIDATE_SHA: ' + candidate + '\nUTC_START: ' + start + '\n')
        capture.flush()
        completed = subprocess.run(command, cwd=ROOT, env=environment, shell=True,
                                   executable='/bin/bash', capture_output=True)
        end = datetime.now(timezone.utc).isoformat()
        capture.write('STDOUT:\n' + completed.stdout.decode(errors='replace'))
        if completed.stdout and not completed.stdout.endswith(b'\n'):
            capture.write('\n')
        capture.write('STDERR:\n' + completed.stderr.decode(errors='replace'))
        if completed.stderr and not completed.stderr.endswith(b'\n'):
            capture.write('\n')
        capture.write('UTC_END: ' + end + '\nEXIT: ' + str(completed.returncode) + '\n')
    result = {'command': command, 'evidence': required['evidence'], 'exit_code': completed.returncode}
    results.append(result)
    print('AT' + str(index) + ' actual EXIT ' + str(completed.returncode) + ' -> ' + required['evidence'], flush=True)
with (E / 'acceptance-command-results.json').open('x') as output:
    json.dump({'candidate_sha': seal['candidate_sha'], 'checks': results}, output, indent=2)
    output.write('\n')
print('ACTUAL CONTRACT CHECKS ' + str(len(results)) + '; EXIT0 ' + str(sum(r['exit_code'] == 0 for r in results)), flush=True)
