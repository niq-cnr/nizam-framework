#!/usr/bin/env python3
"""Run frozen observer exactly once only after Root explicitly releases diagnosis2."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

root = Path(__file__).resolve().parents[3]
stem = root / '.agent/evidence/122/ci1-diagnosis2'
paths = {suffix: Path(str(stem) + suffix) for suffix in
         ('.stdout.txt', '.stderr.txt', '-trace.txt', '-result.json')}
for path in paths.values():
    if path.exists():
        raise SystemExit('Refuse diagnostic overwrite: ' + str(path))
prefix = '/home/cnross/.tmp/nizam-feature122-ci-git255-build1/install'
argv = [sys.executable, str(stem) + '-observer.py']
env = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1',
       'PATH': prefix + '/bin:' + os.environ['PATH'],
       'GIT_EXEC_PATH': prefix + '/libexec/git-core',
       'GIT_TRACE2_EVENT': str(paths['-trace.txt'])}
revision = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD']).decode().strip()
start = time.time()
with paths['.stdout.txt'].open('wb') as stdout, paths['.stderr.txt'].open('wb') as stderr:
    result = subprocess.run(argv, cwd=root, env=env, stdout=stdout, stderr=stderr)
record = dict(kind='unchanged semantic selector, isolated pinned Git2.55, no induced gc configuration',
              argv=argv, cwd=str(root), revision=revision,
              environment={key: env[key] for key in
                           ('PYTHONDONTWRITEBYTECODE', 'PATH', 'GIT_EXEC_PATH', 'GIT_TRACE2_EVENT')},
              actual_exit=result.returncode, elapsed_seconds=round(time.time()-start, 3),
              helper_sha256=hashlib.sha256(Path(argv[1]).read_bytes()).hexdigest(),
              evidence={suffix: dict(path=str(path.relative_to(root)),
                                    sha256=hashlib.sha256(path.read_bytes()).hexdigest(), bytes=path.stat().st_size)
                        for suffix, path in paths.items() if suffix != '-result.json'})
paths['-result.json'].write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record, indent=2))
raise SystemExit(result.returncode)
