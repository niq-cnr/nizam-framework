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
             'delta':c.bounded_delta, 'history':c.history, 'production-lifecycle':c.lifecycle,
             'claim':c.claim_boundary, 'budget':c.budget_actual, 'debt':c.debt}
try:
    if name in ('debt-models','lifecycle'):
        model_spec=importlib.util.spec_from_file_location('model', c.RECOVERY/'control_models.py')
        model=importlib.util.module_from_spec(model_spec);model_spec.loader.exec_module(model)
        if name=='lifecycle':model.lifecycle_control(c,root)
        else:
            recovered=c.read(c.RECOVERY,'debt-recovery.md')
            c.debt_text(c.read(c.RECOVERY,'debt-original.md'),c.read(c.HERE,'recovery-debt-halt.md'),
                        recovered,model.resolved_debt(recovered),allow_resolved=True)
    elif name == 'integrity':
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
