#!/usr/bin/env python3
"""qa_run.py NAME... : Evaluator re-run of feature 105 verification commands, strictly sequential, from the repo root.
AT1-AT5 come from .agent/feature_list_014.json (feature 105) and S01,S03-S09 from .agent/contracts/105.json (S02 is attempt-root only).
Each capture is .agent/evidence/105/qa/<evidence basename> in the 04 Section 5 shape: line 1 the verbatim command
(first line for a heredoc), then verbatim stdout+stderr, last line EXIT:<code> read from the process."""
import json, os, subprocess, sys
c = json.load(open('.agent/contracts/105.json'))
f = next(x for x in json.load(open('.agent/feature_list_014.json'))['features'] if x['id'] == '105')
cmds, files = {}, {}
n_s = 0
n_at = 0
for v in c['verification']:
    if v.get('supplementary'):
        n_s += 1; name = 'S%02d' % n_s
    else:
        n_at += 1; name = 'AT%d' % n_at
        assert v['command'] == f['acceptance_tests'][n_at - 1], name
    cmds[name] = v['command']; files[name] = os.path.basename(v['evidence_file'])
env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
rcs = {}
for name in sys.argv[1:]:
    cmd = cmds[name]
    p = subprocess.run(['bash', '-c', cmd], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
    path = '.agent/evidence/105/qa/' + files[name]
    with open(path, 'wb') as fh:
        fh.write(cmd.split('\n')[0].encode() + b'\n')
        fh.write(p.stdout)
        if p.stdout and not p.stdout.endswith(b'\n'): fh.write(b'\n')
        fh.write(b'EXIT:%d\n' % p.returncode)
    rcs[name] = p.returncode
    print(name, 'rc=%d' % p.returncode, path)
    sys.stdout.flush()
sys.exit(0 if all(v == 0 for v in rcs.values()) else 1)
