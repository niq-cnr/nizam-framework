import json, re, subprocess
from pathlib import Path
import jsonschema, yaml
base = '6770458'
spec = Path('.agent/product_spec_018.md').read_text()
new = json.loads(Path('.agent/feature_list_018.json').read_text())
old = json.loads(subprocess.check_output(['git', 'show', base + ':.agent/feature_list_018.json']))
jsonschema.validate(yaml.safe_load(spec.split('---', 2)[1]), json.loads(Path('.nizam/schema/frontmatter.schema.json').read_text()))
jsonschema.validate(new, json.loads(Path('.nizam/schema/feature_list.schema.json').read_text()))
assert new['features'] == old['features'] and new['phase_status'] == 'pending'
assert all(new[k] == old[k] for k in old if k not in ('spec_version', 'cross_phase_prerequisites', 'activation_prerequisites'))
assert [x['requires'] for x in new['cross_phase_prerequisites']] == [['118'], ['127']]
for x in new['cross_phase_prerequisites']:
    receipt = json.loads(Path(x['evidence'][0]).read_text()); assert receipt['passed']
for link in re.findall(r'\]\(([^)]+)\)', spec): assert (Path('.agent') / link).is_file(), link
ci = json.loads(Path('.agent/evidence/128/pr99-main-ci.json').read_text())['run']
assert ci['headSha'].startswith('fcd0584') and ci['conclusion'] == 'success' and len(ci['jobs']) == 5
assert all(x['conclusion'] == 'success' for x in ci['jobs'])
assert 'Preserve historical A09-after-NIP3-120 edge' in spec and 'All commands in the list are future acceptance obligations; none is run here.' in spec
assert set(subprocess.check_output(['git', 'diff', '--name-only', base], text=True).splitlines()) == {'.agent/product_spec_018.md', '.agent/feature_list_018.json'}
print('PASS NDS/JSON schemas, unchanged features/dependencies/budgets/pending lifecycle, actual118/127 capture links, historical A09, postmerge mainCI; no acceptance executed')
