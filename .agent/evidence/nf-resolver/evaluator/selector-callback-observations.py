"""Observe callback safety of malformed host data; no process or file effects."""
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
import skill_recommendations as api

observations = []
callbacks = []
class Key:
    def __hash__(self): return hash('enabled')
    def __eq__(self, value): callbacks.append('key-equality'); return False
key = Key()
config = {key: 'invalid', 'enabled': True}
callbacks.clear()
result = api.resolve(config, {})
observations.append({'case':'nonstring key colliding with enabled', 'callbacks':list(callbacks), 'result':result})
assert callbacks

callbacks.clear()
class Value(str):
    def __eq__(self, other): callbacks.append('str-subclass-equality'); return False
result = api.resolve({'enabled':True,'authoring_method':Value('direct')}, {})
observations.append({'case':'authoring method string subclass', 'callbacks':list(callbacks), 'result':result})
assert callbacks

class Raising:
    def __eq__(self, other): raise RuntimeError('synthetic equality callback')
try:
    api.resolve({'enabled':True, 'authoring_method':Raising()}, {})
except RuntimeError:
    observations.append({'case':'raising authoring method comparison','result':'exception escaped resolver advisory boundary'})
else:
    raise AssertionError('expected current prevalidation exception was not observed')

callbacks.clear()
class DictTrap(dict):
    def get(self, *args): callbacks.append('dict-subclass-get'); raise RuntimeError('must not call')
result = api.resolve(DictTrap(enabled=True), {})
observations.append({'case':'top-level dictionary subclass control', 'callbacks':list(callbacks), 'result':result})
assert not callbacks

callbacks.clear()
class Meta(type):
    def __eq__(cls, other): callbacks.append('metaclass-equality'); return False
class Object(metaclass=Meta): pass
result = api.resolve({'enabled':True, 'untrusted_nested':Object()}, {})
observations.append({'case':'nested invalid type with metaclass equality', 'callbacks':list(callbacks), 'result':result})
assert callbacks
print(json.dumps({'scope':'synthetic invalid in-memory host data; no package, verifier, network, subprocess or write',
                  'observations':observations}, sort_keys=True))
