#!/usr/bin/env python3
"""Synthetic specialist routing preserves host requirements and selection."""
import tempfile
import unittest
from pathlib import Path
from unittest import mock
from test_skill_recommendations import SyntheticFixture

class RoutingTests(unittest.TestCase):
    def test_context_routes_and_ambiguous_none(self):
        import skill_recommendations as api
        for kind,expected in [('readme','readme-docs'),('tutorial','tutorial-docs'),('reference','software-docs'),
             ('operations','software-docs'),('documentation-architecture','software-docs'),('code',None),('ambiguous',None)]:
            self.assertEqual(api.route(kind),expected)

    def test_only_deliberately_selected_matching_entrypoint(self):
        with tempfile.TemporaryDirectory(prefix='nf-route-') as tmp:
            f=SyntheticFixture(tmp)
            for method in ('direct','alternate'):
                f.config['authoring_method']=method
                result=f.run(required_checks=('same-required-check',))
                self.assertIsNone(result['offer']);self.assertEqual(result['required_checks'],['same-required-check'])
            f.config.pop('authoring_method')
            result=f.run(required_checks=('same-required-check',))
            self.assertEqual(result['offer']['entrypoint'],str(f.package/'SKILL.md'))
            # Host deliberately loads the returned relevant path; resolver returns no body.
            self.assertNotIn('Synthetic selected body',str(result))
            f.config['selected_skill']='software-docs';self.assertIsNone(f.run()['offer'])
            f.config['task_kind']='ambiguous';self.assertIsNone(f.run()['offer'])

if __name__=='__main__':unittest.main()
