"""Fresh Evaluator's isolated guard controls and one cwd-decoy adversarial extra."""
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone

REPO = Path(sys.argv[1]).resolve()
OUT = Path(sys.argv[2]).resolve()
MODE = sys.argv[3]
INTERPRETERS = ['/usr/bin/python3.12', '/home/cnross/.local/share/uv/python/cpython-3.13.13-linux-x86_64-gnu/bin/python3.13', '/home/cnross/.local/share/uv/python/cpython-3.14.3-linux-x86_64-gnu/bin/python3.14']
API = REPO / 'tools/workflow_assurance.py'
RUNNER = REPO / 'tools/test_receipt_candidate_batching.py'
GUARD = b'ASSERTION_FAILURE: product AST outside _receipt_candidate body changed\n'
PASS = 'PASS real-git-count-reduction'


def invoke(name, argv, cwd):
    started = datetime.now(timezone.utc).isoformat()
    begin = time.monotonic()
    child = subprocess.Popen(argv, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
    timed_out = False
    try:
        stdout, stderr = child.communicate(timeout=120)
    except subprocess.TimeoutExpired:
        timed_out = True
        child.kill()
        stdout, stderr = child.communicate()
    for kind, raw in [('stdout', stdout), ('stderr', stderr)]:
        (OUT / (name + '.' + kind + '.txt')).write_bytes(raw)
    receipt = dict(argv=argv, cwd=str(cwd), pid=child.pid, started_at=started, ended_at=datetime.now(timezone.utc).isoformat(), elapsed_seconds=time.monotonic()-begin, actual_exit=child.returncode, timed_out=timed_out, exercised_revision=subprocess.check_output(['git', '-C', str(REPO), 'rev-parse', 'HEAD'], text=True).strip(), source_sha256=hashlib.sha256(API.read_bytes()).hexdigest(), runner_sha256=hashlib.sha256(RUNNER.read_bytes()).hexdigest())
    for kind, raw in [('stdout', stdout), ('stderr', stderr)]:
        receipt[kind] = dict(path=name + '.' + kind + '.txt', sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
    (OUT / (name + '.execution.json')).write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, sort_keys=True), flush=True)
    assert not timed_out, name
    return child.returncode, stdout, stderr


if MODE == 'guards':
    for index, interpreter in enumerate(INTERPRETERS):
        for mutation in ['global', 'helper', 'signature', 'body-only']:
            tree = ast.parse(API.read_bytes())
            target = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_receipt_candidate')
            if mutation == 'global':
                tree.body.append(ast.Assign(targets=[ast.Name(id='QA_OUTSIDE_GUARD', ctx=ast.Store())], value=ast.Constant(value=True)))
            elif mutation == 'helper':
                helper = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name != '_receipt_candidate')
                helper.body.insert(0, ast.Pass())
            elif mutation == 'signature':
                target.args.kwonlyargs.append(ast.arg(arg='qa_guard_probe'))
                target.args.kw_defaults.append(ast.Constant(value=None))
            else:
                target.body.insert(0, ast.Pass())
            ast.fix_missing_locations(tree)
            source = ast.unparse(tree) + '\n'
            compile(source, '<owned-valid-ast-mutation>', 'exec')
            with tempfile.TemporaryDirectory(prefix='nizam133-fresh-guard-') as private:
                cwd = Path(private)
                (cwd / API.name).write_text(source)
                (cwd / RUNNER.name).write_bytes(RUNNER.read_bytes())
                code, stdout, stderr = invoke('guard-' + str(index) + '-' + mutation, [interpreter, str(cwd / RUNNER.name), '--check', 'real-git-count-reduction'], cwd)
                if mutation == 'body-only':
                    assert code == 0 and stderr == b'' and stdout.decode().splitlines().count(PASS) == 1, (mutation, code)
                else:
                    assert code == 1 and stderr == GUARD and b'PASS ' not in stdout, (mutation, code)
    print('PASS independent-full-fingerprint-and-body-mask-controls')
elif MODE == 'extra':
    with tempfile.TemporaryDirectory(prefix='nizam133-fresh-cwd-decoy-') as private:
        cwd = Path(private)
        marker = cwd / 'decoy-executed'
        (cwd / API.name).write_text('from pathlib import Path\nPath(' + repr(str(marker)) + ').write_text("unexpected decoy import")\nraise RuntimeError("cwd decoy was imported")\n')
        code, stdout, stderr = invoke('adversarial-cwd-decoy', [INTERPRETERS[2], str(RUNNER), '--check', 'real-git-count-reduction'], cwd)
        assert code == 0 and stderr == b'' and stdout.decode().splitlines().count(PASS) == 1 and not marker.exists(), code
    print('PASS adversarial-cwd-decoy')
else:
    raise ValueError(MODE)
