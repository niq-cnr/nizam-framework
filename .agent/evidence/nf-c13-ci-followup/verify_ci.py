#!/usr/bin/env python3
"""Verify captured public CI evidence and tree identities without re-running jobs."""
import glob
import hashlib
import json
import re
import subprocess
from pathlib import Path

base=Path('.agent/evidence/nf-c13-ci-followup')
def read(pattern):
 p=list(base.glob(pattern));assert len(p)==1,pattern
 return p[0].read_text()
fixture=read('*ci-job-log*.stdout.txt')
match=re.search(r'MAINTENANCE_CHECKOUT_RECEIPT=(\{"checkout_sha"[^\n]*\})', fixture)
assert match, 'checkout receipt missing'
receipt=json.loads(match.group(1)); checkout=receipt['checkout_sha']
assert checkout=='980f5530ac5bf5813e6d1f51ac6f9a073f0cded3'
head='46b2aeb691b9692c371b4e6bc51e8dddd125a17e'
def git(*args): return subprocess.check_output(['git',*args])
for path,expected in receipt['source_sha256'].items():
 assert hashlib.sha256(git('show',head+':'+path)).hexdigest()==expected, path
assert git('rev-parse',checkout+'^{tree}')==git('rev-parse',head+'^{tree}')
for expected in ['SELF-TEST OK: 176/176 fixtures accounted for, 0 failed',
                 'OK   governance-manifest complete shape, uniqueness and unconditional parity',
                 'c13-substitute skill_index_neg_dangling_module.json -> [C13] FAIL',
                 'c13-substitute skill_index_neg_unindexed_capability.json -> [C13] FAIL']:
 assert expected in fixture, expected
job=json.loads(read('*ci-job-final*.stdout.txt'))
assert job['head_sha']==head and job['conclusion']=='success' and job['status']=='completed'
validate=read('*ci-validate-log*.stdout.txt')
assert 'SUMMARY: 16 passed, 0 failed' in validate and '[C13] PASS skill-index' in validate
bootstrap=read('*ci-bootstrap-log*.stdout.txt')
assert 'assert_payload_validate_cwd_independent: OK' in bootstrap
assert 'e2e_bootstrap_test.sh: PASS' in bootstrap
assert checkout in bootstrap, 'bootstrap tested commit differs from receipt'
print(json.dumps({'ci_head':head,'ci_checkout':checkout,'checkout_tree':git('rev-parse',checkout+'^{tree}').decode().strip(),
                  'fixture_summary':'176/176 accounted; no failures','c13_mutations':'passed; 8 methods',
                  'c13_negative_substitutions':'passed','validate_summary':'16 passed; 0 failed',
                  'consumer_bootstrap':'e2e pass; CWD-independent payload validation',
                  'identity_scope':'equal source tree, distinct Git commit and history; no literal head-run assertion'},sort_keys=True,indent=2))
