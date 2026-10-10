#!/usr/bin/env python3
"""gen_attempt.py ROOT : simulate a faithful Generator attempt in ROOT/att (scratch only).
B = A + the contract with status 'approved' (what the Orchestrator commits); attempt-base.txt first; implement.py; the 15 generator
evidence files captured in the 04 Section-5 shape (line 1 = first line of the command, verbatim output, EXIT:<code> from the process);
ONE commit. S02 is run before and after the commit."""
import json, pathlib, shutil, subprocess, sys
root = pathlib.Path(sys.argv[1]); H = pathlib.Path(__file__).resolve().parent
repo = pathlib.Path.cwd()
A = '2a537644dc93cc71786e6468c8f4295079d1c973'
sh = lambda *a, cwd=None: subprocess.run(a, cwd=cwd, capture_output=True, text=True)
shutil.rmtree(root, ignore_errors=True); root.mkdir(parents=True)
att = root / 'att'
assert sh('git', 'clone', '-q', str(repo), str(att)).returncode == 0
sh('git', '-c', 'advice.detachedHead=false', 'checkout', '-q', A, cwd=att)
sh('git', 'config', 'user.name', 'Orchestrator', cwd=att); sh('git', 'config', 'user.email', 'o@example.invalid', cwd=att)
c = json.load(open(repo / '.agent/contracts/105.json')); c['status'] = 'approved'
(att / '.agent/contracts/105.json').write_text(json.dumps(c, indent=2) + '\n')
sh('git', 'add', '-A', cwd=att); r = sh('git', 'commit', '-q', '-m', 'B: approved contract', cwd=att); assert r.returncode == 0, r.stderr
B = sh('git', 'rev-parse', 'HEAD', cwd=att).stdout.strip()
ev = att / '.agent/evidence/105'; ev.mkdir(parents=True)
(ev / 'attempt-base.txt').write_text('git rev-parse HEAD\n%s\nEXIT:0\n' % B)
assert subprocess.run([sys.executable, str(H / 'implement.py'), str(att)]).returncode == 0
order = ['AT1','AT2','AT3','AT4','AT5'] + ['S%02d' % i for i in range(1, 10)]
efile = {n: v['evidence_file'] for n, v in zip(['AT1','AT2','AT3','AT4','AT5'] + ['S%02d' % i for i in range(1, 10)], c['verification'])}
for n in ['AT1','AT2','AT3','AT4','AT5','S01','S04','S05','S06','S07','S08','S09']:
    cmd = (H / 'cmds' / (n + '.sh')).read_text()
    p = subprocess.run(['bash', '-c', cmd], cwd=att, capture_output=True, text=True)
    (att / efile[n]).write_text(cmd.splitlines()[0] + '\n' + p.stdout + p.stderr + 'EXIT:%d\n' % p.returncode)
    print(n, 'rc', p.returncode); sys.stdout.flush()
for n in ['S02', 'S03']:
    cmd = (H / 'cmds' / (n + '.sh')).read_text()
    p = subprocess.run(['bash', '-c', cmd], cwd=att, capture_output=True, text=True)
    print(n, 'pre-commit rc', p.returncode, (p.stdout + p.stderr).strip().splitlines()[-1][:300])
    (att / efile[n]).write_text(cmd.splitlines()[0] + '\n' + p.stdout + p.stderr + 'EXIT:%d\n' % p.returncode)
sh('git', 'add', '-A', cwd=att); r = sh('git', 'commit', '-q', '-m', 'Attempt: feature 105', cwd=att); assert r.returncode == 0, r.stderr
print('attempt commit', sh('git', 'rev-parse', '--short', 'HEAD', cwd=att).stdout.strip(), 'B', B[:12], 'porcelain lines', len(sh('git', 'status', '--porcelain', cwd=att).stdout.splitlines()))
