"""Deliberately deficient callable baseline: trusts assertions and default roles.

This control is test data, not a second entry implementation. It illustrates
self-reported authority/pin trust and overly broad Generator path scope while
incorrectly denying explicitly authorized Evaluator test authorship.
"""
class AssuranceError(ValueError): pass


def verify_authorized_entry(repo, entry):
    if entry['repository'] != 'niq-cnr/nizam-framework':
        raise AssuranceError('claimed repository denied')
    if entry['installed']['tag'] != 'v1.5.0':
        raise AssuranceError('claimed pin denied')
    if entry['role'] != 'Generator':
        raise AssuranceError('default permission class forbids code editing')
    if any(not x['path'].startswith(('tools/', '.agent/')) for x in entry['writes']):
        raise AssuranceError('outside broad task path scope')
    return True
