#!/usr/bin/env python3
"""extract_cmds.py CONTRACT OUTDIR : write the contract's 14 verification commands verbatim as OUTDIR/{AT1..AT5,S01..S09}.sh (no hand copying)."""
import json, sys, pathlib
c = json.load(open(sys.argv[1])); out = pathlib.Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
n_at = n_s = 0
for v in c['verification']:
    if v.get('supplementary'):
        n_s += 1; name = 'S%02d' % n_s
    else:
        n_at += 1; name = 'AT%d' % n_at
    (out / (name + '.sh')).write_text(v['command'] + '\n')
print('extracted', n_at, 'AT', n_s, 'S')
