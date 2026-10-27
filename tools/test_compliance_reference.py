#!/usr/bin/env python3
"""Exercise inventory parity and negative controls in isolated source copies."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
FILES = ('tools/compliance_checks.json', 'tools/generate_compliance_reference.py',
         'tools/validate.sh', 'tools/README.md', 'README.md',
         'docs/nips/NIP-0003-live-runtime-sessions.md')


class ComplianceReferenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='nizam-compliance-ref-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for name in FILES:
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, target)
        self.registry = self.root / 'tools/compliance_checks.json'
        self.data = json.loads(self.registry.read_text())

    def run_generator(self, expected=0, *args):
        command = [sys.executable, str(self.root / 'tools/generate_compliance_reference.py'), *args]
        result = subprocess.run(command, cwd=self.root, text=True, capture_output=True)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result

    def put(self):
        self.registry.write_text(json.dumps(self.data, indent=2) + '\n')

    def test_valid_and_deterministic(self):
        self.run_generator(0, '--check')
        before = {name: (self.root / name).read_bytes() for name in FILES}
        self.run_generator(0)
        after = {name: (self.root / name).read_bytes() for name in FILES}
        self.assertEqual(before, after)

    def test_missing_duplicate_retired_and_mislabelled(self):
        mutations = [lambda d: d['controls'].pop(),
                     lambda d: d['controls'].append(d['controls'][0].copy()),
                     lambda d: d['controls'][0].update(status='retired'),
                     lambda d: d['controls'][0].update(source_check='check_c2_format'),
                     lambda d: d['controls'][0].update(source_check='check_c1_fictional')]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self.data = json.loads((ROOT / 'tools/compliance_checks.json').read_text())
                mutation(self.data)
                self.put()
                self.run_generator(1, '--check')

    def test_unregistered_and_reserved_control_cannot_pass(self):
        validator = self.root / 'tools/validate.sh'
        original = validator.read_text()
        for addition in ('\necho "[C99] PASS new-control"\n', '\necho "[C17] PASS reserved-control"\n'):
            with self.subTest(addition=addition):
                validator.write_text(original + addition)
                self.run_generator(1, '--check')

    def test_source_reservation_cannot_disappear_from_registry(self):
        self.assertIn('C17', [r['id'] for r in self.data['reserved']])
        self.data['reserved'] = [r for r in self.data['reserved'] if r['id'] != 'C17']
        self.put()
        self.run_generator(1, '--check')

    def test_changed_source_reservation_is_derived(self):
        nip = self.root / 'docs/nips/NIP-0003-live-runtime-sessions.md'
        text = nip.read_text()
        self.assertIn('C17 stays free', text)
        nip.write_text(text.replace('C17 stays free', 'C18 stays free'))
        self.run_generator(1, '--check')

    def test_consumer_payload_does_not_require_nip(self):
        nip = self.root / 'docs/nips/NIP-0003-live-runtime-sessions.md'
        nip.unlink()
        nip.parent.rmdir()
        self.run_generator(0, '--check')

    def test_authoring_checkout_cannot_omit_nip(self):
        nip = self.root / 'docs/nips/NIP-0003-live-runtime-sessions.md'
        nip.unlink()
        nip.parent.rmdir()
        (self.root / '.git').write_text('gitdir: fixture')
        self.run_generator(1, '--check')

    def test_removing_default_dispatch_is_detected(self):
        p = self.root / 'tools/validate.sh'
        original = p.read_text()
        # Remove the call, not the definition or its emitted ID.
        call = '    check_c14_workflow_pins && passed=$((passed + 1)) || failed=$((failed + 1))'
        self.assertEqual(original.count(call), 1)
        p.write_text(original.replace(call, '', 1))
        self.run_generator(1, '--check')

    def test_removing_target_dispatch_is_detected(self):
        p = self.root / 'tools/validate.sh'
        original = p.read_text()
        call = '        check_c9_path_resolution "${target}" && passed=$((passed + 1)) || failed=$((failed + 1))'
        self.assertEqual(original.count(call), 1)
        p.write_text(original.replace(call, '', 1))
        self.run_generator(1, '--check')

    def test_mislabelled_payload_mode_is_rejected(self):
        self.data['controls'][10]['modes']['payload'] = 'exercised'
        self.put()
        self.run_generator(1, '--check')

    def test_regeneration_and_individual_document_drift(self):
        for name in ('README.md', 'tools/README.md', 'tools/validate.sh'):
            with self.subTest(name=name):
                p = self.root / name
                original = p.read_text()
                target = '| C1 |' if name != 'tools/validate.sh' else '  C1: Frontmatter schema'
                self.assertIn(target, original)
                p.write_text(original.replace(target, target + ' DRIFT', 1))
                self.run_generator(1, '--check')
                self.run_generator(0)
                self.assertEqual(p.read_text(), original)
                self.run_generator(0, '--check')

    def test_inventory_value_cannot_silently_change_generated_output(self):
        self.data['controls'][0]['purpose'] = 'A modified description.'
        self.put()
        self.run_generator(1, '--check')
        self.run_generator(0)
        self.run_generator(0, '--check')

    def test_missing_generated_boundary_fails(self):
        p = self.root / 'README.md'
        p.write_text(p.read_text().replace('<!-- END GENERATED COMPLIANCE CONTROLS -->', '', 1))
        self.run_generator(1)


if __name__ == '__main__':
    unittest.main()
