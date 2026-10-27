"""Execute one operator-authorized QA-round check; stop on any new failure."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys

main = Path(__file__).resolve().parents[4]
identity = json.loads((Path(__file__).parent / 'clone-and-recovery-identity.json').read_text())
clone = Path(identity['clone']).resolve()
sys.path.insert(0, str(clone / 'tools'))
import start_path as sp
step = sys.argv[1]
command = sys.argv[2:]
counts = {}
for label, root in [('main', main.resolve()), ('clone', clone)]:
    history = sp._task_capture_history(root, 'nf-resolver')
    failed = [d for d in history if not sp._successful_task_capture(root, d)]
    counts[label] = len(failed) + 1  # Committed uncaptured setup-verifier failure.
if max(counts.values()) >= 7:
    print(json.dumps({'state':'STOP', 'reason':'operator recovery budget exhausted', 'actual_failed_executions':counts}))
    raise SystemExit(2)
lineage = sp._evaluate_attempt_continuation(clone, task_id='nf-resolver', step=step,
    attempt=7, target_dir=clone / '.agent/evidence/nf-resolver/evaluator-recovery7',
    continuation_basis='operator-reset')
precheck = dict(actual_failed_executions=counts, failure_ceiling=7,
                operator_recovery_accepted=lineage['operator_extension_present'],
                source_commit=identity['assessed_commit'], step=step)
prepath = Path(__file__).parent / ('before-' + step + '.json')
with prepath.open('x') as stream:
    json.dump(precheck, stream, indent=2)
    stream.write('\n')
argv = [sys.executable, 'tools/start_path.py', 'capture', '--id','nf-resolver',
        '--step',step,'--attempt','7','--continuation-basis','operator-reset',
        '--agent-id','first_contact','--session-id','nf-resolver-recovery7',
        '--output-dir','.agent/evidence/nf-resolver/evaluator-recovery7','--',*command]
result = subprocess.run(argv, cwd=clone, env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},
                        text=True,capture_output=True)
if not result.stdout.strip().startswith('{'):
    (Path(__file__).parent / (step + '-gate.stderr.txt')).write_text(result.stderr)
    print(json.dumps({'state':'STOP','reason':'capture refused or malformed output','returncode':result.returncode,'stderr':result.stderr}))
    raise SystemExit(result.returncode or 2)
capture = json.loads(result.stdout)
for relative in [capture['capture_path'], capture['stdout']['path'], capture['stderr']['path']]:
    target = main / relative
    target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():
        if target.read_bytes() != (clone / relative).read_bytes():
            raise RuntimeError('exclusive evidence collision; stop')
    else:
        shutil.copyfile(clone / relative, target)
reservation = Path('.agent/evidence') / ('nf-resolver-' + step + '-attempt7.reservation.json')
if (clone / reservation).exists() and not (main / reservation).exists():
    shutil.copyfile(clone / reservation, main / reservation)
print(json.dumps({'step':step,'assessed_commit':capture['revision'],'exit_code':capture['exit_code'],
                  'capture':capture['capture_path'],'actual_failures_before':counts,
                  'state':'passed' if result.returncode == 0 else 'STOP: new failure; recovery ended'}))
raise SystemExit(result.returncode)
