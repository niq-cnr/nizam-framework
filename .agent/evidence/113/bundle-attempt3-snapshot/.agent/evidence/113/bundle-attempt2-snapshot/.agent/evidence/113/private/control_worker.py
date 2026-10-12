#!/usr/bin/env python3
"""Scratch component checks. This emits CONTROL only, never acceptance verdicts."""
import importlib.util
from pathlib import Path
import sys

spec = importlib.util.spec_from_file_location('feature113', Path(__file__).resolve().parents[1] / 'check_113.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)
root, name = Path(sys.argv[1]).resolve(), sys.argv[2]
assert root != c.HERE.parents[2] and 'nizam113-controls-' in str(root)
functions = {'surface':c.surface_content, 'routing':c.routing, 'compatibility':c.compatibility,
             'delta':c.bounded_delta, 'history':c.history, 'lifecycle':c.lifecycle,
             'claim':c.claim_boundary, 'budget':c.budget_actual}
try:
    if name == 'integrity':
        c.integrity_data(root, c.js(root,'.agent/evidence/113/fixed-inputs.json'),
                         c.js(root,'.agent/evidence/113/fixed-inputs-seal.json'),
                         c.js(root,'.agent/evidence/113/current-source-inputs.json'),
                         c.js(root,'.agent/evidence/113/current-source-seal.json'))
    else:
        functions[name](root)
    print('CONTROL_COMPONENT:' + name + ':PASS')
except (c.Failure, ValueError, KeyError, OSError) as error:
    print('CONTROL_COMPONENT:FAIL:' + str(error), file=sys.stderr)
    sys.exit(1)
