from pathlib import Path
import datetime
import hashlib
import importlib.util
import json
import os
import subprocess
import sys

root = Path('/home/cnross/code/audit-remediation/nizam-framework-prerelease-selfinstall')
os.chdir(root)
expected = '7af4273e6e2a55f5371eec8241d5c1c2e341cf30'
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
assert head == expected
assert not subprocess.check_output(['git', 'status', '--porcelain'], text=True)
assert not subprocess.check_output(['git', 'ls-files', '--others', '-z'])
assert sys.dont_write_bytecode
evidence = Path('.agent/evidence/release-v3.1.2')
freeze = json.loads((evidence / 'source-freeze.json').read_text())
for group in ('source_sha256', 'inherited_component_sha256'):
    for name, expected_hash in freeze[group].items():
        assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == expected_hash, name
verdict = json.loads((evidence / 'reviewer-outputs/validator-modeB.json').read_text())
assert verdict['final_verdict']['approved'] is True
contract_path = '.agent/contracts/release-v3.1.2.json'
contract = json.loads(Path(contract_path).read_text())
assert contract['status'] == 'approved'
lineage = contract['budget_lineage']
ledger_path = Path(lineage['root_ledger_ref'])
authority_path = Path(lineage['user_recovery_ref'])
ledger_bytes, authority_bytes = ledger_path.read_bytes(), authority_path.read_bytes()
ledger, authority = json.loads(ledger_bytes), json.loads(authority_bytes)
assert ledger['task_id'] == lineage['logical_task'] == 'F05-current-state-qualification'
assert ledger['known_failures'] < ledger['task_limit'] == authority['total_failure_ceiling'] == 50
assert 'held' not in ledger['status'].lower() and 'exhaust' not in ledger['status'].lower()
os.environ['F05_LOGICAL_BUDGET_LEDGER_SHA256'] = hashlib.sha256(ledger_bytes).hexdigest()
os.environ['F05_USER_AUTHORITY_SHA256'] = hashlib.sha256(authority_bytes).hexdigest()
spec = importlib.util.spec_from_file_location('independent_prerelease_installed_assurance', root / '.nizam/tools/workflow_assurance.py')
wa = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = wa
spec.loader.exec_module(wa)
checks = wa.qa_required_checks(contract['verification'])
context = wa.qa_context_sha256(root, contract['contract_id'], [contract_path], checks)
os.environ[wa.QA_CONTEXT_VARIABLE] = context
os.environ[wa.QA_EXECUTION_ROOT_VARIABLE] = str(root)
tracked = [p for p in subprocess.check_output(['git', 'ls-files', '-z']).decode().split('\0') if p]
tests = [p for p in tracked if (p.startswith('tools/') and
         (Path(p).name.startswith('test_') or p.startswith('tools/fixtures/'))) or
         (p.startswith('.github/scripts/') and Path(p).name.startswith('test_'))]
tools = [p for p in tracked if p.startswith('tools/') and p not in tests]
tools += [p for p in tracked if p in ('.nizam/tools/start_path.py', '.nizam/tools/workflow_assurance.py',
          '.nizam/tools/git_seam.py', '.nizam/schema/qa_verdict.schema.json', '.nizam/schema/contract.schema.json')]
source = [p for p in tracked if not p.startswith(('.agent/', '.nizam/', 'tools/')) and p not in tests]
source += [p for p in tracked if p in ('.nizam/NIZAM.json', '.nizam/provenance.json',
          '.nizam/tools/SKILL.md', '.nizam/tools/skill.json')]
readiness_relative = '.agent/evidence/release-v3.1.2/readiness.json'
readiness = json.loads((root / readiness_relative).read_text())
self_install = readiness['prepublication_self_install']
references = [self_install[name] for name in ('authorization','qa_verdict','install_capture','integrity_capture','entrypoint_capture','readback_capture')]
application = json.loads(wa._qa_artifact(root, self_install['authorization']))
references.append(application['authority_ref'])
operation_qa = json.loads(wa._qa_artifact(root, self_install['qa_verdict']))
references.append(operation_qa['candidate_ref'])
for row in operation_qa['checks']:
    references.append(row['capture'])
    capture = json.loads(wa._qa_artifact(root, row['capture']))
    references += [capture['stdout'], capture['stderr']]
for claim in readiness['accepted_source_claims'].values():
    if isinstance(claim, dict):
        references += [claim[k] for k in ('qa','proof_consumption') if k in claim]
for reference in references: wa._qa_artifact(root, reference)
contracts = sorted(set([contract_path, readiness_relative] + [reference['path'] for reference in references]))
contracts += [p for p in tracked if p in ('.agent/contracts/120.json', '.agent/evidence/phase018-preflight/activation-authority.json')]
variables = [wa.QA_CONTEXT_VARIABLE, wa.QA_EXECUTION_ROOT_VARIABLE, 'PYTHONDONTWRITEBYTECODE',
             'PYTHONUNBUFFERED', 'GIT_CONFIG_GLOBAL', 'PATH', 'F05_LOGICAL_BUDGET_LEDGER_SHA256', 'F05_USER_AUTHORITY_SHA256']
candidate = wa.assess_repository(root, head, {'source': sorted(source), 'tests': sorted(tests),
          'tools': sorted(tools), 'contracts': sorted(contracts), 'unknown_dependencies': []}, variables)
wa.validate_qa_context(root, contract['contract_id'], candidate, checks)
folder = evidence / 'independent-final'
folder.mkdir(exist_ok=False)
manifest = folder / 'assessed-candidate.json'
manifest.write_bytes(wa.canonical(candidate) + b'\n')
admission = {'at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'assessed_commit': head,
             'source_freeze': freeze, 'actual_environment': {n: os.environ[n] for n in variables},
             'root_ledger_at_admission': ledger, 'actual_user_authority': authority,
             'logical_task': lineage['logical_task'], 'root_ledger_ref': str(ledger_path),
             'user_authority_ref': str(authority_path), 'new_allowance': False, 'history_reset': False,
             'scope': 'Three final release checks after accepted actual PRIMARY self-install. No core/operation repeats, source merge, tag/publication, service activation or model call.'}
(folder / 'assessment-admission.json').write_text(json.dumps(admission, indent=2) + '\n')

for check in contract['verification']:
    current_encoded = ledger_path.read_bytes()
    current = json.loads(current_encoded)
    assert current['task_id'] == 'F05-current-state-qualification' and current['known_failures'] < current['task_limit'] == 50
    assert 'held' not in current['status'].lower() and 'exhaust' not in current['status'].lower()
    (folder / (check['id'] + '.admission.json')).write_text(json.dumps({'at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'actual_root_ledger': current, 'root_ledger_sha256': hashlib.sha256(current_encoded).hexdigest(), 'candidate_environment_ledger_hash_is_assessment_snapshot': True}, indent=2) + '\n')
    argv = ['python3', '.nizam/tools/start_path.py', 'capture', '--root', str(root), '--id', contract['contract_id'], '--step', check['id'], '--attempt', '1', '--candidate', str(manifest), '--output-dir', str(folder), '--proof-kind', check['proof_kind'], '--timeout-sec', '900', '--agent-id', 'independent_acceptance', '--session-id', 'F05-framework-final-release-20261029']
    for name in variables: argv += ['--env-var', name]
    argv += ['--', *check['argv']]
    result = subprocess.run(argv, env=os.environ, text=True, capture_output=True)
    (folder / (check['id'] + '.producer.stdout')).write_text(result.stdout)
    (folder / (check['id'] + '.producer.stderr')).write_text(result.stderr)
    matching = [json.loads(p.read_text()) for p in folder.glob('*.capture.json') if json.loads(p.read_text())['step'] == check['id']]
    if len(matching) != 1:
        print(json.dumps({'verification': check['id'], 'producer_exit': result.returncode, 'actual_capture_count': len(matching)}), flush=True)
        sys.stdout.write(result.stdout);sys.stderr.write(result.stderr);sys.exit(result.returncode or 1)
    capture = matching[0]
    print(json.dumps({'verification': check['id'], 'producer_exit': result.returncode, **{k:capture[k] for k in ('outcome','exit_code','completion_state','duration_ms','capture_path')}}), flush=True)
    if result.returncode or capture['outcome'] != 'success' or type(capture['exit_code']) is not int or capture['exit_code'] != 0 or capture['completion_state'] != 'completed' or capture['signal'] is not None: sys.exit(result.returncode or 1)
