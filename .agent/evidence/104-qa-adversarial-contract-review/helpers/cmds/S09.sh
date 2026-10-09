python3 - <<'PY'
import re, subprocess, sys
p = subprocess.run(['bash', 'tools/validate.sh'], capture_output=True, text=True)
o = p.stdout + p.stderr
passes = re.findall(r'^\[C(\d+)\] PASS', o, re.M)
fails = re.findall(r'^\[C(\d+)\] FAIL', o, re.M)
s = re.findall(r'^SUMMARY: (\d+) passed, (\d+) failed$', o, re.M)
ok = p.returncode == 0 and not fails and s == [('16', '0')] and len(passes) == 16 and '[C14] PASS workflow-sha-pins' in o
print('exit:', p.returncode, 'PASS lines:', len(passes), 'FAIL lines:', fails, 'SUMMARY:', s, 'C14:', '[C14] PASS workflow-sha-pins' in o)
sys.exit(0 if ok else 1)
PY
