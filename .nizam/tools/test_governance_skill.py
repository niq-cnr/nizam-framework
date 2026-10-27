#!/usr/bin/env python3
"""C13 mutations exercise the real check in disposable roots, never the live manifest."""
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class GovernanceSkillTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='nizam-c13-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for name in ('standard', 'methodology', 'templates', 'schema', 'tools', 'ecosystem', 'registry', 'docs'):
            # C13 reads pointers only; copy files without bulky development fixtures.
            shutil.copytree(ROOT / name, self.root / name, ignore=shutil.ignore_patterns('fixtures', '__pycache__'))
        shutil.copy2(ROOT / 'NIZAM.json', self.root / 'NIZAM.json')
        self.skill = json.loads((ROOT / 'tools/skill.json').read_text())

    def check(self, manifest, valid, mode='default'):
        (self.root / 'tools/skill.json').write_text(json.dumps(manifest))
        script = (ROOT / 'tools/validate.sh').read_text()
        # Source the exact production functions, excluding only its entrypoint.
        self.assertTrue(script.rstrip().endswith('main "$@"'))
        script = script[:script.rfind('main "$@"')]
        run = subprocess.run(['bash', '-c', script + '\ncheck_c13_skill_index "$1"', 'c13-test', mode],
                             cwd=self.root, text=True, capture_output=True,
                             env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
        self.assertEqual(run.returncode, 0 if valid else 1, run.stdout + run.stderr)
        self.assertNotIn('Traceback', run.stdout + run.stderr)

    def test_current_manifest_and_subset(self):
        self.check(self.skill, True)
        self.check(self.skill, True, 'payload')
        self.skill['capabilities'] = self.skill['capabilities'][:1]
        self.check(self.skill, True)

    def test_missing_required_fields(self):
        for key in ('name', 'description', 'version', 'entry_point', 'capabilities', 'runtime_requirements', 'state_interface'):
            with self.subTest(key=key):
                changed = copy.deepcopy(self.skill)
                del changed[key]
                self.check(changed, False)

    def test_wrong_required_types_and_shapes(self):
        mutations = [('name', []), ('description', 7), ('version', 'banana'), ('entry_point', True),
                     ('capabilities', {}), ('runtime_requirements', []), ('state_interface', []),
                     ('runtime_requirements', {'x': {'required': 'yes', 'description': 'runtime'}}),
                     ('state_interface', {'root_index': {'path': 5, 'description': 'index'}, 'artifact_families': {}})]
        for key, value in mutations:
            with self.subTest(key=key, value=value):
                changed = copy.deepcopy(self.skill)
                changed[key] = value
                self.check(changed, False)

    def test_malformed_and_duplicate_capabilities(self):
        for value in [[], [None], [{'name': 'x', 'module': 'tools/SKILL.md'}],
                      [self.skill['capabilities'][0]] * 2]:
            with self.subTest(value=value):
                changed = copy.deepcopy(self.skill)
                changed['capabilities'] = value
                self.check(changed, False)

    def test_all_names_obey_version_parity(self):
        for name in ('nizam-governance', 'nizam-skill-index-negative-fixture', 'nizam-skill-index-negative-fixture-extra'):
            with self.subTest(name=name):
                changed = copy.deepcopy(self.skill)
                changed.update(name=name, version='99.0.0')
                self.check(changed, False)

    def test_containment_and_index(self):
        for path in ('../escape.md', '/tmp/escape.md', 'standard/absent.md', 'ecosystem/README.md'):
            with self.subTest(path=path):
                changed = copy.deepcopy(self.skill)
                changed['capabilities'][0]['module'] = path
                self.check(changed, False)
        (self.root / 'tools/escape.md').symlink_to(ROOT / 'tools/SKILL.md')
        changed = copy.deepcopy(self.skill)
        changed['entry_point'] = 'tools/escape.md'
        self.check(changed, False)

    def test_payload_carveout_and_entrypoint(self):
        # Add an indexed non-injected pointer: absence is permitted only for module in payload mode.
        index = json.loads((self.root / 'NIZAM.json').read_text())
        index['capabilities'].append({'id': 'test-envelope', 'summary': 'test', 'authoritative_source': 'docs/absent.md'})
        (self.root / 'NIZAM.json').write_text(json.dumps(index))
        self.skill['capabilities'][0]['module'] = 'docs/absent.md'
        self.check(self.skill, True, 'payload')
        self.check(self.skill, False)
        self.skill['entry_point'] = 'docs/absent.md'
        self.check(self.skill, False, 'payload')

    def test_extension_policy(self):
        # Existing producer-specific fields remain permitted; recognized fields stay typed.
        self.skill['x-consumer-note'] = {'owner': 'test'}
        self.check(self.skill, True)


if __name__ == '__main__':
    unittest.main()
