#!/usr/bin/env python3
"""gap_probes.py TREE SCENARIO : run one scenario the contract's 24 checks do not cover, against TREE (a scratch worktree).
Scenarios:
  flag_with_partial_capability : S10's shim (probe passes, full sandbox refused) PLUS --allow-unsupported-isolation.
  ordinary_skip_on_capable_host: capable-host shim (probe ok, sandbox exec'd without namespaces) and a jsonschema stub that raises ImportError,
                                 so only ORDINARY skipTests occur; required mode must still print CONFORMANCE: FULL / exit 0."""
import os, pathlib, re, subprocess, sys, tempfile
tree, scenario = pathlib.Path(sys.argv[1]), sys.argv[2]
with tempfile.TemporaryDirectory() as d:
    d = pathlib.Path(d); (d / 'bin').mkdir()
    shim = d / 'bin' / 'unshare'; env = dict(os.environ); args = []
    if scenario == 'flag_with_partial_capability':
        shim.write_text('#!/bin/sh\nif [ "$*" = "--user --map-root-user true" ]; then exit 0; fi\necho "simulated sandbox failure" >&2\nexit 97\n')
        args = ['--allow-unsupported-isolation']
    elif scenario == 'ordinary_skip_on_capable_host':
        shim.write_text('#!/bin/sh\nif [ "$*" = "--user --map-root-user true" ]; then exit 0; fi\nif [ "$3" = "--net" ]; then shift 8; exec "$@"; fi\nexit 98\n')
        (d / 'stub').mkdir(); (d / 'stub' / 'jsonschema.py').write_text('raise ImportError("jsonschema deliberately absent")\n')
        env['PYTHONPATH'] = str(d / 'stub')
    else: raise SystemExit('unknown scenario')
    shim.chmod(0o755); env['PATH'] = str(d / 'bin') + os.pathsep + env['PATH']
    p = subprocess.run([sys.executable, 'tools/test_convergent_review.py', *args], cwd=tree, env=env, capture_output=True, text=True)
out = p.stdout + p.stderr
print('scenario:', scenario, 'rc=%d' % p.returncode)
print('FAIL lines:', len(re.findall(r'^FAIL: test_', out, re.M)), 'UNSUPPORTED result lines:', len(re.findall(r"skipped 'UNSUPPORTED", out)), 'other skipped lines:', len(re.findall(r"skipped '(?!UNSUPPORTED)", out)))
print('CONFORMANCE lines:', re.findall(r'^CONFORMANCE:.*$', out, re.M))
sys.exit(0)
