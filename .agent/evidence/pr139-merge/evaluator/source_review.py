"""Independent two-parent conflict preservation, metadata and local-link review."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import sys
import yaml
import jsonschema
root = Path.cwd().resolve()
sys.path.insert(0, str(root / 'tools'))
import start_path as sp
parents = {'pr': 'db3e8431146ad40584cd577b26cbf542e25b12d5',
           'main': '52a91abbee308282e24a5296d3597e9494e9a849'}
def blob(revision, path):
    return subprocess.check_output(['git', 'show', revision + ':' + path])
assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip() == parents['pr']
assert subprocess.check_output(['git','rev-parse','MERGE_HEAD'],text=True).strip() == parents['main']
changelog = Path('CHANGELOG.md').read_bytes()
roadmap = Path('docs/planning/ROADMAP.md').read_bytes()
main_change = blob(parents['main'], 'CHANGELOG.md')
pr_change = blob(parents['pr'], 'CHANGELOG.md')
assert changelog[changelog.index(b'## [3.0.0]'):] == main_change[main_change.index(b'## [3.0.0]'):]
def unreleased(value):
    return value.split(b'## [Unreleased]\n', 1)[1].split(b'\n## [', 1)[0]
assert unreleased(changelog) == unreleased(pr_change)
def parsed(value):
    header, body = value.decode().split('\n---\n', 1)
    return yaml.safe_load(header.removeprefix('---\n')), body
current_meta, current_body = parsed(roadmap)
main_meta, main_body = parsed(blob(parents['main'], 'docs/planning/ROADMAP.md'))
pr_meta, pr_body = parsed(blob(parents['pr'], 'docs/planning/ROADMAP.md'))
assert current_meta['version'] == '0.65.38'
expected_meta = dict(main_meta)
expected_meta['version'] = '0.65.38'
expected_meta['change_log'] = [dict(pr_meta['change_log'][0], version='0.65.38'), *main_meta['change_log']]
assert current_meta == expected_meta
begin = '## Approved backlog additions — 2026-10-27'
finish = '## Current position — Jev readiness program, 2026-10-22'
addition = current_body[current_body.index(begin):current_body.index(finish)]
assert addition == pr_body[pr_body.index(begin):pr_body.index(finish)]
assert current_body.replace(addition, '', 1) == main_body
jsonschema.validate(current_meta, json.loads(Path('schema/frontmatter.schema.json').read_text()))
links = []
for target in re.findall(r'\]\(([^)\s]+)\)', addition):
    assert not target.startswith(('http:', 'https:')), 'No external lookup belongs in this local check'
    assert (root / 'docs/planning' / target.split('#')[0]).is_file(), target
    links.append('docs/planning/' + target)
sp.verify_actual_changed_scope(root, 'trivial', ['CHANGELOG.md','docs/planning/ROADMAP.md'], 'pr139-merge')
files = {}
for path in ('CHANGELOG.md','docs/planning/ROADMAP.md'):
    data = Path(path).read_bytes()
    assert data == blob('', path), 'staged and assessed bytes differ'
    files[path] = hashlib.sha256(data).hexdigest()
print(json.dumps({'parents':parents,'assessed_files':files,'release_tail':'v3 and prior bytes preserved',
                  'unreleased':'PR API entry preserved byte-for-byte','roadmap':'main body and historical metadata retained; API block preserved',
                  'local_links':links,'frontmatter':'schema-valid v0.65.38','scope':'only declared conflict files; inherited staged changes preserved',
                  'qualification':'staged review only; no done-qualified committed-source proof'}, sort_keys=True))
