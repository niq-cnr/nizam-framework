#!/usr/bin/env python3
"""Author-proposed Git-object regressions; independent evaluator must harden and execute."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('convergent_review', ROOT / 'tools/convergent_review.py')
cr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cr)


class HistoricalSymlinkPacketTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        self.git('init', '-q')
        self.git('config', 'user.name', 'Fixture')
        self.git('config', 'user.email', 'fixture@example.test')

    def git(self, *args, data=None):
        return subprocess.run(['git', '-C', str(self.repo), *args], input=data, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, check=True).stdout.decode().strip()

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

    def deleted_link(self, target):
        oid = self.entry('link', '120000', target)
        base = self.commit('base')
        self.git('update-index', '--force-remove', 'link')
        head = self.commit('delete')
        return base, head, oid

    def test_deleted_escaping_target_is_exact_inert_evidence(self):
        target = b'../../outside'
        base, head, oid = self.deleted_link(target)
        for mode in ('ordinary', 'full_audit'):
            with self.subTest(mode=mode):
                packet = self.packet(base, head, mode=mode)
                item = next(x for x in packet['delta'] if x['path'] == 'link')
                self.assertEqual(item['change_kind'], 'deleted')
                self.assertEqual(item['old_content'].encode(), target)
                self.assertEqual(item['old_mode'], '120000')
                self.assertEqual(item['old_object_id'], oid)
                self.assertEqual(item['old_digest'], hashlib.sha256(target).hexdigest())
                cr.validate_packet(packet)
                for field, value in [('old_object_id', '0' * 40), ('old_digest', '0' * 64), ('old_mode', '100644')]:
                    altered = copy.deepcopy(packet)
                    next(x for x in altered['delta'] if x['path'] == 'link')[field] = value
                    with self.assertRaises(cr.ReviewError, msg=field):
                        cr.validate_packet(altered)

    def test_deleted_safe_link_and_worktree_change(self):
        base, head, oid = self.deleted_link(b'local-target')
        before = self.packet(base, head)
        (self.repo / 'link').symlink_to('../../outside')
        after = self.packet(base, head)
        self.assertEqual(before, after)
        self.assertEqual(before['delta'][0]['old_object_id'], oid)
        cr.validate_packet(after)

    def test_candidate_added_and_modified_unsafe_links_rejected(self):
        self.entry('keep', '100644', b'keep')
        base = self.commit('base')
        self.entry('link', '120000', b'../../outside')
        added = self.commit('unsafe-added')
        with self.assertRaises(cr.ReviewError):
            self.packet(base, added)
        self.entry('link', '120000', b'safe')
        safe = self.commit('safe')
        self.entry('link', '120000', b'../../outside')
        unsafe = self.commit('unsafe-modified')
        with self.assertRaises(cr.ReviewError):
            self.packet(safe, unsafe)

    def test_link_to_file_and_file_to_unsafe_link(self):
        self.entry('link', '120000', b'../../outside')
        base = self.commit('old-link')
        self.entry('link', '100644', b'ordinary file')
        head = self.commit('new-file')
        packet = self.packet(base, head)
        self.assertEqual(packet['delta'][0]['old_mode'], '120000')
        self.assertEqual(packet['delta'][0]['new_mode'], '100644')
        self.entry('link', '120000', b'../../outside')
        unsafe = self.commit('new-unsafe-link')
        with self.assertRaises(cr.ReviewError):
            self.packet(head, unsafe)

    def test_safe_rename_keeps_deletion_and_identity(self):
        oid = self.entry('old-link', '120000', b'local-target')
        base = self.commit('old')
        self.git('update-index', '--force-remove', 'old-link')
        self.entry('new-link', '120000', b'local-target')
        head = self.commit('rename')
        packet = self.packet(base, head)
        deleted = next(x for x in packet['delta'] if x['path'] == 'old-link')
        self.assertEqual(deleted['old_object_id'], oid)
        self.assertEqual(deleted['old_mode'], '120000')
        self.assertEqual(deleted['change_kind'], 'deleted')
        cr.validate_packet(packet)

    def test_binary_historical_link_has_explicit_fail_closed_limit(self):
        base, head, _ = self.deleted_link(b'\xff\xfe')
        with self.assertRaisesRegex(cr.ReviewError, 'symlink|UTF-8|binary'):
            self.packet(base, head)

    def test_retrieval_path_rejects_traversal_and_symlink(self):
        for bad in ('../outside', '/tmp/outside', 'nested/../../outside'):
            with self.subTest(path=bad), self.assertRaises(cr.ReviewError):
                cr.validate_path(bad, 'retrieval')
        outside = self.root / 'outside'
        outside.write_bytes(b'sentinel')
        (self.repo / 'linked').symlink_to(outside)
        with self.assertRaises(cr.ReviewError):
            cr._read_regular_nofollow(self.repo / 'linked', 'retrieval')

    def test_outside_fifo_not_read_by_builder(self):
        os.mkfifo(self.root / 'outside')
        base, head, _ = self.deleted_link(b'../outside')
        output = self.root / 'packet.json'
        cmd = ['python3', '-B', str(ROOT / 'tools/convergent_review.py'), 'build-packet', '--repo', str(self.repo),
               '--repository', 'example/repo', '--review-id', 'outside-fifo', '--mode', 'ordinary',
               '--base', base, '--head', head, '--packet-version', '1.1.0', '--output', str(output)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(output.read_text())['delta'][0]['old_content'], '../outside')


if __name__ == '__main__':
    unittest.main()
