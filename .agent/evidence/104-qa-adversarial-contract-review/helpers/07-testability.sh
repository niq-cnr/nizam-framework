# Testability: static scan of the 21 commands + determinism (three consecutive passes of the fast checks, slow checks repeated) in the positive-control tree. Strictly sequential.
set -u
H=$PWD/.agent/evidence/104-qa-adversarial-contract-review/helpers
python3 -I - <<'PY'
import re, pathlib
bad = []
for p in sorted(pathlib.Path('.agent/evidence/104-qa-adversarial-contract-review/helpers/cmds').glob('*.sh')):
    t = p.read_text()
    flags = []
    if re.search(r'/home/|/tmp/|/usr/|/Users/', t): flags.append('absolute path')
    if '|| true' in t or '| tee' in t: flags.append('masking pipe')
    if re.search(r'\bcurl\b|\bwget\b|http', t): flags.append('network')
    if re.search(r'\bsudo\b|sysctl -w', t.replace("'sudo'", '').replace('sudo sysctl -w kernel.apparmor_restrict_unprivileged_userns=0', 'GUARD-TEXT-ONLY')): flags.append('sudo/sysctl write')
    live = bool(re.search(r"'gh'|\bgh\b", t))
    print('%-5s %5d bytes  %s%s' % (p.stem, len(t), ','.join(flags) or 'clean', '  [live read-only gh at S10/S11 only]' if live else ''))
    if flags: bad.append((p.stem, flags))
print('flagged:', bad)
PY
echo "static scan rc=$?"
for run in 1 2 3; do echo "== fast pass $run"; TAIL=0 python3 "$H/runall.py" "$NIZAM_EVAL_SCRATCH/work/impl" AT1 AT2 AT3 AT4 S01 S03 S04 S05 S06 S07 | tail -n 1; done
for run in 2 3; do echo "== slow pass $run (AT9, AT10, S08, S09, one at a time)"; TAIL=0 python3 "$H/runall.py" "$NIZAM_EVAL_SCRATCH/work/impl" AT9 AT10 S08 S09 | tr '\n' ' '; echo; done
