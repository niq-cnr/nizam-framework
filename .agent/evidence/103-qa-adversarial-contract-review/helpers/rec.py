#!/usr/bin/env python3
"""rec.py OUTFILE CWD DISPLAY SCRIPTFILE : run bash SCRIPTFILE in CWD; write 04-s5 evidence (line1 invocation, output, EXIT:)."""
import subprocess, sys
out, cwd, display, script = sys.argv[1:5]
p = subprocess.run(['bash', script], cwd=cwd, capture_output=True, text=True)
body = p.stdout + p.stderr
with open(out, 'w') as f:
    f.write(display + '\n' + body)
    if body and not body.endswith('\n'): f.write('\n')
    f.write('EXIT:%d\n' % p.returncode)
print(open(out).read()[-3000:])
sys.exit(0)
