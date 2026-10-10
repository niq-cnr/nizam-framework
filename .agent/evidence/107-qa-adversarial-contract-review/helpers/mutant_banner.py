import subprocess, sys
code = 'p = root / "tools/validate.sh"\nt = p.read_text()\nold = "  echo \\"[C1] FAIL frontmatter-schema\\"\\n"\nnew = "  echo \\"[C1] FAIL other-banner\\"\\n"\nassert t.count(old) == 1, t.count(old)\np.write_text(t.replace(old, new, 1))\n'
base = [sys.executable, '.agent/evidence/phase-014-activation/gates/scratch_run.py', '--replace', 'docs/nips/NIP-0001-ecosystem-engineering-cycle.md', 'status: active', 'status: accepted', '--py-mutate', code]
loose = base + ['--expect-rc', '1', '--expect', r'^\[C1\] FAIL', '--expect', r'NIP-0001-ecosystem-engineering-cycle\.md', '--', 'bash', 'tools/validate.sh']
exact = base + ['--expect-rc', '1', '--expect', r'^\[C1\] FAIL frontmatter-schema$', '--', 'bash', 'tools/validate.sh']
a = subprocess.run(loose)
print('LOOSE_AT2_EXIT', a.returncode)
b = subprocess.run(exact)
print('EXACT_BANNER_EXIT', b.returncode)
sys.exit(0 if a.returncode == 0 and b.returncode == 1 else 1)
