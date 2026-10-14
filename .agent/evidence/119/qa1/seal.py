"""Seal fresh QA's observed results and raw file identities; no lifecycle mutation."""
import hashlib
import json
from pathlib import Path
import subprocess
import jsonschema

root = Path(__file__).resolve().parents[4]
e = root/'.agent/evidence/119/qa1'
read = lambda p: json.loads(p.read_bytes())
def write(p, value): p.write_text(json.dumps(value, indent=2)+'\n')
summary = read(e/'execution-summary.json')
assert summary['all_commands_passed'] is True and summary['protected_identities_unchanged'] is True
assert len(summary['results']) == 14
before = read(e/'identity-before.json'); assert before == read(e/'identity-after.json')
contract_checks = [r for r in summary['results'] if r['name'].startswith('case-')]
assert len(contract_checks) == 6 and all(r['exit_code'] == 0 for r in contract_checks)
verdict = {
    'feature_id':'119', 'qa_pass':True, 'actor':'/root/qa119', 'attempt':1,
    'reviewed_revision':summary['revision'],
    'approved_input':'8c50ec1e8a8bd44eb7e484929551f5c633fd7f58',
    'source_commit':'9ef2db5b0106c7f92520d18015562c85faf64fc2',
    'test_commit':'833b97b2116d630c4af937e23b7ad89eb442ee77',
    'approved_contract_sha256':before['files']['.agent/contracts/119.json']['sha256'],
    'checks_run':6, 'checks_passed':6,
    'checks':[{'command':'PYTHONDONTWRITEBYTECODE=1 '+' '.join(r['argv']), 'exit_code':r['exit_code'], 'evidence':'.agent/evidence/119/qa1/'+r['name']+'.result.json'} for r in contract_checks],
    'supplementary_checks':{r['name']:{'exit_code':r['exit_code'],'passed':r['passed'],'evidence':'.agent/evidence/119/qa1/'+r['name']+'.result.json'} for r in summary['results'] if not r['name'].startswith('case-') and r['name'] != 'adversarial'},
    'adversarial':{'performed':True,'count':1},
    'adversarial_check':{'description':'Actual carried-ledger mapping under side-effect-denying audit hook with real blocked write-attempt control', 'result':'pass', 'evidence':'.agent/evidence/119-qa-adversarial.txt'},
    'evidence_files':['.agent/evidence/119/qa1/execution-summary.json','.agent/evidence/119/qa1/identity-before.json','.agent/evidence/119/qa1/identity-after.json','.agent/evidence/119/qa1/historical-identity.json','.agent/evidence/119/qa1/environment.json','.agent/evidence/119/qa1/manifest.json','.agent/evidence/119/qa1/schema-check.json','.agent/evidence/119-qa-adversarial.txt']+[c['evidence'] for c in []],
    'issues':[], 'missing_acceptance_coverage':[], 'unsupported_claims':[], 'required_fixes':[],
    'final_verdict':{'approved':True,'summary':'Six exact selectors and preserved default26 pass; inherited source/API AST and old acceptance functions unchanged. Immutable118 foundation succeeds while live119 rejects stale118 source binding with the exact expected diagnostic. Default/payload compliance and exactly one independent purity check pass; protected source/test/contract/239 installed files unchanged.'},
    'boundary':'Historical foundation success is bound to immutable8ac94f6808e8197111197c9acbf59b2aa92efc7c without a119contract. Live119 rejection is expected semantic source mismatch, not setup. Earlier helper HEAD-preflight failure remains preserved; helper2 actual0 and semanticQA1 executed once. QA does not complete lifecycle, replace Root capture, claim123 or comparative superiority.',
    'dod_ref':'.nizam/standard/definition_of_done.md'
}
verdict['evidence_files'] += [c['evidence'] for c in verdict['checks']]
path = root/'.agent/qa/119.json'; assert not path.exists(); write(path, verdict)
schema = root/'.nizam/schema/qa_verdict.schema.json'
jsonschema.validate(verdict, read(schema))
write(e/'schema-check.json', {'command':'PYTHONDONTWRITEBYTECODE=1 python3 .agent/evidence/119/qa1/seal.py', 'cwd':str(root), 'schema':str(schema.relative_to(root)), 'schema_sha256':hashlib.sha256(schema.read_bytes()).hexdigest(), 'actual_exit_code':0, 'result':'jsonschema.validate returned normally; strict approved true and three exact empty arrays independently asserted'})
assert verdict['final_verdict']['approved'] is True and all(verdict[k] == [] for k in ('issues','missing_acceptance_coverage','unsupported_claims'))
paths = sorted([p for p in e.iterdir() if p.is_file() and p.name != 'manifest.json']+[root/'.agent/evidence/119-qa-adversarial.txt',path,root/'.agent/evidence/119/qa1-helper2.stdout.txt',root/'.agent/evidence/119/qa1-helper2.stderr.txt'])
files = {str(p.relative_to(root)):{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'git_blob':subprocess.check_output(['git','hash-object',str(p)],cwd=root).decode().strip(),'bytes':p.stat().st_size} for p in paths}
write(e/'manifest.json', {'role':'/root/qa119','reviewed_revision':summary['revision'],'files':files,'protected_inputs':before,'historical_inputs':read(e/'historical-identity.json'),'self_excluded':'Manifest omits its own recursive hash; Root verifies its committed Git blob.'})
print('PASS QA119 strict verdict/schema and '+str(len(files))+' actual raw/helper/verdict file pins')
