"""One static stdlib analysis of the completed, separately released profile."""
import gzip, hashlib, json, os, pstats, stat, subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('/home/cnross/.tmp/nizam-performance-attribution1')
OUT = Path('/home/cnross/.tmp/nizam-performance-attribution1-run')
RELEASE = '5667864732b40d79a0ddf5d98e20175a82d88f5d'
started = datetime.now(timezone.utc).isoformat()
def sha(raw): return hashlib.sha256(raw).hexdigest()
def read(path): return json.loads(path.read_bytes())
def require(condition, message):
    if not condition: raise RuntimeError(message)
def blob(revision, path):
    return subprocess.check_output(['git', '-C', str(ROOT), 'show', revision + ':' + path])
def save(name, value):
    with (OUT / name).open('x') as target: json.dump(value, target, indent=2, sort_keys=True); target.write('\n')
frame = read(OUT / 'candidate-profile1.execution.json')
summary = read(OUT / 'candidate-profile1.capture-summary.json')
release = json.loads(blob(RELEASE, '.agent/evidence/performance-maintenance/root-attribution1-release.json'))
require(frame['argv'] == release['argv'] and frame['exercised_revision'] == RELEASE and frame['actual_exit'] == 0 and not frame['timed_out'], 'execution relation')
require(summary['actual_exit'] == 0 and summary['preservation_equal'] and summary['success'] and summary['capture_driver_sha256'] == release['capture_driver_sha256'], 'capture relation')
for stream in ('stdout', 'stderr'):
    raw = Path(frame[stream]['path']).read_bytes()
    require(sha(raw) == frame[stream]['sha256'] and len(raw) == frame[stream]['bytes'], stream)
inventories = []
for side in ('before', 'after'):
    ref = summary[side]; raw = Path(ref['path']).read_bytes(); decoded = gzip.decompress(raw)
    require(sha(raw) == ref['sha256'] and sha(decoded) == ref['inventory_sha256'], side + ' hashes')
    value = json.loads(decoded)
    require(len(value['rows']) == ref['rows'] == 14288 and sum(r['path'].startswith('.nizam/') for r in value['rows']) == ref['installed'] == 239, side + ' coverage')
    inventories.append(value)
require(inventories[0] == inventories[1] and inventories[0]['head'] == RELEASE and inventories[0]['tree'] == frame['checkout_tree'] and inventories[0]['status'] == '' and inventories[0]['origin'] == 'https://github.com/niq-cnr/nizam-framework.git', 'full preservation')
qa_release = json.loads(blob(RELEASE, '.agent/evidence/123/root-fresh-qa1-release.json'))
ref = qa_release['evidence_ref']; raw = blob(ref['revision'], ref['path'])
require(sha(raw) == ref['sha256'], 'protected map hash')
protected = [row for group in json.loads(raw)['candidate']['assessed_inputs'].values() for row in group]
require(len(protected) == 537, 'protected map coverage')
physical = {r['path']: r for r in inventories[0]['rows']}
for row in protected:
    item = physical[row['path']]
    require(stat.S_ISREG(item['mode']) and item['nlink'] == 1 and item['sha256'] == row['sha256'] and bool(item['mode'] & 0o111) == row['executable'], 'protected input ' + row['path'])
profile = OUT / 'candidate.pstats'; info = profile.lstat()
require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and 0 < info.st_size <= 256 * 1024 * 1024, 'profile guard')
stats = pstats.Stats(str(profile))
def coordinate(key): return dict(filename=key[0], line=key[1], function=key[2])
rows = []
for key, (primitive, total, exclusive, cumulative, callers) in sorted(stats.stats.items()):
    edges = [dict(caller=coordinate(caller), raw_cprofile_tuple=list(values)) for caller, values in sorted(callers.items())]
    rows.append(dict(**coordinate(key), primitive_calls=primitive, total_calls=total, exclusive_seconds=exclusive, cumulative_seconds=cumulative, callers=edges))
save('functions-callers.json', dict(function_tuple_order=['primitive_calls', 'total_calls', 'exclusive_seconds', 'cumulative_seconds', 'callers'], caller_tuple_order=['total_calls', 'primitive_calls', 'exclusive_seconds', 'cumulative_seconds'], functions=rows))
for field, name in [('exclusive_seconds', 'exclusive'), ('cumulative_seconds', 'cumulative'), ('total_calls', 'calls')]:
    top = sorted(rows, key=lambda row: (-row[field], row['filename'], row['line'], row['function']))[:100]
    save('top-' + name + '.json', [dict((k, v) for k, v in row.items() if k != 'callers') for row in top])
result = dict(kind='candidate-only static attribution; not QA/CI/runtime acceptance', exercised_revision=RELEASE, candidate_revision=release['candidate_revision'], protected_source_revision=release['protected_source_revision'], actual_exit=frame['actual_exit'], elapsed_seconds=frame['elapsed_seconds'], physical_rows=14288, installed_rows=239, protected_rows_verified=len(protected), preservation_equal=True, profile=dict(bytes=info.st_size, sha256=sha(profile.read_bytes())), function_entries=len(rows), total_calls=stats.total_calls, primitive_calls=stats.prim_calls, summed_exclusive_seconds=stats.total_tt, analysis=dict(pid=os.getpid(), started_at=started, ended_at=datetime.now(timezone.utc).isoformat()), limitations=['Parent-observed time includes child-process waits; child CPU and Git argv are not identified by this profile.', 'Inclusive chains overlap and must not be summed.', 'Profiling overhead and speedup are unmeasured; prior concurrent QA workloads and ambient trees are not comparable controls.'])
save('analysis-result.json', result)
print(json.dumps(result, sort_keys=True))
