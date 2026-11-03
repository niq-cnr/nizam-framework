#!/usr/bin/env python3
"""Independent acceptance corpus for inert historical Git symlink evidence.

Base mode comes from an external Git tree lookup, not a claimed standalone
packet proof. Trials and replay bind the selected packet's complete bytes.
"""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('convergent_review', ROOT / 'tools/convergent_review.py')
cr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cr)
VERSIONS = ('1.0.0', '1.1.0', 'auto')
MODES = ('ordinary', 'full_audit')
# Fixed acceptance limit from the reviewed domain, independent of implementation.
HISTORICAL_MAX_BYTES = 10_000_000
SCHEMA = json.loads((ROOT / 'schema/review_packet.schema.json').read_text())


class HistoricalSymlinkPacketTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        self.env = {
            'PATH': os.environ.get('PATH', os.defpath), 'HOME': str(self.root),
            'LC_ALL': 'C', 'GIT_CONFIG_NOSYSTEM': '1',
            'GIT_CONFIG_GLOBAL': os.devnull, 'GIT_TERMINAL_PROMPT': '0',
            'PYTHONDONTWRITEBYTECODE': '1',
        }
        self.git('init', '-q', '--template=')
        self.git('config', 'user.name', 'Fixture')
        self.git('config', 'user.email', 'fixture@example.test')
        self.git('config', 'commit.gpgsign', 'false')

    def git_bytes(self, *args, data=None):
        return subprocess.run(['git', '-C', str(self.repo), *args], input=data,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              env=self.env, check=True).stdout

    def git(self, *args, data=None):
        return self.git_bytes(*args, data=data).decode().strip()

    def cli(self, *args, tool=None):
        return subprocess.run([sys.executable, '-B', str(tool or ROOT / 'tools/convergent_review.py'),
                               *map(str, args)], cwd=self.root, env=self.env,
                              capture_output=True, text=True, timeout=15)

    def entry(self, path, mode, data):
        oid = self.git('hash-object', '-w', '--stdin', data=data)
        self.git('update-index', '--add', '--cacheinfo', f'{mode},{oid},{path}')
        return oid

    def commit(self, message):
        self.git('commit', '-qm', message)
        return self.git('rev-parse', 'HEAD')

    def packet(self, base, head, version='1.1.0', mode='ordinary'):
        return cr.build_packet_from_git(self.repo, 'example/repo', 'historical-link', mode, base, head,
                                        packet_version=version)

    def variants(self):
        return ((version, mode) for version in VERSIONS for mode in MODES)

    def assert_old_git_identity(self, packet, base, path='link', origin=None):
        """Expected mode/OID/bytes are obtained outside the packet under test."""
        metadata, _ = self.git_bytes('ls-tree', '-z', base, '--', origin or path).split(b'\t', 1)
        mode, kind, oid = metadata.decode().split()
        self.assertEqual(kind, 'blob')
        raw = self.git_bytes('cat-file', 'blob', oid)
        item = next(x for x in packet['delta'] if x['path'] == path)
        self.assertEqual(item['old_mode'], mode)
        self.assertEqual(item['old_content'].encode('utf-8'), raw)
        self.assertEqual(item['old_digest'], hashlib.sha256(raw).hexdigest())
        if packet['schema_version'] == '1.1.0':
            self.assertEqual(item['old_object_id'], oid)
            self.assertEqual(item['old_byte_length'], len(raw))

    def assert_valid_packet(self, packet, version, base, head):
        self.assertEqual(packet['schema_version'], '1.0.0' if version == 'auto' else version)
        self.assertEqual((packet['base_sha'], packet['head_sha']), (base, head))
        jsonschema.Draft202012Validator(SCHEMA).validate(packet)
        cr.validate_packet(packet)
        raw = cr.canonical_json_bytes(packet)
        self.assertEqual(json.loads(raw), packet)
        self.assertEqual(cr.canonical_json_bytes(json.loads(raw)), raw)

    def trial(self, packet, number=1):
        return {'schema_version': '1.0.0', 'review_id': packet['review_id'],
                'trial_number': number, 'packet_digest': hashlib.sha256(cr.canonical_json_bytes(packet)).hexdigest(),
                'head_sha': packet['head_sha'], 'observations': []}

    def deleted_link(self, target):
        oid = self.entry('link', '120000', target)
        base = self.commit('base')
        self.git('update-index', '--force-remove', 'link')
        head = self.commit('delete')
        return base, head, oid

    def test_deleted_escaping_target_is_exact_inert_evidence(self):
        targets = (b'../../outside', b'/absolute/outside', b'C:\\outside', b'folder\\target',
                   b'./local', b'nested/../target', b'<script>"&</script>',
                   'caf\u00e9/\u2028target'.encode(), 'allowed-\u0085-control'.encode())
        for target in targets:
            base, head, _ = self.deleted_link(target)
            for version, mode in self.variants():
                with self.subTest(target=target, version=version, mode=mode):
                    packet = self.packet(base, head, version, mode)
                    self.assert_valid_packet(packet, version, base, head)
                    self.assert_old_git_identity(packet, base)
                    item = packet['delta'][0]
                    self.assertIsNone(item['new_digest'])
                    self.assertIsNone(item['new_mode'])
                    self.assertEqual(packet['review_files'][0]['content'], None)
                    if packet['schema_version'] == '1.1.0':
                        self.assertEqual(item['change_kind'], 'deleted')
                        self.assertEqual(packet['review_files'][0]['record_kind'], 'absent')

    def test_historical_content_digest_blob_length_and_schema_tampering(self):
        base, head, _ = self.deleted_link(b'local-target')
        for version, mode in self.variants():
            with self.subTest(version=version, mode=mode):
                packet = self.packet(base, head, version, mode)
                mutations = [('old_content', 'other-target'), ('old_digest', '0' * 64),
                             ('old_mode', '040000')]
                if packet['schema_version'] == '1.1.0':
                    mutations.extend([('old_object_id', '0' * 40), ('old_byte_length', 0)])
                for field, value in mutations:
                    with self.subTest(field=field):
                        altered = copy.deepcopy(packet)
                        altered['delta'][0][field] = value
                        with self.assertRaisesRegex(cr.ReviewError, 'old_|old text|expected one of'):
                            cr.validate_packet(altered)
                invalid = copy.deepcopy(packet)
                invalid['delta'][0]['unreviewed_extension'] = True
                with self.assertRaises(jsonschema.ValidationError):
                    jsonschema.Draft202012Validator(SCHEMA).validate(invalid)

    def test_selected_packet_mode_substitution_breaks_trial_digest(self):
        base, head, _ = self.deleted_link(b'local-target')
        for version, mode in self.variants():
            with self.subTest(version=version, mode=mode):
                packet = self.packet(base, head, version, mode)
                self.assert_old_git_identity(packet, base)
                trial = self.trial(packet)
                cr.validate_trial(trial, packet, trial['packet_digest'], 'original trial')
                altered = copy.deepcopy(packet)
                altered['delta'][0]['old_mode'] = '100644'
                altered_digest = hashlib.sha256(cr.canonical_json_bytes(altered)).hexdigest()
                self.assertNotEqual(altered_digest, trial['packet_digest'])
                # Valid enum mode is bound by retained packet bytes, not a base-tree proof.
                with self.assertRaisesRegex(cr.ReviewError, 'packet_digest.*exact packet bytes'):
                    cr.validate_trial(trial, altered, altered_digest, 'substituted trial')

    def test_deleted_safe_link_and_worktree_change(self):
        base, head, _ = self.deleted_link(b'local-target')
        before = {(v, m): self.packet(base, head, v, m) for v, m in self.variants()}
        (self.repo / 'link').symlink_to('../../outside')
        (self.repo / 'untracked').write_bytes(b'not committed')
        for version, mode in self.variants():
            with self.subTest(version=version, mode=mode):
                after = self.packet(base, head, version, mode)
                self.assertEqual(before[(version, mode)], after)
                self.assert_old_git_identity(after, base)
                cr.validate_packet(after)
        self.assertEqual(os.readlink(self.repo / 'link'), '../../outside')

    def assert_candidate_rejected(self, base, head):
        for version, mode in self.variants():
            with self.subTest(version=version, mode=mode):
                with self.assertRaisesRegex(cr.ReviewError, '(new blob|head blob|review_files).*symlink'):
                    self.packet(base, head, version, mode)

    def test_candidate_added_and_modified_unsafe_links_rejected(self):
        self.entry('keep', '100644', b'keep')
        base = self.commit('base')
        self.entry('link', '120000', b'../../outside')
        added = self.commit('unsafe-added')
        self.assert_candidate_rejected(base, added)
        self.entry('link', '120000', b'safe')
        safe = self.commit('safe')
        self.entry('link', '120000', b'../../outside')
        unsafe = self.commit('unsafe-modified')
        self.assert_candidate_rejected(safe, unsafe)

    def test_escaping_old_link_can_be_repaired_to_safe_candidate(self):
        self.entry('link', '120000', b'../../outside')
        base = self.commit('escaping old')
        self.entry('link', '120000', b'local-target')
        head = self.commit('safe candidate')
        for version, mode in self.variants():
            with self.subTest(version=version, mode=mode):
                packet = self.packet(base, head, version, mode)
                self.assert_valid_packet(packet, version, base, head)
                self.assert_old_git_identity(packet, base)
                self.assertEqual(packet['review_files'][0]['content'], 'local-target')

    def test_unchanged_escaping_candidate_requires_full_audit_rejection(self):
        self.entry('link', '120000', b'../../outside')
        self.entry('keep', '100644', b'before')
        base = self.commit('base')
        self.entry('keep', '100644', b'after')
        head = self.commit('head')
        for version in VERSIONS:
            with self.subTest(version=version):
                ordinary = self.packet(base, head, version, 'ordinary')
                self.assertEqual({x['path'] for x in ordinary['delta']}, {'keep'})
                self.assertEqual({x['path'] for x in ordinary['review_files']}, {'keep'})
                with self.assertRaisesRegex(cr.ReviewError, 'head blob link.*symlink'):
                    self.packet(base, head, version, 'full_audit')

    def test_link_to_file_and_file_to_unsafe_link(self):
        self.entry('link', '120000', b'../../outside')
        base = self.commit('old-link')
        self.entry('link', '100644', b'ordinary file')
        head = self.commit('new-file')
        for version, mode in self.variants():
            with self.subTest(version=version, mode=mode):
                packet = self.packet(base, head, version, mode)
                self.assert_old_git_identity(packet, base)
                self.assertEqual(packet['delta'][0]['new_mode'], '100644')
        self.entry('link', '120000', b'../../outside')
        unsafe = self.commit('new-unsafe-link')
        self.assert_candidate_rejected(head, unsafe)

    def test_identical_bytes_mode_transitions_keep_candidate_boundary(self):
        for target in (b'local-target', b'../../outside'):
            self.entry('link', '120000', target)
            base = self.commit('link')
            self.entry('link', '100755', target)
            head = self.commit('same bytes executable')
            for version, mode in self.variants():
                with self.subTest(target=target, version=version, mode=mode):
                    packet = self.packet(base, head, version, mode)
                    self.assert_old_git_identity(packet, base)
                    item = packet['delta'][0]
                    self.assertEqual(item['old_digest'], item['new_digest'])
                    self.assertEqual(item['new_mode'], '100755')
                    if packet['schema_version'] == '1.1.0':
                        self.assertEqual(item['change_kind'], 'mode_changed')
            self.entry('link', '120000', target)
            again = self.commit('same bytes link')
            if target == b'../../outside':
                self.assert_candidate_rejected(head, again)
            else:
                for version, mode in self.variants():
                    packet = self.packet(head, again, version, mode)
                    self.assert_old_git_identity(packet, head)
                    self.assertEqual(packet['delta'][0]['new_mode'], '120000')

    def test_safe_rename_keeps_deletion_and_identity(self):
        oid = self.entry('old-link', '120000', b'local-target')
        base = self.commit('old')
        self.git('update-index', '--force-remove', 'old-link')
        self.entry('new-link', '120000', b'local-target')
        head = self.commit('rename')
        for version, mode in self.variants():
            with self.subTest(version=version, mode=mode):
                packet = self.packet(base, head, version, mode)
                self.assert_valid_packet(packet, version, base, head)
                self.assertEqual({x['path'] for x in packet['delta']}, {'old-link', 'new-link'})
                self.assert_old_git_identity(packet, base, 'old-link')
                items = {x['path']: x for x in packet['delta']}
                self.assertIsNone(items['old-link']['new_digest'])
                self.assertEqual(items['new-link']['new_mode'], '120000')
                if packet['schema_version'] == '1.1.0':
                    self.assert_old_git_identity(packet, base, 'new-link', origin='old-link')
                    self.assertEqual(items['old-link']['change_kind'], 'deleted')
                    self.assertEqual(items['new-link']['change_kind'], 'renamed')
                    self.assertEqual(items['new-link']['renamed_from'], 'old-link')
                    self.assertEqual(items['new-link']['new_object_id'], oid)

    def test_escaping_rename_cannot_hide_unsafe_candidate(self):
        self.entry('old-link', '120000', b'../../outside')
        base = self.commit('old')
        self.git('update-index', '--force-remove', 'old-link')
        self.entry('new-link', '120000', b'../../outside')
        head = self.commit('unsafe renamed destination')
        self.assert_candidate_rejected(base, head)

    def test_all_changed_paths_retained_with_historical_link(self):
        self.entry('link', '120000', b'../../outside')
        self.entry('deleted', '100644', b'delete me')
        self.entry('modified', '100644', b'old')
        self.entry('unchanged', '100644', b'keep')
        base = self.commit('base')
        self.git('update-index', '--force-remove', 'link', 'deleted')
        self.entry('modified', '100644', b'new')
        self.entry('space " & name', '100644', b'new path')
        head = self.commit('multiple changes')
        expected = {'link', 'deleted', 'modified', 'space " & name'}
        for version, mode in self.variants():
            with self.subTest(version=version, mode=mode):
                packet = self.packet(base, head, version, mode)
                self.assertEqual({x['path'] for x in packet['delta']}, expected)
                self.assertEqual({x['path'] for x in packet['review_files']},
                                 expected | ({'unchanged'} if mode == 'full_audit' else set()))
                self.assert_old_git_identity(packet, base)

    def test_binary_historical_link_has_explicit_fail_closed_limit(self):
        targets = (b'', b'\xff\xfe', b'embedded\0nul', b'line\rreturn', b'line\nfeed',
                   b'tab\tvalue', b'control\x01', b'control\x1f', b'delete\x7f')
        for target in targets:
            base, head, _ = self.deleted_link(target)
            for version, mode in self.variants():
                with self.subTest(target=target, version=version, mode=mode):
                    with self.assertRaisesRegex(cr.ReviewError, 'symlink|UTF-8|binary|target'):
                        self.packet(base, head, version, mode)

    def test_self_consistent_malformed_old_link_rejected_by_packet_validator(self):
        base, head, _ = self.deleted_link(b'local-target')
        for version, mode in self.variants():
            packet = self.packet(base, head, version, mode)
            for target in (b'', b'embedded\0nul', b'line\rreturn', b'line\nfeed',
                           b'tab\tvalue', b'control\x01', b'control\x1f', b'delete\x7f'):
                with self.subTest(target=target, version=version, mode=mode):
                    altered = copy.deepcopy(packet)
                    item = altered['delta'][0]
                    item['old_content'] = target.decode()
                    item['old_digest'] = hashlib.sha256(target).hexdigest()
                    if altered['schema_version'] == '1.1.0':
                        item['old_byte_length'] = len(target)
                        item['old_object_id'] = hashlib.sha1(
                            f'blob {len(target)}\0'.encode() + target).hexdigest()
                    with self.assertRaisesRegex(cr.ReviewError, 'symlink|target'):
                        cr.validate_packet(altered)

    def test_historical_target_exact_byte_limit_and_oversize_rejection(self):
        # Multibyte input makes a character-count-only bound observably incorrect.
        for target in (b'a' * HISTORICAL_MAX_BYTES,
                       '\u00e9'.encode() * (HISTORICAL_MAX_BYTES // 2)):
            base, head, _ = self.deleted_link(target)
            for version, mode in self.variants():
                with self.subTest(multibyte=target.startswith(b'\xc3'), version=version, mode=mode):
                    packet = self.packet(base, head, version, mode)
                    self.assert_old_git_identity(packet, base)
            oversized = target + b'a'
            base, head, _ = self.deleted_link(oversized)
            for version, mode in self.variants():
                with self.subTest(oversized=True, version=version, mode=mode):
                    with self.assertRaisesRegex(cr.ReviewError, 'exceeds|max_bytes|bytes'):
                        self.packet(base, head, version, mode)

    def test_retrieval_path_rejects_traversal_and_symlink(self):
        for bad in ('../outside', '/tmp/outside', 'nested/../../outside'):
            with self.subTest(path=bad), self.assertRaises(cr.ReviewError):
                cr.validate_path(bad, 'retrieval')
        outside = self.root / 'outside'
        outside.write_bytes(b'sentinel')
        (self.repo / 'linked').symlink_to(outside)
        with self.assertRaises(cr.ReviewError):
            cr._read_regular_nofollow(self.repo / 'linked', 'retrieval')
        directory = self.root / 'outside-dir'
        directory.mkdir()
        (directory / 'sentinel').write_bytes(b'sentinel')
        (self.repo / 'ancestor').symlink_to(directory, target_is_directory=True)
        with self.assertRaisesRegex(cr.ReviewError, 'without following symlinks'):
            cr._read_regular_nofollow(self.repo / 'ancestor/sentinel', 'retrieval')
        self.assertEqual(outside.read_bytes(), b'sentinel')

    def test_output_symlink_refused_without_touching_sentinel(self):
        base, head, _ = self.deleted_link(b'local-target')
        sentinel = self.root / 'sentinel'
        sentinel.write_bytes(b'outside sentinel')
        output = self.root / 'packet.json'
        output.symlink_to(sentinel)
        result = self.cli('build-packet', '--repo', self.repo, '--repository', 'example/repo',
                          '--review-id', 'output', '--mode', 'ordinary', '--base', base,
                          '--head', head, '--output', output)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn('File exists', result.stderr)
        self.assertTrue(output.is_symlink())
        self.assertEqual(sentinel.read_bytes(), b'outside sentinel')

    def test_outside_fifo_not_read_by_builder(self):
        os.mkfifo(self.root / 'outside')
        base, head, _ = self.deleted_link(b'../outside')
        (self.repo / 'link').symlink_to('../outside')
        for version, mode in self.variants():
            with self.subTest(version=version, mode=mode):
                output = self.root / f'packet-{version}-{mode}.json'
                result = self.cli('build-packet', '--repo', self.repo, '--repository', 'example/repo',
                                  '--review-id', 'outside-fifo', '--mode', mode, '--base', base,
                                  '--head', head, '--packet-version', version, '--output', output)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(output.read_text())['delta'][0]['old_content'], '../outside')
                self.assertEqual(os.readlink(self.repo / 'link'), '../outside')

    def assert_consumer_roundtrip_and_substitution(self, base, head, case_label='', historical_path='link'):
        for version, mode in self.variants():
            with self.subTest(version=version, mode=mode):
                packet = self.packet(base, head, version, mode)
                self.assert_valid_packet(packet, version, base, head)
                self.assert_old_git_identity(packet, base, historical_path)
                if packet['schema_version'] == '1.1.0':
                    historical = next(x for x in packet['delta'] if x['path'] == historical_path)
                    self.assertEqual(historical['old_record_kind'], 'text')
                    self.assertTrue(historical['old_validated_media_type'].startswith('text/'))
                case = self.root / f'consumer-{case_label}{version}-{mode}'
                case.mkdir()
                selected = case / 'packet.json'
                selected.write_bytes(cr.canonical_json_bytes(packet))
                args = ['converge', '--packet', selected, '--output-dir', case / 'result']
                for number in (1, 2, 3):
                    trial_path = case / f'trial-{number}.json'
                    trial_path.write_bytes(cr.canonical_json_bytes(self.trial(packet, number)))
                    args.extend(['--trial', trial_path])
                result = self.cli(*args)
                self.assertEqual(result.returncode, 0, result.stderr)
                replay = case / 'result/replay.json'
                self.assertEqual(self.cli('verify-replay', '--replay', replay).returncode, 0)
                ledger = json.loads((case / 'result/ledger.json').read_bytes())
                self.assertEqual(ledger['packet_digest'], hashlib.sha256(selected.read_bytes()).hexdigest())
                self.assertEqual(ledger['findings'], [])
                retained = case / 'result/inputs/packet.json'
                altered = json.loads(retained.read_bytes())
                altered['delta'][0]['old_mode'] = '100644'
                retained.write_bytes(cr.canonical_json_bytes(altered))
                rejected = self.cli('verify-replay', '--replay', replay)
                self.assertEqual(rejected.returncode, 2, rejected.stderr)
                self.assertRegex(rejected.stderr, 'digest|byte_length')
                selected.write_bytes(cr.canonical_json_bytes(altered))
                args[args.index('--output-dir') + 1] = case / 'substituted-result'
                rejected = self.cli(*args)
                self.assertEqual(rejected.returncode, 2, rejected.stderr)
                self.assertRegex(rejected.stderr, 'packet_digest.*exact packet bytes')

    def test_safe_packet_consumer_replay_and_retained_digest_boundary(self):
        base, head, _ = self.deleted_link(b'local-target')
        self.assert_consumer_roundtrip_and_substitution(base, head)

    def test_historical_packet_consumer_replay_and_retained_digest_boundary(self):
        base, head, _ = self.deleted_link(b'../../outside')
        self.assert_consumer_roundtrip_and_substitution(base, head)

    def test_historical_binary_looking_text_and_binary_extension_paths_are_inert(self):
        # These are valid target text, not files to classify by magic or suffix.
        cases = (('link', b'%PDF-safe'), ('link', b'GIF89a'),
                 ('old-link.pdf', b'local-target'), ('old-link.png', b'local-target'))
        for number, (path, target) in enumerate(cases):
            with self.subTest(path=path, target=target):
                self.entry(path, '120000', target)
                base = self.commit('historical media-looking link')
                self.git('update-index', '--force-remove', path)
                head = self.commit('delete historical media-looking link')
                self.assert_consumer_roundtrip_and_substitution(
                    base, head, case_label=f'media-{number}-', historical_path=path)

    def test_installed_v3_consumer_accepts_only_claimed_v1_0_boundary(self):
        tool = ROOT / '.nizam/tools/convergent_review.py'
        self.assertTrue(tool.is_file(), 'self-governed consumer installation is required')
        installed_spec = importlib.util.spec_from_file_location('historical_installed_consumer', tool)
        installed = importlib.util.module_from_spec(installed_spec)
        installed_spec.loader.exec_module(installed)
        base, head, _ = self.deleted_link(b'../../outside')
        for mode in MODES:
            with self.subTest(mode=mode):
                packet = self.packet(base, head, '1.0.0', mode)
                installed.validate_packet(json.loads(cr.canonical_json_bytes(packet)))


if __name__ == '__main__':
    unittest.main()
