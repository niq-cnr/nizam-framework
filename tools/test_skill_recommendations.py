#!/usr/bin/env python3
"""Offline controls for Nizam-owned recommendation metadata, without skill bodies."""

import copy
import json
from pathlib import Path
import unittest
import hashlib
import hmac
import importlib
import tempfile
from unittest import mock

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


class SyntheticFixture:
    """Independent fictional host data only; never a DS contract or qualification."""
    def __init__(self, root, skill='readme-docs'):
        self.api = importlib.import_module('skill_recommendations')
        self.root = Path(root).resolve()
        self.package = self.root / skill
        self.package.mkdir()
        (self.package / 'SKILL.md').write_bytes(b'# Synthetic selected body\n')
        (self.package / '.hidden').write_bytes(b'included')
        self.framework = self.api.FrameworkIdentity('c' * 40, 'e' * 64, 'd' * 64)
        entry = CatalogueSchemaTests().qualified_shape()
        entry['skill'] = skill
        self.catalogue = CatalogueSchemaTests().catalogue(entry)
        self.config = dict(enabled=True, task_kind='readme', selected_skill=skill,
                           root=str(self.root), package=skill, entrypoint='SKILL.md',
                           format_version='nizam-local-observation/1', inventory=self.inventory())

    def inventory(self):
        return [dict(path=p.relative_to(self.package).as_posix(), size=p.stat().st_size,
                     sha256=hashlib.sha256(p.read_bytes()).hexdigest())
                for p in sorted(self.package.rglob('*')) if p.is_file()]

    def verifier(self, *, fault=None):
        # Fixture trust is installed in application code, never selected by JSON.
        api = self.api
        expected = api.qualification_binding(self.catalogue, self.catalogue['entries'][0],
                    self.framework, api.host_digest(self.config['inventory']), 'SKILL.md')
        key = b'synthetic-fixture-only-key'
        signed = api.canonical(expected)
        signature = hmac.digest(key, signed, 'sha256')
        if fault == 'signature': signature = b'x' * 32
        class FixedSyntheticVerifier(api.HostVerifier):
            def verify(self, binding):
                if fault in ('producer', 'store', 'mapping'): return None
                if binding != expected: return None
                if not hmac.compare_digest(signature, hmac.digest(key, api.canonical(binding), 'sha256')): return None
                return api.VerifiedQualification(api.digest(binding), 'f' * 64, 'synthetic-producer',
                         released=fault != 'release', supported_mapping=True,
                         limitations=('synthetic Nizam interface test only',))
        return FixedSyntheticVerifier()

    def run(self, **kwargs):
        verifier=kwargs.pop('verifier') if 'verifier' in kwargs else self.verifier()
        return self.api.resolve(self.config, self.catalogue, framework=self.framework,
                                verifier=verifier, **kwargs)


class ResolverTests(unittest.TestCase):
    def test_available_entrypoint(self):
        self.assertTrue((ROOT / 'tools/skill_recommendations.py').is_file(),
                        'missing optional resolver capability before NF10 implementation')

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='nf-host-synthetic-')
        self.addCleanup(self.tmp.cleanup)
        if not (ROOT / 'tools/skill_recommendations.py').is_file(): return
        self.f = SyntheticFixture(self.tmp.name)

    def test_known_answer_digest_and_synthetic_trust(self):
        result = self.f.run()
        self.assertEqual(result['local_state'], 'compatible')
        self.assertEqual(result['offer']['skill'], 'readme-docs')
        self.assertFalse(result['execution_authorized'])
        expected = {'version': 'nizam-local-observation/1', 'files': sorted(self.f.config['inventory'], key=lambda r:r['path'])}
        raw = json.dumps(expected, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode('ascii')
        self.assertEqual(self.f.api.host_digest(self.f.config['inventory']), hashlib.sha256(raw).hexdigest())
        self.assertNotEqual(self.f.api.host_digest(self.f.config['inventory']), 'b' * 64)

    def test_no_verifier_and_forged_data_never_qualify(self):
        self.f.config.update(accepted=True, verifier='os.system', trust_store='attacker', command='touch marker')
        self.assertEqual(self.f.run(verifier=None)['local_state'], 'unverified')
        for fault in ('signature', 'producer', 'store', 'mapping', 'release'):
            with self.subTest(fault=fault):
                self.assertIsNone(self.f.run(verifier=self.f.verifier(fault=fault))['offer'])
        self.assertIsNone(self.f.run(verifier={'accepted': True})['offer'])

    def test_exact_pair_and_released_catalogue_binding(self):
        verifier = self.f.verifier()
        entry = self.f.catalogue['entries'][0]
        for parent,key,value in [('identity','source_commit','0'*40),('identity','inventory_sha256','0'*64),
              ('tested_framework','source_commit','0'*40),('tested_framework','payload_sha256','0'*64),
              ('tested_framework','compatibility_surface_sha256','0'*64),('supported_contracts','synthetic-report','2.0.0'),
              ('qualification','sha256','0'*64),('qualification','producer','other')]:
            with self.subTest(parent=parent,key=key):
                old=entry[parent][key]; entry[parent][key]=value
                self.assertIsNone(self.f.run(verifier=verifier)['offer']);entry[parent][key]=old
        self.f.catalogue['entries'][0]['acquisition_reference']='changed released metadata'
        self.assertIsNone(self.f.run(verifier=verifier)['offer'])

    def test_lifecycle_and_required_assurance(self):
        for state in ('candidate','verified','withdrawn'):
            self.f.catalogue['entries'][0]['status']=state
            if state=='withdrawn':self.f.catalogue['entries'][0]['withdrawal_reason']='synthetic withdrawal'
            result=self.f.run(required_checks=('runtime-required',))
            self.assertIsNone(result['offer']);self.assertEqual(result['required_checks'], ['runtime-required'])
            self.assertEqual(result['assurance'], 'unassessed')
        self.f.catalogue['entries'][0]['status']='recommended'
        for key in ('enabled','declined'):
            old=self.f.config.get(key);self.f.config[key]=key=='declined'
            result=self.f.run(required_checks=('runtime-required',))
            self.assertIsNone(result['offer']);self.assertEqual(result['required_checks'], ['runtime-required'])
            if old is None:self.f.config.pop(key)
            else:self.f.config[key]=old

    def test_missing_modified_scope_and_unsupported(self):
        (self.f.package/'SKILL.md').write_bytes(b'changed')
        self.assertEqual(self.f.run()['local_state'],'incompatible')
        self.f.config['inventory']=self.f.inventory();(self.f.package/'untracked').write_bytes(b'added')
        self.assertEqual(self.f.run()['local_state'],'incompatible')
        self.f.config['format_version']='nizam-local-observation/2'
        self.assertEqual(self.f.run()['local_state'],'unverified')
        self.f.config['format_version']='nizam-local-observation/1';self.f.config['package']='missing'
        self.assertEqual(self.f.run()['local_state'],'missing')

    def test_actual_observation_change_cannot_reuse_qualification(self):
        verifier=self.f.verifier()
        (self.f.package/'SKILL.md').write_bytes(b'different actual bytes')
        self.f.config['inventory']=self.f.inventory()
        self.assertIsNone(self.f.run(verifier=verifier)['offer'])
        self.f.config['required_checks']=[]
        self.assertEqual(self.f.run(verifier=None,required_checks=('host-required',))['required_checks'],['host-required'])

    def test_duplicate_inventory_and_bounded_sizes(self):
        original=copy.deepcopy(self.f.config['inventory'])
        self.f.config['inventory']=original+[copy.deepcopy(original[0])]
        self.assertIsNone(self.f.run()['offer'])
        self.f.config['inventory']=original
        for limits in [self.f.api.Limits(individual_file_bytes=1),self.f.api.Limits(aggregate_file_bytes=1),
                       self.f.api.Limits(entrypoint_bytes=1),self.f.api.Limits(inventory_files=1)]:
            self.assertIsNone(self.f.run(limits=limits)['offer'])
        for value in (-1, True, 16385):
            with self.assertRaises(ValueError):self.f.api.Limits(total_visited_entries=value)

    def test_disabled_and_declined_do_not_read_inventory_or_package(self):
        for config in ({'enabled':False}, {'enabled':True,'declined':True}):
            config.update(root='/never/read',inventory=object())
            with mock.patch('os.open', side_effect=AssertionError('package read')) as opening, mock.patch('os.scandir', side_effect=AssertionError('scan')) as scanning:
                result=self.f.api.resolve(config, self.f.catalogue, required_checks=('required',))
                self.assertIsNone(result['offer']);self.assertEqual(result['required_checks'],['required'])
                opening.assert_not_called();scanning.assert_not_called()


if __name__ == '__main__':
    unittest.main()
