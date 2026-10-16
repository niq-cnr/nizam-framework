#!/usr/bin/env python3
"""Once-only supplement; never run before Root END. Read-only except --output.
--inventory JSON: endpoint, heads [full SHA], rules [{prefix,owner}], entries
keyed by commit:path or snapshot:path for ambiguous owners/shared allocations
{owner: lines} plus hunk_proof. Generated overrides require generator [rev,path],
sha256, output_sha256, frame [rev,path], reason. Known19ef copies derive b084.
Raw JSON body fields require bodies {pointer: {canonical:[rev,path,pointer|null],
reason}} or {authored:true, previous:[rev,path,pointer|null]|null, owner,reason}.
Canonical Markdown bytes are derived; other body declarations require review.
path_entries supplies shared defaults; allocation_owner attributes a whole event,
split_blocks uses default_owner and rules [{pattern,owner}] with hunk_proof.
Hash-pinned authored {kind,sha256,reason} handles genuine evidence prose/source.
Foreign-only work is attributed separately and remains unmeasured, not free.
body_texts maps body SHA to [rev,path,pointer]; body_readbacks lists reviewed
read-only capture prefixes. Original body events still require authored entries.
Two-parent merges require actual empty remerge-diff proof. Strict JSON hash
indexes use repository-relative paths; other mixed reports retain authored cost.
"""
import argparse
import difflib
import hashlib
import json
import re
from pathlib import Path, PurePosixPath
import runpy
import subprocess
if not __debug__:
    raise RuntimeError('Run without Python optimization; provenance checks are mandatory')
FROZEN = '462f30f21a280f7dec7e7aab1f68979a900dbf78'
COPY = '19efbca54be6b2d58f637b22ee4b4185cf32b342'
ADMISSION = 'b08442c7'
HELPER = '.agent/evidence/133/root-final-scope1.py'
CLASSIFIER = '.agent/evidence/scope-budget-014/measure.py'
PINS = {HELPER: 'a93677bc96c02f48082b1739a19bc715c60e5e0f19de726892dcb10f251e29b8', CLASSIFIER: '3d40a57b5200d7cd00f3fdfbc2cb348b87e9523669d1b9d2682419ca526d9973'}
def sha(raw):
    return hashlib.sha256(raw).hexdigest()
def git(*args):
    return subprocess.check_output(['git', *args])
def blob(rev, path):
    result = subprocess.run(['git', 'show', rev + ':' + path], capture_output=True)
    assert result.returncode in (0, 128), result.stderr
    return result.stdout if result.returncode == 0 else None
def pointer(value, path):
    for part in path.split('/')[1:]:
        key = part.replace('~1', '/').replace('~0', '~')
        value = value[int(key)] if isinstance(value, list) else value[key]
    return value
def textref(ref):
    raw = blob(ref[0], ref[1])
    assert raw is not None, ref
    return pointer(json.loads(raw), ref[2]) if len(ref) > 2 and ref[2] is not None else raw.decode()
def bodies(value, prefix=''):
    if isinstance(value, dict):
        for key, child in value.items():
            p = prefix + '/' + key.replace('~', '~0').replace('/', '~1')
            if key == 'body' and isinstance(child, str) and child:
                yield p, child
            yield from bodies(child, p)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from bodies(child, prefix + '/' + str(index))
def changed(before, after):
    return sum(x[0] in '+-' for x in difflib.ndiff(before.splitlines(), after.splitlines()))
def automatic_merge(commit, parents):
    """Verify this actual merge, rather than assuming every merge is mechanical."""
    assert len(parents) == 2, ('unsupported parent count; review required', commit, parents)
    argv = ['git', '-c', 'color.ui=false', 'show', '--remerge-diff',
            '--format=', '--no-ext-diff', '--no-textconv', commit]
    process = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    proof = dict(commit=commit, parents=parents, argv=argv, child_pid=process.pid,
                 actual_exit=process.returncode, git_version=git('--version').decode().strip(),
                 tree=git('rev-parse', commit + '^{tree}').decode().strip(),
                 parent_trees=[git('rev-parse', p + '^{tree}').decode().strip() for p in parents],
                 stdout=dict(sha256=sha(stdout), bytes=len(stdout)),
                 stderr=dict(sha256=sha(stderr), bytes=len(stderr)))
    assert process.returncode == 0 and stdout == b'' and stderr == b'', ('authored or unsupported remerge; review required', proof)
    proof['disposition'] = 'verified automatic merge; no authored resolution delta'
    return proof


def strict_object(pairs):
    assert len({key for key, _ in pairs}) == len(pairs), 'duplicate JSON keys'
    return dict(pairs)


def json_hash_index(data, revision):
    """Recognize only nonempty, uniform, exact hash maps with file path keys."""
    value = json.loads(data, object_pairs_hook=strict_object)
    if not isinstance(value, dict) or not value:
        return None
    strings = all(isinstance(v, str) and re.fullmatch('[0-9a-f]{64}', v) for v in value.values())
    sized = all(isinstance(v, dict) and set(v) == {'sha256', 'bytes'}
                and isinstance(v['sha256'], str) and re.fullmatch('[0-9a-f]{64}', v['sha256'])
                and type(v['bytes']) is int and v['bytes'] >= 0 for v in value.values())
    if not (strings or sized):
        return None
    # Ordinary hash-valued metadata fields remain maintained reports.
    if not all('/' in key or PurePosixPath(key).suffix for key in value):
        return None
    sources = []
    for path, expected in value.items():
        parsed = PurePosixPath(path)
        assert path and not parsed.is_absolute() and '..' not in parsed.parts and str(parsed) == path, ('index path', path)
        source = blob(revision, path)
        assert source is not None, ('index source absent at same revision', revision, path)
        digest = expected if strings else expected['sha256']
        assert sha(source) == digest, ('index source hash', revision, path)
        assert strings or len(source) == expected['bytes'], ('index source size', revision, path)
        sources.append(dict(path=path, sha256=digest, bytes=len(source)))
    return dict(kind='strict JSON hash index', source_revision=revision,
                schema='filepath->sha256' if strings else 'filepath->{sha256,bytes}', sources=sources)


def allocate_blocks(parent, revision, path, specification):
    """Derive shared-file attribution from reviewed changed-block patterns."""
    patch = git('-c', 'color.ui=false', 'diff', '--no-ext-diff', '--no-textconv',
                '--no-renames', '--unified=0', parent, revision, '--', path).decode()
    blocks, current = [], []
    for line in patch.splitlines():
        if line.startswith(('--- ', '+++ ')):
            continue
        if line[:1] in ('+', '-'):
            current.append(line)
        elif current and not line.startswith('\\ No newline'):
            blocks.append(current)
            current = []
    if current:
        blocks.append(current)
    allocations = {}
    for block in blocks:
        text = '\n'.join(block)
        matched = {rule['owner'] for rule in specification['rules'] if re.search(rule['pattern'], text)}
        assert len(matched) <= 1, ('ambiguous shared block', revision, path)
        owner = next(iter(matched)) if matched else specification['default_owner']
        allocations[owner] = allocations.get(owner, 0) + len(block)
    return allocations


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--endpoint', required=True)
    ap.add_argument('--inventory', required=True, type=Path)
    ap.add_argument('--output', required=True, type=Path)
    args = ap.parse_args()
    cfg = json.loads(args.inventory.read_bytes())
    end = git('rev-parse', args.endpoint).decode().strip()
    assert len(args.endpoint) == 40 and cfg['endpoint'] == end
    assert blob(end, Path(__file__).resolve().relative_to(Path.cwd().resolve()).as_posix()) == Path(__file__).read_bytes(), 'helper must be retained at endpoint'
    heads = [end] + cfg.get('heads', [])
    assert all(len(x) == 40 and git('rev-parse', x).decode().strip() == x for x in heads)
    out = args.output.resolve()
    assert Path.cwd().resolve() not in (out, *out.parents) and not out.exists()
    for path, pin in PINS.items():
        assert sha(Path(path).read_bytes()) == pin, path
    authored = runpy.run_path(HELPER)['authored']
    classify = runpy.run_path(CLASSIFIER)['classify']
    assert all(subprocess.run(['git', 'merge-base', '--is-ancestor', FROZEN, h]).returncode == 0 for h in heads)
    commits = git('rev-list', '--reverse', '--topo-order', *heads, '^' + FROZEN).decode().splitlines()
    events, rows, totals = {}, [], {'snapshot': {}, 'chronological': {}}
    merges = []
    inline_seen = {v: {} for v in totals}
    canonical, markdown = {}, {}
    for commit in commits:
        parents = git('rev-list', '--parents', '-n', '1', commit).decode().split()[1:]
        if len(parents) != 1:
            merges.append(automatic_merge(commit, parents))
            continue
        for item in git('diff', '--numstat', '--no-renames', '-z', parents[0], commit).split(b'\0'):
            if item:
                a, d, path = item.decode().split('\t', 2)
                events[(commit, path)] = (parents[0], a, d)
    for rev, path in [(FROZEN, p) for p in git('ls-tree', '-r', '--name-only', FROZEN).decode().splitlines()] + list(events):
        if Path(path).suffix in {'.py', '.go', '.sh', '.md'}:
            raw = blob(rev, path)
            if raw is not None:
                (markdown if path.endswith('.md') else canonical).setdefault(sha(raw), [rev, path])
    admission = git('rev-parse', ADMISSION).decode().strip()
    def record(view, rev, path, parent, a, d):
        raw, prior = blob(rev, path), blob(parent, path)
        data = raw if raw is not None else prior
        data_revision = rev if raw is not None else parent
        assert data is not None
        key = ('snapshot' if view == 'snapshot' else rev) + ':' + path
        entry = dict(cfg.get('path_entries', {}).get(path, {}), **cfg.get('entries', {}).get(key, {}))
        automatic = 'coordination' if path == '.agent/run_state.json' else ('133' if path.startswith(('.agent/evidence/133/', '.agent/evidence/performance-maintenance/')) or re.fullmatch(r'\.agent/(contracts|qa|validator)/133[^/]*\.json', path) or path == '.agent/evidence/133-qa-adversarial.txt' else ('legacy018' if path.startswith('.agent/evidence/123/') else ('129/phase020' if path.startswith(('.agent/evidence/129/', '.agent/evidence/phase020-preflight/')) else None)))
        if re.fullmatch(r'\.agent/(contracts|qa|validator)/(129|phase020)[^/]*\.json', path):
            automatic = '129/phase020'
        owners = [r['owner'] for r in cfg.get('rules', []) if path.startswith(r['prefix'])] or ([automatic] if automatic else [])
        owner = entry.get('owner', owners[0] if len(owners) == 1 else None)
        assert owner in {'133', 'legacy018', '129/phase020', 'other', 'coordination'} and (len(owners) <= 1 or 'owner' in entry), ('ownership', key)
        category = classify(path)
        assert category != 'unclassified', key
        lines = 0 if a == '-' else int(a) + int(d)
        if 'allocation_owner' in entry:
            entry['allocations'] = {entry['allocation_owner']: lines}
        if 'split_blocks' in entry:
            entry['allocations'] = allocate_blocks(parent, rev, path, entry['split_blocks'])
        if path.startswith(('.agent/feature_list', '.agent/product_spec', 'docs/planning/')):
            assert entry.get('hunk_proof') and 'allocations' in entry, ('shared attribution', key)
        if 'allocations' in entry:
            assert sum(entry['allocations'].values()) == lines, ('shared allocation coverage', key)
        if owner != '133' and not entry.get('allocations', {}).get('133'):
            rows.append(dict(view=view, commit=rev, parent=parent, path=path, owner=owner,
                             before=sha(prior) if prior is not None else None,
                             after=sha(raw) if raw is not None else None,
                             disposition='Separate owner; excluded from133, authored cost unmeasured'))
            return
        kind = authored(path, data) if category == 'evidence' else category
        authored_proof = entry.get('authored')
        if authored_proof is not None:
            assert kind is None and category == 'evidence' and authored_proof['sha256'] == sha(data) and authored_proof['reason']
            assert authored_proof['kind'] in {'source', 'inline-source', 'maintained-prose'}
            kind = authored_proof['kind']
        git_object = entry.get('observed_git_object')
        if git_object is not None:
            assert kind is None and category == 'evidence'
            assert set(git_object) == {'type', 'oid'} and git_object['type'] in {'blob', 'tree', 'commit', 'tag'}
            assert re.fullmatch('[0-9a-f]{40}', git_object['oid']) and git('cat-file', git_object['type'], git_object['oid']) == data, ('Git object observation', key)
        assert kind is not None or git_object is not None or a == '-' or any(t in path for t in ('/raw/', '.stdout.', '.stderr.', '.execution.', '.started.', '.capture-summary.', '.preservation-', 'capture-index', 'outside-sentinel', '.stdin')) or path.endswith('numstat.raw') or (entry.get('observed', {}).get('reason') and entry['observed']['sha256'] == sha(data) and 'actual_exit' in json.loads(blob(*entry['observed']['frame']))), ('unknown observation', key)
        charge = lines if kind and category != 'excluded/run_state' else 0
        provenance = {'before': sha(prior) if prior is not None else None, 'after': sha(raw) if raw is not None else None}
        if authored_proof is not None:
            provenance['authored'] = authored_proof
        if git_object is not None:
            provenance['git_object'] = git_object
        if category == 'evidence' and path.endswith('.json') and kind == 'maintained-mixed-json':
            index = json_hash_index(data, data_revision)
            if index is not None:
                charge = 0
                provenance['hash_index'] = index
        if path.endswith('.sha256') and kind is None:
            for line in data.decode().splitlines():
                digest, target = line.split(maxsplit=1)
                assert re.fullmatch('[0-9a-f]{64}', digest) and sha(blob(data_revision, (Path(path).parent / target.lstrip('*')).resolve().relative_to(Path.cwd().resolve()).as_posix())) == digest, ('index source', key, target)
            provenance['hash_index'] = dict(kind='sha256 text index', source_revision=data_revision, rule='every digest verified against same-revision Git source beside index')
        if path == '.agent/evidence/133/scope-final/scope-report.json':
            frame = json.loads(blob(data_revision, '.agent/evidence/133/scope-final/scope.execution.json'))
            assert sha(data) == '291a25fdf8f8d3601dc1f108c851b47815e0a897a5149b9d4f0647b169770235' and frame['exercised_revision'] == FROZEN and frame['actual_exit'] == 0 and HELPER in frame['argv']
            charge, provenance['generated'] = 0, dict(generator=[FROZEN, HELPER], sha256=PINS[HELPER], frame=frame)
        if 'generated' in entry:
            proof = entry['generated']
            assert proof['reason'] and proof['sha256'] == sha(blob(*proof['generator']))
            assert kind == 'maintained-mixed-json' and category == 'evidence' and proof['output_sha256'] == sha(data) and json.loads(blob(*proof['frame']))['actual_exit'] == 0, key
            provenance['generated'] = proof
            charge = 0
        if rev == COPY and view == 'chronological' and path.startswith('.agent/evidence/133/') and raw is not None and blob(admission, path) == raw:
            release = json.loads(blob(COPY, '.agent/evidence/133/ci-portability1/delivery-release.json'))
            assert git('rev-parse', release['root_admission_revision']).decode().strip() == admission
            source = git('log', '-1', '--format=%H', admission, '--', path).decode().strip()
            assert blob(source, path) == raw and ((source, path) in events or subprocess.run(['git', 'merge-base', '--is-ancestor', source, FROZEN]).returncode == 0)
            provenance['copy'] = [source, path]
            charge = 0
        if kind == 'inline-source':
            digest = sha(data)
            if digest in canonical or digest in inline_seen[view]:
                charge = 0
                provenance['inline_duplicate'] = canonical[digest] if digest in canonical else inline_seen[view][digest]
            inline_seen[view].setdefault(digest, [rev, path])
        body_charges = []
        if category == 'evidence' and kind is None:
            try:
                decoded = json.loads(data)
            except (ValueError, UnicodeError):
                decoded = None
            for p, text in bodies(decoded):
                proof = entry.get('bodies', {}).get(p)
                if not proof and any(path.startswith(prefix) for prefix in cfg.get('body_readbacks', [])):
                    canonical_body = cfg.get('body_texts', {}).get(sha(text.encode()))
                    if canonical_body is not None:
                        assert canonical_body[1:] != [path, p], ('body origin needs authored declaration', key, p)
                        proof = dict(canonical=canonical_body, reason='reviewed readback family and exact canonical body bytes')
                if 'copy' in provenance:
                    proof = dict(canonical=provenance['copy'] + [p], reason='proven mechanical branch copy')
                if not proof and sha(text.encode()) in markdown:
                    proof = dict(canonical=markdown[sha(text.encode())], reason='exact retained Markdown bytes')
                assert proof and proof['reason'], ('unclassified body', key, p)
                if 'canonical' in proof:
                    assert textref(proof['canonical']) == text
                    amount = 0
                else:
                    assert proof.get('authored') is True and proof['owner']
                    before = textref(proof['previous']) if proof['previous'] else ''
                    amount = changed(before, text)
                body_charges.append(dict(pointer=p, sha256=sha(text.encode()), charge=amount, proof=proof))
                target = proof.get('owner', owner)
                totals[view][target] = totals[view].get(target, 0) + amount
        allocations = entry.get('allocations', {owner: charge})
        assert sum(allocations.values()) == charge and all(isinstance(x, int) and x >= 0 for x in allocations.values()), key
        assert set(allocations) <= {'133', 'legacy018', '129/phase020', 'other', 'coordination'} and (len(allocations) <= 1 or entry.get('hunk_proof')), key
        for target, amount in allocations.items():
            totals[view][target] = totals[view].get(target, 0) + amount
        rows.append(dict(view=view, commit=rev, parent=parent, path=path, binary=a == '-', lines=lines, kind=kind, owner=owner, allocations=allocations, provenance=provenance, bodies=body_charges))
    for (commit, path), (parent, a, d) in events.items():
        record('chronological', commit, path, parent, a, d)
    for item in git('diff', '--numstat', '--no-renames', '-z', FROZEN, end).split(b'\0'):
        if item:
            a, d, path = item.decode().split('\t', 2)
            record('snapshot', end, path, FROZEN, a, d)
    supplement = max(totals[v].get('133', 0) for v in totals)
    report = dict(endpoint=end, heads=heads, inventory_sha256=sha(args.inventory.read_bytes()), frozen_endpoint=FROZEN, historical_cost=3024, historical_budget_gate_passed=False, views=totals, supplement=supplement, cumulative_retained_lines=3024 + supplement, rows=rows, merges=merges, foreign_owner_costs='Not measured; foreign-only rows retain ownership and hashes without asserting free work.', limitation='No new budget verdict; later authored administration remains separate and unmeasured; retained-line cost excludes unretained work/time/tokens/billing.')
    out.write_text(json.dumps(report, indent=2) + '\n')
if __name__ == '__main__':
    main()
