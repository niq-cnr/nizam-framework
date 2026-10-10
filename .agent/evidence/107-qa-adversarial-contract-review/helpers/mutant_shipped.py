import json, subprocess, sys
from pathlib import Path
code = 'p = root / "tools/validate.sh"\nt = p.read_text()\nold = "  files+=(\\"CONTEXT.md\\")\\n"\nnew = old + "  files+=(\\"docs/nips/NIP-0001-ecosystem-engineering-cycle.md\\")\\n"\nassert t.count(old) == 1, t.count(old)\np.write_text(t.replace(old, new, 1))\nnip = root / "docs/nips/NIP-0001-ecosystem-engineering-cycle.md"\nsuffix = "\\n\\n```\\nuntagged probe\\n```\\n\\nSee docs/nips/DOES-NOT-EXIST.md for the probe.\\n"\nassert suffix not in nip.read_text()\nnip.write_text(nip.read_text() + suffix)\n'
argv = [sys.executable, '.agent/evidence/phase-014-activation/gates/scratch_run.py', '--py-mutate', code, '--expect-rc', '1', '--expect', r'^\[C3\] FAIL', '--expect', r'^\[C9\] FAIL', '--expect', 'DOES-NOT-EXIST', '--', 'bash', 'tools/validate.sh']
proc = subprocess.run(argv)
sys.exit(proc.returncode)
