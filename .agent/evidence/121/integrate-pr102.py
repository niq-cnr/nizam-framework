"""Authorized Root integration; exact-head checks and threads precede ordinary merge."""
import hashlib
import json
import pathlib
import subprocess

E = pathlib.Path('.agent/evidence/121'); REPO = 'niq-cnr/nizam-framework'
HEAD = '342bee61488284ec4cf65042ac3872ea4daeaf0f'
revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(); records = []
def capture(label, argv):
    r = subprocess.run(argv, capture_output=True)
    row = {'argv': argv, 'cwd': str(pathlib.Path.cwd()), 'exercised_revision': revision, 'actual_exit': r.returncode, 'environment': {'PYTHONDONTWRITEBYTECODE': '1', 'other': 'inherited gh authentication; no secret capture'}}
    for stream in ('stdout', 'stderr'):
        data = getattr(r, stream); path = E / ('pr102-' + label + '.' + stream + '.txt'); path.write_bytes(data)
        row[stream] = {'path': str(path), 'sha256': hashlib.sha256(data).hexdigest()}
    records.append(row); (E / 'pr102-integration-commands.json').write_text(json.dumps(records, indent=2) + '\n')
    assert r.returncode == 0, label
    return r.stdout
fields = 'number,state,isDraft,headRefOid,mergeable,mergeStateStatus,reviewDecision,reviews,statusCheckRollup'
def inspect(label, draft):
    p = json.loads(capture(label, ['gh', 'pr', 'view', '102', '--repo', REPO, '--json', fields]))
    assert p['headRefOid'] == HEAD and p['state'] == 'OPEN' and p['isDraft'] is draft
    assert p['mergeable'] == 'MERGEABLE' and p['mergeStateStatus'] == 'CLEAN'
    assert p['reviewDecision'] != 'CHANGES_REQUESTED'
    latest = {r['author']['login']: r['state'] for r in p['reviews']}
    assert not any(s == 'CHANGES_REQUESTED' for s in latest.values())
    checks = p['statusCheckRollup']
    assert len(checks) == 6 and all(c['status'] == 'COMPLETED' and c['conclusion'] == 'SUCCESS' for c in checks)
    assert {c['name'] for c in checks} == {'validate', 'closeout', 'e2e_bootstrap', 'fixtures_self_test', 'convergent_review', 'self_governance'}
    return p
ci = json.loads((E / 'ci3-receipt.json').read_text())
assert ci['passed'] is True and ci['default42_passed'] is True and ci['head'] == HEAD
inspect('before-ready', True)
query = 'query { repository(owner:"niq-cnr", name:"nizam-framework") { pullRequest(number:102) { reviewThreads(first:100) { nodes { isResolved isOutdated } pageInfo { hasNextPage } } } } }'
threads = json.loads(capture('threads', ['gh', 'api', 'graphql', '-f', 'query=' + query]))['data']['repository']['pullRequest']['reviewThreads']
assert threads['pageInfo']['hasNextPage'] is False and all(t['isResolved'] is True for t in threads['nodes'])
body_path = pathlib.Path('/tmp/nizam-pr102-body.md'); body = body_path.read_text()
body = body.replace('- [ ] Successful checks on the exact final PR head.', '- [x] Six successful checks on exact final head `' + HEAD + '` (compliance38662279804 and closeout38662279792).')
body_path.write_text(body); (E / 'pr102-final-body.md').write_text(body)
capture('edit', ['gh', 'pr', 'edit', '102', '--repo', REPO, '--title', 'feat: add conflict lanes and owned attempt rollback', '--body-file', str(body_path)])
capture('ready', ['gh', 'pr', 'ready', '102', '--repo', REPO])
inspect('ready-state', False)
capture('merge', ['gh', 'pr', 'merge', '102', '--repo', REPO, '--merge', '--match-head-commit', HEAD])
p = json.loads(capture('merged-state', ['gh', 'pr', 'view', '102', '--repo', REPO, '--json', 'number,state,isDraft,headRefOid,mergeCommit,mergedAt,url']))
assert p['state'] == 'MERGED' and p['headRefOid'] == HEAD and len(p['mergeCommit']['oid']) == 40
(E / 'pr102-merge-receipt.json').write_text(json.dumps({'role': 'Root', 'passed': True, 'pr': 102, 'head': HEAD, 'merge': p['mergeCommit']['oid'], 'merged_at': p['mergedAt'], 'six_exact_head_checks': True, 'unresolved_threads': 0, 'normal_merge': True, 'postmerge_main_CI': 'pending; not yet asserted'}, indent=2) + '\n')
print('MERGED PR102 at ' + p['mergeCommit']['oid'] + '; main CI remains pending')
