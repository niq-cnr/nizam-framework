#!/usr/bin/env python3
"""runall.py TREE [IDS...] : run the contract's verification commands (helpers/cmds/*.sh) sequentially with cwd=TREE,
print id, exit code (read from the process, no pipelines), and the last lines of output."""
import subprocess, sys, os, time
tree = sys.argv[1]
here = os.path.dirname(os.path.abspath(__file__))
ids = sys.argv[2:] or ['AT%d' % i for i in range(1, 9)] + ['S%02d' % i for i in range(1, 17)]
tail = int(os.environ.get('TAIL', '6'))
for i in ids:
    t = time.time()
    p = subprocess.run(['bash', os.path.join(here, 'cmds', i + '.sh')], cwd=tree, capture_output=True, text=True)
    out = (p.stdout + p.stderr).rstrip('\n').splitlines()
    print('### %s rc=%d (%.1fs)' % (i, p.returncode, time.time() - t))
    for l in out[-tail:]: print('    ' + l[:260])
