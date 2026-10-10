#!/usr/bin/env python3
"""05-tally.py : merge 04-mutants.txt with 04b-mutants-corrected.txt (04b supersedes the same ids) and print the tally and the survivor list."""
import re, pathlib
d = pathlib.Path('.agent/evidence/105-qa-adversarial-contract-review')
def parse(p):
    out = {}
    for l in (d / p).read_text().splitlines():
        m = re.match(r'^(\S+)\s+(CAUGHT|SURVIVED)\s+(.*?)\s+(\S+)\s+(\d+s)$', l)
        if m: out[m.group(1)] = (m.group(2), m.group(3), m.group(4))
    return out
a, b = parse('04-mutants.txt'), parse('04b-mutants-corrected.txt')
print('first run rows:', len(a), ' corrected rerun rows:', len(b), ' superseded ids:', sorted(b))
m = dict(a); m.update(b)
caught = {k: v for k, v in m.items() if v[0] == 'CAUGHT'}; surv = {k: v for k, v in m.items() if v[0] == 'SURVIVED'}
print('merged mutants:', len(m), 'caught:', len(caught), 'survived:', len(surv))
byprefix = {}
for k, v in m.items(): byprefix.setdefault(re.match(r'[a-z]+', k).group(0), []).append(v[0])
for k, v in sorted(byprefix.items()): print('  group %-3s mutants=%d caught=%d' % (k, len(v), v.count('CAUGHT')))
print('survivors:')
for k, v in sorted(surv.items()): print('  %-4s %s' % (k, v[1]))
firstcatch = {}
for k, v in caught.items(): firstcatch.setdefault(v[2].split(',')[0], []).append(k)
print('first catching check -> count:', {k: len(v) for k, v in sorted(firstcatch.items())})
