#!/usr/bin/env python3
"""Task-only structural planning checks; future runtime conformance is not run here."""
import argparse, copy, difflib, fnmatch, hashlib, json, pathlib, re, shlex, subprocess, tempfile
import jsonschema, yaml

ROOT = pathlib.Path(__file__).resolve().parents[3]
BASE = 'e22a3bf4c748cbd4f9daf9b0f66c4a0a6e5efc80'
AUTH_BASE = '3d9b24931ecad49221b8e8faffc12a7fc0fc1bf0'
APPROVED = '132480aab50424f8b3815fba7159b27a5a2bcfdc'
EXISTING_TASK = '84cc13da81ea3db65ea3f083030862982b086af8'
E = '.agent/evidence/workflow-016-planning/'
PHASES = ('017', '018', '019', '016', '020')
NIP3 = 'docs/nips/NIP-0003-live-runtime-sessions.md'
NIP4 = 'docs/nips/NIP-0004-workflow-assurance.md'

def require(ok, label):
    if not ok: raise ValueError(label)

def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args])

def original(path, base=BASE):
    return git('show', base + ':' + path)

def read(path):
    return json.loads((ROOT / path).read_text())

def schema(value, name):
    jsonschema.Draft202012Validator(read('.nizam/schema/' + name + '.schema.json')).validate(value)

def section(text, heading):
    match = re.search(r'^## ' + re.escape(heading) + r'\n(.*?)(?=^## |\Z)', text, re.M | re.S)
    require(match is not None, 'section:' + heading)
    return match.group(0)

def graph(edges, label):
    visited, active = set(), set()
    def visit(node):
        require(node not in active, label + ':cycle')
        if node in visited: return
        active.add(node)
        for dep in edges[node]:
            require(dep in edges, label + ':dangling')
            visit(dep)
        active.remove(node); visited.add(node)
    for node in edges: visit(node)

def expected_cases():
    table = section(original(NIP3, AUTH_BASE).decode(), 'Acceptance Cases')
    expected = set()
    for line in table.splitlines():
        row = [v.strip() for v in line.split('|')[1:-1]]
        if row and row[0].isdigit():
            case = int(row[0]); proof = row[-1]
            for runtime in ('stub', 'sbcl', 'ci'):
                if re.search(r'\b' + runtime + r'\b', proof, re.I):
                    expected.add((case, runtime, ('mechanism' if runtime == 'ci' else 'policy') if case == 8 else 'live'))
    require({v[0] for v in expected} == set(range(1, 14)), 'external-case-anchor')
    return expected

def check_lists(lists, full=True, baseline_ids=None):
    ids, budgets, cases = [], {}, []
    for phase, listing in lists.items():
        schema(listing, 'feature_list')
        fs = listing['features']; local = [f['id'] for f in fs]
        require(len(set(local)) == len(local), 'duplicate')
        require(listing.get('phase_status') == 'pending', 'activation')
        require(all(f['status'] == 'pending' and f.get('passes', False) is False for f in fs), 'activation')
        edges = {f['id']: f['dependencies'] for f in fs}; graph(edges, 'list')
        require(all(local.index(d) < local.index(f['id']) for f in fs for d in f['dependencies']), 'topological-order')
        total = sum(f['estimated_lines'] for f in fs)
        require(total == listing['original_estimate_lines'], 'budget-sum')
        require(listing.get('ceiling_130pct') == total * 13 // 10 and total <= 8600, 'budget-ceiling')
        for f in fs:
            buckets = f.get('budget_categories', {})
            require({'product', 'tests', 'process'} <= buckets.keys() and all(type(v) is int and v >= 0 for v in buckets.values()) and sum(buckets.values()) == f['estimated_lines'], 'budget-buckets')
            require(bool(f['acceptance_tests']) and all(shlex.split(c) for c in f['acceptance_tests']), 'future-command')
        require(all(set(f['budget_categories']) == {'product', 'tests', 'process'} for f in fs) and listing.get('budget_categories') == {k: sum(f['budget_categories'][k] for f in fs) for k in ('product', 'tests', 'process')}, 'budget-aggregate')
        ids += local; budgets[phase] = {'estimate': total, 'ceiling': listing['ceiling_130pct']}
        cases += listing.get('case_matrix', [])
    require(len(ids) == len(set(ids)), 'global-duplicate')
    require(not set(ids).intersection(baseline_ids or ()) and all(int(v) > 114 for v in ids), 'global-allocation')
    wa = [int(f['id']) for p, l in lists.items() if p in PHASES[:3] for f in l['features']]
    controller = [int(f['id']) for p, l in lists.items() if p in PHASES[3:] for f in l['features']]
    require(not controller or max(wa) < min(controller), 'wa-first')
    require(ids and sorted(map(int, ids)) == list(range(115, max(map(int, ids)) + 1)), 'allocation-gap')
    if full:
        actual = {(int(c['case']), c['runtime'], c['layer']) for c in cases}
        require(actual == expected_cases() and len(actual) == len(cases), 'case-coverage')
        for c in cases:
            require(c['owner'] in ids and c['proof_kind'] == 'future-live', 'case-proof')
            words = shlex.split(c['command'])
            require('--case' in words and words[words.index('--case') + 1] == str(c['case']) and '--runtime' in words and words[words.index('--runtime') + 1] == c['runtime'], 'case-command')
            require(c['command'] in next(f['acceptance_tests'] for l in lists.values() for f in l['features'] if f['id'] == c['owner']), 'case-owner-command')
            if c['case'] == 8:
                require('--layer' in words and words[words.index('--layer') + 1] == c['layer'], 'case8-layer')
    return {'allocation': {p: [f['id'] for f in l['features']] for p, l in lists.items()}, 'budgets': budgets}

def metadata(lists, result, full):
    owners = {f['id']: p for p, l in lists.items() for f in l['features']}
    interface_rows = [i for l in lists.values() for i in l.get('future_interfaces', [])]
    interfaces = {i['path']: i['owner'] for i in interface_rows}
    require(bool(interfaces) and all(i in owners for i in interfaces.values()), 'interface-owner')
    require(all(interfaces[i['path']] == i['owner'] for i in interface_rows), 'interface-owner-conflict')
    phase_edges = {p: [] for p in lists}
    feature_edges = {f['id']: list(f['dependencies']) for l in lists.values() for f in l['features']}
    for p, listing in lists.items():
        for f in listing['features']:
            for command in f['acceptance_tests']:
                words = shlex.split(command)
                while words and '=' in words[0]: words.pop(0)
                runner = words[1] if words[0] in ('python3', 'bash', 'sbcl') else words[0]
                require(runner in interfaces and not any(v in words for v in (';', '&&', '||', '|')) and not any(v in command for v in ('\n', '`', '$(')), 'future-interface')
        for pre in listing.get('cross_phase_prerequisites', []):
            upstream = pre['phase'][:3]
            require(upstream in PHASES and upstream != p and pre['evidence'] and pre['authority'], 'cross-phase-prerequisite')
            if upstream in lists: phase_edges[p].append(upstream)
            elif full: raise ValueError('cross-phase-prerequisite')
            for owner in pre['requires']:
                require(owner.startswith('H-') or owner.isdigit(), 'prerequisite-identifier')
                if owner.isdigit() and (full or owner in owners): require(owners.get(owner) == upstream or int(owner) <= 114, 'prerequisite-owner')
                if owner in owners:
                    for f in listing['features']: feature_edges[f['id']].append(owner)
        require(isinstance(listing.get('shared_file_lanes'), list), 'shared-lanes')
        for lane in listing['shared_file_lanes']:
            require(lane['path'] and set(lane['owners']) == set(lane['order']) and len(set(lane['order'])) == len(lane['order']), 'shared-lane-order')
            require(not full or set(lane['owners']) <= owners.keys(), 'shared-lane-owner')
            for earlier, later in zip(lane['order'], lane['order'][1:]):
                if earlier in owners and later in owners: feature_edges[later].append(earlier)
    graph(phase_edges, 'proposed-phase')
    graph(feature_edges, 'proposed-feature')
    result['cross_phase_graph'] = phase_edges
    result['proposed_feature_graph'] = feature_edges

def projections(lists, result, dag):
    projection = dag['planning_projection']
    phase_ids = [l['phase'] for l in lists.values()]; allocation = {f['id']: l['phase'] for l in lists.values() for f in l['features']}
    require(projection['phases'] == phase_ids and projection['allocation'] == allocation and set(projection['order']) == set(phase_ids) and len(projection['order']) == len(phase_ids), 'planning-projection')
    order = [p[:3] for p in projection['order']]
    require(all(order.index(dep) < order.index(p) for p, deps in result['cross_phase_graph'].items() for dep in deps), 'proposed-order')
    old = json.loads(original('docs/planning/backlog_dag.json'))
    packets = {v['id']: v for v in dag['packets']}
    for prior in old['packets']:
        now = packets[prior['id']]
        excluded = {'actual_assigned'} | ({'status', 'prerequisites', 'planning_delivery'} if prior['id'] in ('PLAN-WA', 'PLAN-016') else set())
        require({k: v for k, v in prior.items() if k not in excluded} == {k: v for k, v in now.items() if k not in excluded}, 'historical-packet')
    for alias in ['NIP3-' + str(n) for n in range(115, 121)] + ['A09', 'A04b', 'A10', 'A11-D', 'A11-CI', 'A14', 'A15', 'A16-WA']:
        assignments = packets[alias].get('actual_assigned', [])
        require(bool(assignments), 'alias-assignment')
        for a in assignments: require(allocation.get(a['feature_id']) == a['phase'] and a['evidence'].startswith('.agent/evidence/' + a['feature_id'] + '/'), 'alias-owner')
    proposed = {v['id']: v['dependency_edges']['depends_on'] + v['dependency_edges']['serialize_after'] for v in dag['packets']}
    supersessions = dag['proposed_supersessions']
    require({s['packet'] for s in supersessions} == {'A09', 'NIP3-115', 'A11-D', 'NIP3-117'} and len(supersessions) == 4, 'supersession-set')
    for s in supersessions:
        packet = packets[s['packet']]
        require(packet['dependency_edges']['serialize_after'] == s['prior_serialize_after'] and s['rationale'], 'supersession-history')
        proposed[s['packet']] = packet['dependency_edges']['depends_on'] + s['proposed_serialize_after']
    graph(proposed, 'proposed-global')
    for path in ('docs/planning/ROADMAP.md', 'docs/planning/HANDOVER.md', 'docs/planning/backlog_reconciliation.md', NIP3, NIP4):
        require(E + 'plan-validation.json' in (ROOT / path).read_text(), 'current-validation-reference')
    rows = re.findall(r'^\|\s*(0(?:16|17|18|19|20))\s*\|\s*([^|]+)\|', (ROOT / 'docs/planning/ROADMAP.md').read_text(), re.M)
    expanded = {p: [str(n) for a, b in re.findall(r'(\d{3})(?:\s*[-–]\s*(\d{3}))?', ids) for n in range(int(a), int(b or a) + 1)] for p, ids in rows}
    require(expanded == result['allocation'], 'roadmap-allocation')

def scope_paths(changed, allowed):
    require(all(any(fnmatch.fnmatchcase(p, pat) for pat in allowed) for p in changed), 'protected-scope')

def current_phase(manifest, old):
    require(manifest['current_phase'] == old['current_phase'] and manifest['phases'][:len(old['phases'])] == old['phases'], 'current-phase')

def preserve_public(path):
    before, after = original(path).decode(), (ROOT / path).read_text()
    if before == after: return
    if path == 'CHANGELOG.md':
        removed = [before.splitlines()[i:j] for tag, i, j, _, _ in difflib.SequenceMatcher(None, before.splitlines(), after.splitlines(), autojunk=False).get_opcodes() if tag in ('delete', 'replace')]
        require(not removed, 'changelog-history'); return
    a, b = before.split('---', 2), after.split('---', 2)
    fa, fb = yaml.safe_load(a[1]), yaml.safe_load(b[1])
    versions = {'ROADMAP.md': '0.61.0', 'HANDOVER.md': '1.0.9', 'backlog_reconciliation.md': '0.1.15', 'NIP-0003-live-runtime-sessions.md': '1.1.2', 'NIP-0004-workflow-assurance.md': '1.1.1'}
    require(fb['version'] == versions[pathlib.Path(path).name], 'public-version')
    require(fb['change_log'][1:] == fa['change_log'] and len(fb['change_log']) == len(fa['change_log']) + 1, 'public-log-history')
    require({k: v for k, v in fa.items() if k not in ('version', 'change_log')} == {k: v for k, v in fb.items() if k not in ('version', 'change_log')}, 'public-frontmatter')
    if path.endswith('ROADMAP.md'):
        a[2] = re.sub(r'^- \*\*Phase015 normative scope is complete\.\*\*.*?(?=^- |\Z)', '', a[2], count=1, flags=re.M | re.S)
        b[2] = re.sub(r'^- \*\*Phase015 normative scope is complete\.\*\*.*?(?=^- |\Z)', '', b[2], count=1, flags=re.M | re.S)
    old_lines, new_lines = a[2].splitlines(), b[2].splitlines()
    deleted = [line for tag, i, j, _, _ in difflib.SequenceMatcher(None, old_lines, new_lines, autojunk=False).get_opcodes() if tag in ('delete', 'replace') for line in old_lines[i:j]]
    require(all(re.fullmatch(r'## (Current Position \([^)]*\)|Current status — [\d-]+|Current planning view — [\d-]+)', line) for line in deleted), 'public-body-history')

def immutable_task_records(task_root):
    mutable = {E + 'check_plans.py', E + 'lifecycle.yaml'}
    entries = [line.split('\t') for line in git('ls-tree', '-r', EXISTING_TASK, '--', E).decode().splitlines()]
    require(bool(entries), 'immutable-task-anchor')
    for info, name in entries:
        if name in mutable: continue
        path = task_root / name
        require(path.exists() or path.is_symlink(), 'immutable-task-missing:' + name)
        require(path.is_file() and not path.is_symlink(), 'immutable-task-type:' + name)
        require(bool(path.stat().st_mode & 0o111) == (info.split()[0] == '100755'), 'immutable-task-mode:' + name)
        require(path.read_bytes() == original(name, EXISTING_TASK), 'immutable-task-bytes:' + name)

def check_scope(task_root=ROOT):
    immutable_task_records(task_root)
    contract = read('.agent/contracts/workflow-016-planning.json')
    require(contract['scope'] == json.loads(original('.agent/contracts/workflow-016-planning.json', APPROVED))['scope'], 'contract-scope-anchor')
    allowed = [v['path'] for kind in ('files_create', 'files_modify') for v in contract['scope'][kind]]
    changed = set(git('diff', '--name-only', BASE, '--').decode().splitlines()) | set(git('ls-files', '--others', '--exclude-standard').decode().splitlines())
    scope_paths(changed, allowed)
    old, now = json.loads(original('.agent/run_state.json')), read('.agent/run_state.json')
    ignored = {'planning_task', 'updated_at', 'last_action', 'history', 'circuit_breaker'}
    require({k: v for k, v in old.items() if k not in ignored} == {k: v for k, v in now.items() if k not in ignored}, 'state-owned-fields')
    require(now['history'][:len(old['history'])] == old['history'], 'history-prefix')
    require(all(now['circuit_breaker'].get(k) == v for k, v in old['circuit_breaker'].items()), 'old-counters')
    require(all(k in old['circuit_breaker'] or (k.startswith('workflow-016-planning-') and v['limit'] == 3 and 0 <= v['attempts'] <= 3) for k, v in now['circuit_breaker'].items()), 'new-counters')
    baseline = {line.split('\t')[1]: line.split()[0] for line in git('ls-tree', '-r', BASE, '--', '.nizam').decode().splitlines()}
    actual = {str(p.relative_to(ROOT)): p for p in (ROOT / '.nizam').rglob('*') if p.is_file() or p.is_symlink()}
    require(set(actual) == set(baseline), 'installed-inventory')
    require(all(p.read_bytes() == original(name) and not p.is_symlink() and bool(p.stat().st_mode & 0o111) == (baseline[name] == '100755') for name, p in actual.items()), 'installed-bytes-mode')
    for path, headings in ((NIP3, ('Acceptance Cases', 'Decision')), (NIP4, ('Acceptance matrix', 'Design choices and selected decisions'))):
        for h in headings: require(section((ROOT / path).read_text(), h) == section(original(path).decode(), h), 'sealed-section:' + h)
    for path, marker in (('docs/planning/HANDOVER.md', '## Historical handover snapshot'), ('docs/planning/backlog_reconciliation.md', '## Prior reconciliation history')):
        require((ROOT / path).read_text().split(marker, 1)[1] == original(path).decode().split(marker, 1)[1], 'historical-suffix')
    for path in ('docs/planning/ROADMAP.md', 'docs/planning/HANDOVER.md', 'docs/planning/backlog_reconciliation.md', NIP3, NIP4, 'CHANGELOG.md'): preserve_public(path)
    return sorted(changed)

def negative():
    lists = {}
    for index, p in enumerate(PHASES):
        fid = str(115 + index)
        lists[p] = {'phase': p, 'spec_version': '0.1.0', 'phase_status': 'pending', 'original_estimate_lines': 100, 'ceiling_130pct': 130, 'budget_categories': {'product': 40, 'tests': 30, 'process': 30}, 'future_interfaces': [{'path': 'tools/future.py', 'owner': '115'}], 'shared_file_lanes': [], 'cross_phase_prerequisites': [], 'features': [{'id': fid, 'name': p, 'description': 'Synthetic bounded control', 'status': 'pending', 'dependencies': [], 'acceptance_tests': ['python3 tools/future.py --positive'], 'estimated_lines': 100, 'budget_categories': {'product': 40, 'tests': 30, 'process': 30}}]}
    lists['020']['case_matrix'] = [{'case': c, 'runtime': r, 'layer': l, 'owner': '119', 'command': f'python3 tools/future.py --case {c} --runtime {r} --layer {l}', 'proof_kind': 'future-live'} for c, r, l in sorted(expected_cases())]
    lists['020']['features'][0]['acceptance_tests'] += [c['command'] for c in lists['020']['case_matrix']]
    metadata(lists, check_lists(lists), True); receipts = []
    def trial(label, change, expected):
        bad = copy.deepcopy(lists); change(bad)
        try: metadata(bad, check_lists(bad), True)
        except (ValueError, jsonschema.ValidationError) as err:
            require(str(err).startswith(expected), 'negative-target:' + label); receipts.append({'control': label, 'rejection': expected, 'restored_valid': True})
        else: raise ValueError('negative-false-pass:' + label)
        metadata(lists, check_lists(lists), True)
    trial('duplicate', lambda m: m['017']['features'].append(copy.deepcopy(m['017']['features'][0])), 'duplicate')
    trial('schema-required-key', lambda m: m['017'].pop('spec_version'), "'spec_version' is a required property")
    trial('dangling', lambda m: m['017']['features'][0].update(dependencies=['999']), 'list:dangling')
    trial('cycle', lambda m: m['017']['features'][0].update(dependencies=['115']), 'list:cycle')
    trial('activation', lambda m: m['017'].update(phase_status='active'), 'activation')
    trial('budget', lambda m: m['017'].update(original_estimate_lines=101), 'budget-sum')
    trial('omitted-case', lambda m: m['020']['case_matrix'].pop(), 'case-coverage')
    trial('stale-fixture-proof', lambda m: m['020']['case_matrix'][0].update(proof_kind='schema-fixture'), 'case-proof')
    trial('omitted-case8-layer', lambda m: next(c for c in m['020']['case_matrix'] if c['case'] == 8).update(layer='live'), 'case-coverage')
    trial('global-duplicate', lambda m: m['018']['features'][0].update(id='115'), 'global-duplicate')
    trial('wrong-case-command', lambda m: m['020']['case_matrix'][0].update(command='python3 tools/future.py --positive'), 'case-command')
    trial('vacuous-echo-command', lambda m: m['017']['features'][0].update(acceptance_tests=['echo PASS']), 'future-interface')
    trial('expanded-crossphase-cycle', lambda m: (m['017']['cross_phase_prerequisites'].append({'phase': '016', 'requires': ['118'], 'evidence': ['.agent/evidence/118/'], 'authority': 'future H-PHASE-016'}), m['016']['cross_phase_prerequisites'].append({'phase': '017', 'requires': ['115'], 'evidence': ['.agent/evidence/115/'], 'authority': 'future H-PHASE-017'})), 'proposed-phase:cycle')
    for label, action, target in [('global-serialization-cycle', lambda: graph({'a': ['b'], 'b': ['a']}, 'global'), 'global:cycle'), ('protected-untracked', lambda: scope_paths(['tools/forbidden.py'], [E + '**']), 'protected-scope'), ('protected-history-mutation', lambda: scope_paths(['.agent/qa/114.json'], [E + '**']), 'protected-scope'), ('current-phase-spoof', lambda: current_phase({'current_phase': '017', 'phases': []}, {'current_phase': '015', 'phases': []}), 'current-phase')]:
        try: action()
        except ValueError as err: require(str(err) == target, 'negative-target'); receipts.append({'control': label, 'rejection': target, 'restored_valid': True})
        else: raise ValueError('negative-false-pass:' + label)
        graph({'a': [], 'b': ['a']}, 'global'); scope_paths([E + 'control.json'], [E + '**']); current_phase({'current_phase': '015', 'phases': []}, {'current_phase': '015', 'phases': []})
    with tempfile.TemporaryDirectory(prefix='nizam-planning-evidence-control-') as temporary:
        scratch = pathlib.Path(temporary)
        for line in git('ls-tree', '-r', EXISTING_TASK, '--', E).decode().splitlines():
            info, name = line.split('\t'); path = scratch / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(original(name, EXISTING_TASK)); path.chmod(0o755 if info.split()[0] == '100755' else 0o644)
        check_scope(scratch)
        for label, name, defect in [('changed-authorization', 'authorization-isolation.json', 'bytes'), ('missing-receipt', 'checker-negative.txt', 'missing'), ('evidence-type', 'environment-observed.txt', 'type'), ('evidence-mode', 'checker-negative.txt', 'mode'), ('unrelated-evidence-mutation', 'plan-interface.json', 'bytes')]:
            path = scratch / (E + name); data = path.read_bytes()
            if defect == 'missing': path.unlink()
            elif defect == 'type': path.unlink(); path.symlink_to(scratch / (E + 'authorization-isolation.json'))
            elif defect == 'mode': path.chmod(0o755)
            else: path.write_bytes(data + b'\nchanged\n')
            try: check_scope(scratch)
            except ValueError as error: require(str(error) == 'immutable-task-' + defect + ':' + E + name, 'negative-target:' + label)
            else: raise ValueError('negative-false-pass:' + label)
            finally:
                if path.is_symlink(): path.unlink()
                path.write_bytes(data); path.chmod(0o644)
            check_scope(scratch); receipts.append({'control': label, 'rejection': 'immutable-task-' + defect, 'restored_valid': True})
        added = E + 'legitimate-new-receipt.txt'; (scratch / added).write_text('new command/exit receipt\n'); scope_paths([added], [E + '**']); check_scope(scratch)
        receipts.append({'control': 'legitimate-new-receipt', 'result': 'accepted', 'restored_valid': True})
    return receipts

def main():
    parser = argparse.ArgumentParser()
    # Options are kept explicit so an unknown switch is a setup error, never a negative receipt.
    for name in ('wa', 'all', 'negative', 'scope'): parser.add_argument('--' + name, action='store_true')
    args = parser.parse_args(); mode = [name for name in ('wa', 'all', 'negative', 'scope') if getattr(args, name)]
    require(len(mode) == 1, 'exactly-one-mode'); mode = mode[0]
    if mode == 'negative': result = {'negative_controls': negative()}
    elif mode == 'scope': result = {'scope_changed': check_scope()}
    else:
        selected = PHASES[:3] if mode == 'wa' else PHASES
        lists = {p: read('.agent/feature_list_' + p + '.json') for p in selected if (ROOT / ('.agent/feature_list_' + p + '.json')).exists()}
        require('017' in lists and (mode == 'wa' or {'016', '020'} <= lists.keys()), 'selected-triples')
        baseline = [f['id'] for path in git('ls-tree', '-r', '--name-only', AUTH_BASE, '--', '.agent').decode().splitlines() if re.fullmatch(r'\.agent/feature_list[^/]*\.json', path) for f in json.loads(original(path, AUTH_BASE))['features']]
        require(max(map(int, baseline)) == 114, 'baseline-max'); result = check_lists(lists, mode == 'all', baseline)
        for p, l in lists.items():
            phase = yaml.safe_load((ROOT / ('docs/planning/phase_' + p + '.yaml')).read_text()); schema(phase, 'phase')
            require(phase['id'] == l['phase'] and phase['status'] == 'pending' and len(phase['steps']) == len(l['features']) and all(s['status'] == 'PENDING' and 'evidence' not in s for s in phase['steps']), 'phase-pending')
            text = (ROOT / ('.agent/product_spec_' + p + '.md')).read_text(); front = yaml.safe_load(text.split('---', 2)[1]); schema(front, 'frontmatter'); require(front['status'] == 'draft', 'spec-draft')
        manifest = read('docs/planning/manifest.json'); schema(manifest, 'manifest')
        old_manifest = json.loads(original('docs/planning/manifest.json'))
        current_phase(manifest, old_manifest)
        require([r['feature_list'] for r in manifest['phases'][len(old_manifest['phases']):]] == ['.agent/feature_list_' + p + '.json' for p in lists] and all(r['status'] == 'pending' for r in manifest['phases'][len(old_manifest['phases']):]), 'manifest-projection')
        require(len({r['id'] for r in manifest['phases']}) == len(manifest['phases']), 'manifest-duplicate')
        dag = read('docs/planning/backlog_dag.json'); graph({v['id']: v['dependency_edges']['depends_on'] + v['dependency_edges']['serialize_after'] for v in dag['packets']}, 'global')
        metadata(lists, result, mode == 'all')
        if mode == 'all': projections(lists, result, dag)
        result['scope_changed'] = check_scope()
        inputs = [q for p in lists for q in ('.agent/feature_list_' + p + '.json', '.agent/product_spec_' + p + '.md', 'docs/planning/phase_' + p + '.yaml')] + ['docs/planning/manifest.json', 'docs/planning/backlog_dag.json', E + 'check_plans.py']
        inputs += ['.nizam/schema/' + n + '.schema.json' for n in ('feature_list', 'phase', 'manifest', 'frontmatter')]
        inputs += ['docs/planning/ROADMAP.md', 'docs/planning/HANDOVER.md', 'docs/planning/backlog_reconciliation.md', NIP3, NIP4, 'CHANGELOG.md']
        result['input_sha256'] = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in inputs}
        result['external_case_anchor'] = {'revision': AUTH_BASE, 'path': NIP3, 'sha256': hashlib.sha256(original(NIP3, AUTH_BASE)).hexdigest()}
    result.update(mode=mode, passed=True, revision=git('rev-parse', 'HEAD').decode().strip())
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    try: main()
    except (ValueError, KeyError, IndexError, OSError, jsonschema.ValidationError) as error:
        print(json.dumps({'passed': False, 'error': str(error)})); raise SystemExit(1)
