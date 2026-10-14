"""Deliberately wrong, callable commissioning control; never product code."""
class AssuranceError(ValueError): pass

def verify_foundation_ready(repo, prerequisite):
    return prerequisite.get('passed') is True
