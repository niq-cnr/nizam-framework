"""Independent intentionally deficient baseline: trusts assertions and ambient HEAD.

This fixture is never product implementation. Its defects are deliberately fixed:
it accepts role/seal/proof violations, and rejects valid later record-only HEAD.
"""
import subprocess


class AssuranceError(ValueError):
    pass


def verify_acceptance_bundle(repo, bundle, independent_review):
    head = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'],
                                   stderr=subprocess.PIPE).decode().strip()
    if head != bundle['baseline']['commit']:
        raise AssuranceError('naive ambient HEAD rejected immutable baseline handoff')
    return True
