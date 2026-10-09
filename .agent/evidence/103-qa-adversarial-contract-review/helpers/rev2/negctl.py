#!/usr/bin/env python3
"""negctl.py REPO_BASE_CLONE ATTEMPT_COMMIT WORKDIR CHECKS NAME... : for each mutant, add a detached worktree at the
attempt commit, inject the defect, run the listed checks sequentially (never concurrently), print rc per check, remove the worktree.
Exit status per check is read from the process (no pipelines)."""
import os, subprocess, sys
here = os.path.dirname(os.path.abspath(__file__))
clone, commit, work, checks = sys.argv[1:5]
names = sys.argv[5:]
checks = checks.split(',')
for name in names:
    wt = os.path.join(work, 'mut-' + name)
    subprocess.run(['git', '-C', clone, 'worktree', 'add', '-q', '--detach', wt, commit], check=True)
    try:
        subprocess.run([sys.executable, os.path.join(here, 'mutate.py'), name, wt], check=True)
        res = []
        for c in checks:
            env = dict(os.environ)
            cid = c
            if c.endswith('c') and c[:-1] in ('AT1', 'AT2', 'AT4'):
                cid = c[:-1]; env['PATH'] = os.path.join(os.environ['NIZAM_EVAL_SCRATCH'], 'capbin') + os.pathsep + env['PATH']
            p = subprocess.run(['bash', os.path.join(here, 'cmds', cid + '.sh')], cwd=wt, capture_output=True, text=True, env=env)
            res.append('%s=%d' % (c, p.returncode))
        print('%-62s %s' % (name, ' '.join(res)), flush=True)
    finally:
        subprocess.run(['git', '-C', clone, 'worktree', 'remove', '--force', wt], check=True)
