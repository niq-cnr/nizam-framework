"""Independent local observation controls; no verifier or DS qualification."""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
import skill_recommendations as api

with tempfile.TemporaryDirectory(prefix='nf-independent-race-') as temporary:
    root = Path(temporary).resolve()
    package = root / 'selected'
    package.mkdir()
    body = b'# Harmless synthetic entrypoint\n'
    (package / 'SKILL.md').write_bytes(body)
    inventory = [dict(path='SKILL.md', size=len(body), sha256=hashlib.sha256(body).hexdigest())]
    baseline = api.observe(str(root), 'selected', inventory, 'SKILL.md', api.Limits())
    assert baseline == api.host_digest(inventory)
    original = os.scandir
    walks = 0
    def add_untracked(fd):
        global walks
        walks += 1
        if walks == 2:
            (package / '.untracked').write_text('synthetic private note; never diagnostics')
        return original(fd)
    with mock.patch('os.scandir', side_effect=add_untracked):
        try:
            api.observe(str(root), 'selected', inventory, 'SKILL.md', api.Limits())
        except api.ObservationError as error:
            assert str(error) in ('directory-changed', 'inventory-mismatch'), str(error)
            assert 'synthetic private note' not in str(error)
            race = str(error)
        else:
            raise AssertionError('Untracked scope change admitted after first assessed-byte walk')
    assert walks == 2
    # Invalid command-looking path must be rejected before a filesystem root
    # can be opened. It is data, without a verifier or any execution authority.
    malicious = [dict(path='SKILL.md; touch unauthorized-marker', size=0, sha256='0' * 64)]
    with mock.patch.object(api, 'AnchoredTree', side_effect=AssertionError('invalid path touched filesystem')) as anchored:
        try:
            api.observe(str(root), 'selected', malicious, 'SKILL.md', api.Limits())
        except api.ObservationError as error:
            assert str(error) == 'invalid-relative-path'
        else:
            raise AssertionError('Malformed inventory path accepted')
        anchored.assert_not_called()
    assert not (root / 'unauthorized-marker').exists()
    print(json.dumps({'scope':'independent synthetic Nizam observation only',
                      'baseline':'same assessed bytes produce canonical host digest',
                      'concurrent_untracked_input':'rejected: ' + race,
                      'malicious_path':'rejected before root access; no command execution',
                      'qualification_verifier':'none', 'DS_qualification':'not_assessed'}, sort_keys=True))
