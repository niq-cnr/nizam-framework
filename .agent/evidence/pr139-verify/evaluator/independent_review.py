"""Independent committed parent preservation and applicable document checks."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import yaml
import jsonschema
ROOT = Path.cwd().resolve()
BASE = '52a91abbee308282e24a5296d3597e9494e9a849'
PR = '65036ef8eea1eef4dcf9a3a772570736a0baf499'
OLD_PR = 'db3e8431146ad40584cd577b26cbf542e25b12d5'
def read(rev, path):
    return subprocess.check_output(['git','show',rev+':'+path])
def parsed(data):
    header, body = data.decode().split('\n---\n', 1)
    return yaml.safe_load(header.removeprefix('---\n')), body
assert subprocess.check_output(['git','show','-s','--format=%P',PR],text=True).strip().split() == [OLD_PR, BASE]
change = Path('CHANGELOG.md').read_bytes()
main_change = read(BASE,'CHANGELOG.md')
assert change[change.index(b'## [3.0.0]'):] == main_change[main_change.index(b'## [3.0.0]'):]
assert change.split(b'## [Unreleased]\n',1)[1].split(b'\n## [',1)[0] == read(OLD_PR,'CHANGELOG.md').split(b'## [Unreleased]\n',1)[1].split(b'\n## [',1)[0]
meta, body = parsed(Path('docs/planning/ROADMAP.md').read_bytes())
main_meta, main_body = parsed(read(BASE,'docs/planning/ROADMAP.md'))
pr_meta, pr_body = parsed(read(OLD_PR,'docs/planning/ROADMAP.md'))
expected = dict(main_meta,version='0.65.38',change_log=[dict(pr_meta['change_log'][0],version='0.65.38'),*main_meta['change_log']])
assert meta == expected
begin='## Approved backlog additions — 2026-10-27'
finish='## Current position — Jev readiness program, 2026-10-22'
addition=body[body.index(begin):body.index(finish)]
assert addition == pr_body[pr_body.index(begin):pr_body.index(finish)]
assert body.replace(addition,'',1) == main_body
schema=json.loads(Path('schema/frontmatter.schema.json').read_text())
links=[]
for path,selected in [('docs/planning/ROADMAP.md',addition),('docs/planning/API_REFERENCE_PILOT.md',Path('docs/planning/API_REFERENCE_PILOT.md').read_text())]:
    metadata,_=parsed(Path(path).read_bytes())
    jsonschema.validate(metadata,schema)
    assert metadata['authoritative_source']==path
    for target in re.findall(r'\]\(([^)\s]+)\)',selected):
        if target.startswith(('http:','https:','#')):continue
        resolved=Path(path).parent/target.split('#',1)[0]
        assert resolved.is_file(),str(resolved)
        links.append(str(resolved))
files={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in ['CHANGELOG.md','docs/planning/ROADMAP.md','docs/planning/API_REFERENCE_PILOT.md']}
print(json.dumps({'assessed_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'PR_parents':[OLD_PR,BASE],'assessed_files':files,'releases':'main v3 and prior bytes preserved','backlog':'PR API block, main NF/current position and historical metadata preserved','frontmatter':'two governed planning docs valid','local_links':links,'source_changes':'none by Evaluator'},sort_keys=True))
