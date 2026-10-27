"""Independent malformed programmatic-data probe; no commands or mutation."""
from pathlib import Path
import json
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
import skill_recommendations as api
calls = []
class InvalidData:
    def __eq__(self, other):
        calls.append(other)
        return False
result = api.resolve({'enabled': True, 'authoring_method': InvalidData()}, {})
print(json.dumps({'invalid_non_json_input': 'custom comparison object',
                  'comparison_callbacks_invoked': calls, 'result': result,
                  'scope': 'synthetic local probe; no real package/verifier/qualification'}, sort_keys=True))
assert not calls, 'untrusted non-JSON value comparison ran before bounded type validation'
