"""Pre-code contract review only; missing future selectors are setup failures."""
import hashlib, importlib.util, json, os, pathlib, subprocess, sys
import jsonschema
ROOT = pathlib.Path(__file__).resolve().parents[3]
os.chdir(ROOT)
def read(path):
    return json.loads(pathlib.Path(path).read_text())
def load(path):
    spec = importlib.util.spec_from_file_location('review_' + pathlib.Path(path).stem, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module
contract = read('.agent/contracts/119.json')
assert hashlib.sha256(pathlib.Path('.agent/contracts/119.json').read_bytes()).hexdigest() == '9de754f810676e2f154aca96cb28c75236ac650ab78a0e06f53f97d66e885226'
jsonschema.validate(contract, read('.nizam/schema/contract.schema.json'))
feature = read('.agent/feature_list_018.json')['features'][0]
commands = [row['command'] for row in contract['verification']]
assert commands == feature['acceptance_tests'] and len(set(commands)) == 6
assert contract['status'] == 'proposed' and contract['estimated_lines'] == feature['estimated_lines'] == 1000
assert [contract['budget'][k] for k in ('product', 'independent_tests', 'process')] == [200, 300, 500]
assert [contract['budget'][k] for k in ('phase_original', 'phase_ceiling')] == [7200, 9360]
assert contract['budget']['measurement_base'] == 'fcd0584146fd836df0080292cc2cf10180bb9f31'
activation = read('.agent/evidence/phase018-preflight/activation-result.json')
assert activation['passed'] is True and activation['selected'] == '119' and activation['historical016'] == 5179
gate = read('.agent/evidence/phase018-preflight/activation-review.json')
assert gate['final_verdict']['approved'] is True and all(gate[k] == [] for k in ('issues', 'missing_acceptance_coverage', 'unsupported_claims'))
runner = load('tools/test_workflow_assurance.py'); api = load('tools/workflow_assurance.py')
assert len(runner.CASES) == len(set(runner.CASES)) == 20 and not hasattr(api, 'convergent_agf_verdict')
assert all(command.split()[-1] not in runner.CASES for command in commands)
revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
assert revision == '667ce42930ae76000b1b7ade047b7ad520104d35'
receipt = {'reviewer': '/root/evaluator119', 'revision': revision, 'cwd': str(ROOT), 'environment': {'PYTHONDONTWRITEBYTECODE': os.environ.get('PYTHONDONTWRITEBYTECODE')}, 'commands': []}
paths = ['AGENTS.md', '.nizam/NIZAM.json', '.nizam/tools/SKILL.md', '.nizam/methodology/01_execution.md', '.nizam/methodology/02_adversarial_tdd.md', '.agent/contracts/119.json', '.agent/product_spec_018.md', '.agent/feature_list_018.json', 'docs/planning/phase_018.yaml', 'tools/workflow_assurance.py', 'tools/test_workflow_assurance.py', 'tools/convergent_review.py', '.github/workflows/compliance.yml']
receipt['inputs'] = {p: {'sha256': hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest(), 'git_object': subprocess.check_output(['git', 'rev-parse', 'HEAD:' + p], text=True).strip()} for p in paths}
for command in commands:
    name = command.split()[-1]
    argv = command.split()[1:]
    result = subprocess.run(argv, capture_output=True, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
    prefix = '.agent/evidence/119/contract-review1-' + name
    pathlib.Path(prefix + '.stdout.txt').write_bytes(result.stdout)
    pathlib.Path(prefix + '.stderr.txt').write_bytes(result.stderr)
    receipt['commands'].append({'command': command, 'argv': argv, 'exit': result.returncode, 'stdout': prefix + '.stdout.txt', 'stderr': prefix + '.stderr.txt', 'classification': 'expected pre-code setup absence; not semantic red'})
    assert result.returncode == 2 and b'invalid choice' in result.stderr and b'PASS ' not in result.stdout
pathlib.Path('.agent/evidence/119/contract-review1-check-result.json').write_text(json.dumps(receipt, indent=2) + '\n')
print('PASS contract/schema/plan/budget/activation; existing inventory20; six absent selectors each setup exit2, no semantic-red claim')
