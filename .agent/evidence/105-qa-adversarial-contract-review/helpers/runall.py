#!/usr/bin/env python3
"""runall.py TREE [NAMES...] : run the contract's commands sequentially in TREE (never concurrently: C13 race); exit status read from each process.
Default set: AT1..AT5 S01 S03..S09 (S02 is attempt-root only)."""
import subprocess, sys, time, os, pathlib
H = pathlib.Path(os.environ.get('CMDS', pathlib.Path(__file__).resolve().parent / 'cmds'))
tree = sys.argv[1]
names = sys.argv[2:] or ['AT1','AT2','AT3','AT4','AT5','S01','S03','S04','S05','S06','S07','S08','S09']
tail = int(os.environ.get('TAIL', '2'))
rcs = {}
for n in names:
    t0 = time.time()
    p = subprocess.run(['bash', str(H / (n + '.sh'))], cwd=tree, capture_output=True, text=True)
    rcs[n] = p.returncode
    out = (p.stdout + p.stderr).strip().splitlines()
    print('### %s rc=%d (%.1fs)' % (n, p.returncode, time.time() - t0))
    for l in out[-tail:]:
        print('    ' + l[:300])
    sys.stdout.flush()
print('SUMMARY: ' + ' '.join('%s=%d' % kv for kv in rcs.items()))
sys.exit(0 if all(v == 0 for v in rcs.values()) else 1)
