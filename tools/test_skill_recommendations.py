#!/usr/bin/env python3
"""Offline controls for Nizam-owned recommendation metadata, without skill bodies."""

import copy
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]


class CatalogueSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads((ROOT / 'schema/recommended_skills.schema.json').read_text())
        Draft202012Validator.check_schema(cls.schema)
        cls.validator = Draft202012Validator(cls.schema)

    def catalogue(self, entry=None):
        return {'catalogue_version': '1.0.0', 'mapping_version': '1.0.0',
                'entries': [] if entry is None else [entry]}

    def candidate(self):
        return {'skill': 'readme-docs', 'task_applicability': ['readme'],
                'status': 'candidate', 'distribution': 'approved-public-metadata'}

    def qualified_shape(self):
        # Fictional metadata tests shape only. It is never a qualified recommendation.
        result = self.candidate()
        result.update({
            'status': 'recommended', 'package_version': '1.0.0',
            'origin': 'synthetic-package-owner',
            'identity': {'source_commit': 'a' * 40, 'inventory_sha256': 'b' * 64},
            'supported_contracts': {'synthetic-report': '1.0.0'},
            'tested_framework': {'source_commit': 'c' * 40,
                                 'compatibility_surface_sha256': 'd' * 64,
                                 'payload_sha256': 'e' * 64},
            'qualification': {'reference': 'approved-evidence-record', 'sha256': 'f' * 64,
                              'producer': 'synthetic-producer',
                              'signature_reference': 'synthetic-signature'},
        })
        return result

    def assertInvalid(self, value):
        self.assertTrue(list(self.validator.iter_errors(value)), value)

    def test_shipped_catalogue_empty_and_valid(self):
        data = json.loads((ROOT / 'tools/recommended_skills.json').read_text())
        self.validator.validate(data)
        self.assertEqual(data['entries'], [])

    def test_empty_and_candidate_do_not_need_external_artifacts(self):
        self.validator.validate(self.catalogue())
        self.validator.validate(self.catalogue(self.candidate()))

    def test_recommended_shape_and_required_identity(self):
        entry = self.qualified_shape()
        self.validator.validate(self.catalogue(entry))
        for key in ['package_version', 'origin', 'identity', 'supported_contracts',
                    'tested_framework', 'qualification']:
            with self.subTest(key=key):
                mutated = copy.deepcopy(entry)
                del mutated[key]
                self.assertInvalid(self.catalogue(mutated))
        for parent, keys in [('identity', ['source_commit', 'inventory_sha256']),
                             ('tested_framework', ['source_commit',
                                                   'compatibility_surface_sha256',
                                                   'payload_sha256']),
                             ('qualification', ['reference', 'sha256', 'producer',
                                                'signature_reference'])]:
            for key in keys:
                with self.subTest(parent=parent, key=key):
                    mutated = copy.deepcopy(entry)
                    del mutated[parent][key]
                    self.assertInvalid(self.catalogue(mutated))

    def test_unverified_cannot_be_promoted_by_status_only(self):
        for state in ['verified', 'recommended']:
            entry = self.candidate()
            entry['status'] = state
            self.assertInvalid(self.catalogue(entry))

    def test_mutable_or_malformed_identity_fails(self):
        entry = self.qualified_shape()
        for key, value in [('source_commit', 'main'), ('source_commit', 'v1.0.0'),
                           ('inventory_sha256', 'latest'), ('inventory_sha256', '')]:
            with self.subTest(key=key, value=value):
                mutated = copy.deepcopy(entry)
                mutated['identity'][key] = value
                self.assertInvalid(self.catalogue(mutated))
        entry['supported_contracts'] = {}
        self.assertInvalid(self.catalogue(entry))

    def test_availability_and_authority_not_catalogue_states(self):
        for state in ['missing', 'modified', 'inaccessible', 'compatible', 'approved']:
            entry = self.candidate()
            entry['status'] = state
            self.assertInvalid(self.catalogue(entry))
        for key in ['install', 'execute', 'host_acceptance', 'local_availability']:
            entry = self.candidate()
            entry[key] = True
            self.assertInvalid(self.catalogue(entry))

    def test_withdrawal_keeps_history_and_requires_reason(self):
        entry = self.qualified_shape()
        entry['status'] = 'withdrawn'
        self.assertInvalid(self.catalogue(entry))
        entry['withdrawal_reason'] = 'Synthetic qualification revoked.'
        self.validator.validate(self.catalogue(entry))
        self.assertIn('qualification', entry)
        self.assertIn('identity', entry)

    def test_withdrawal_cannot_erase_exact_history(self):
        entry = self.qualified_shape()
        entry.update(status='withdrawn', withdrawal_reason='Synthetic qualification revoked.')
        self.validator.validate(self.catalogue(entry))
        required_history = ['package_version', 'origin', 'identity', 'supported_contracts',
                            'tested_framework', 'qualification']
        for key in required_history:
            with self.subTest(missing=key):
                erased = copy.deepcopy(entry)
                del erased[key]
                self.assertInvalid(self.catalogue(erased))
        skeleton = self.candidate()
        skeleton.update(status='withdrawn', withdrawal_reason='Synthetic qualification revoked.')
        self.assertInvalid(self.catalogue(skeleton))

    def test_closed_format_and_local_schema_refs(self):
        self.assertInvalid({'catalogue_version': '2.0.0', 'mapping_version': '1.0.0',
                            'entries': []})
        self.assertInvalid(self.catalogue() | {'install_by_default': True})
        self.assertInvalid([])
        self.assertInvalid(self.catalogue(self.candidate() | {'task_applicability': []}))
        self.assertInvalid(self.catalogue(self.candidate() | {'distribution': 'private-source'}))
        # $schema declares the dialect; every validation ref is local if one exists.
        def refs(value):
            if isinstance(value, dict):
                for key, child in value.items():
                    if key == '$ref':
                        yield child
                    yield from refs(child)
            elif isinstance(value, list):
                for child in value:
                    yield from refs(child)
        self.assertTrue(all(ref.startswith('#') for ref in refs(self.schema)))


if __name__ == '__main__':
    unittest.main()
