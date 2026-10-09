#!/usr/bin/env python3
"""gen_attempt.py ROOT : simulate a faithful Generator attempt in ROOT/att (scratch only).
B = A + the contract with status 'approved' (what the Orchestrator commits); attempt-base.txt first; implement.py; the 16 generator
evidence files captured in the 04 Section-5 shape (line 1 = first line of the command, verbatim output, EXIT:<code> read from the process);
ONE commit. Then S02 is run pre- and post-commit with the other checks."""
import json, os, pathlib, shutil, subprocess, sys
root = pathlib.Path(sys.argv[1]); H = pathlib.Path(__file__).resolve().parent
repo = pathlib.Path.cwd()
A = 'f3b6dcb3a2e9c8a465e8ccb1be2e67fce721deef'
sh = lambda *a, cwd=None: subprocess.run(a, cwd=cwd, capture_output=True, text=True)
shutil.rmtree(root, ignore_errors=True); root.mkdir(parents=True)
att = root / 'att'
assert sh('git', 'clone', '-q', str(repo), str(att)).returncode == 0
sh('git', '-c', 'advice.detachedHead=false', 'checkout', '-q', A, cwd=att)
sh('git', 'config', 'user.name', 'Orchestrator', cwd=att); sh('git', 'config', 'user.email', 'o@example.invalid', cwd=att)
c = json.load(open(repo / '.agent/contracts/104.json')); c['status'] = 'approved'
json.dump(c, open(att / '.agent/contracts/104.json', 'w'), indent=2); (att / '.agent/contracts/104.json').write_text((att / '.agent/contracts/104.json').read_text() + '\n')
(att / '.agent/validator').mkdir(exist_ok=True); shutil.copy(repo / '.agent/validator/104-mode-a.json', att / '.agent/validator/')
sh('git', 'add', '-A', cwd=att); r = sh('git', 'commit', '-q', '-m', 'B: approved contract', cwd=att); assert r.returncode == 0, r.stderr
B = sh('git', 'rev-parse', 'HEAD', cwd=att).stdout.strip()
ev = att / '.agent/evidence/104'; ev.mkdir(parents=True)
(ev / 'attempt-base.txt').write_text('git rev-parse HEAD\n%s\nEXIT:0\n' % B)
assert subprocess.run([sys.executable, str(H / 'implement.py'), str(att)]).returncode == 0
names = ['AT1','AT2','AT3','AT4','AT9','AT10'] + ['S%02d' % i for i in range(1, 10)]
for n in names:
    cmd = (H / 'cmds' / (n + '.sh')).read_text()
    if n == 'S02': continue
    ef = [v['evidence_file'] for v in c['verification']][(['AT1','AT2','AT3','AT4','AT5','AT6','AT7','AT8','AT9','AT10'] + ['S%02d' % i for i in range(1, 12)]).index(n)]
    p = subprocess.run(['bash', '-c', cmd], cwd=att, capture_output=True, text=True)
    (att / ef).write_text(cmd.splitlines()[0] + '\n' + p.stdout + p.stderr + 'EXIT:%d\n' % p.returncode)
    print(n, 'rc', p.returncode); sys.stdout.flush()
# S02 evidence last (needs everything final)
cmd = (H / 'cmds' / 'S02.sh').read_text()
p = subprocess.run(['bash', '-c', cmd], cwd=att, capture_output=True, text=True)
print('S02 pre-commit rc', p.returncode, (p.stdout + p.stderr).strip().splitlines()[-1][:300])
(att / '.agent/evidence/104/s02-attempt-root-delta.txt').write_text(cmd.splitlines()[0] + '\n' + p.stdout + p.stderr + 'EXIT:%d\n' % p.returncode)
sh('git', 'add', '-A', cwd=att); r = sh('git', 'commit', '-q', '-m', 'Attempt: feature 104', cwd=att); assert r.returncode == 0, r.stderr
print('attempt commit', sh('git', 'rev-parse', '--short', 'HEAD', cwd=att).stdout.strip(), 'B', B[:12], 'porcelain lines', len(sh('git', 'status', '--porcelain', cwd=att).stdout.splitlines()))
