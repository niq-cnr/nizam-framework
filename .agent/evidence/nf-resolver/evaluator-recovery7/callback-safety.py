"""Independent recovery controls; no package verifier or DS qualification."""
import json
from pathlib import Path
import runpy
import sys
import tempfile
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
import skill_recommendations as api
calls = []
results = []
def check(name, value):
    calls.clear()
    result = api.resolve(value, {}, required_checks=('execution-required',))
    assert not calls, (name, calls)
    assert result['offer'] is None
    assert result['required_checks'] == ['execution-required']
    results.append(name)
class Key:
    def __hash__(self): return hash('enabled')
    def __eq__(self, other): calls.append('key-equality'); return False
key = Key()
config = {key: 'invalid', 'enabled': True}
check('colliding nonstring top-level key', config)
class Value(str):
    def __eq__(self, other): calls.append('value-equality'); return False
check('authoring selector str subclass', {'enabled':True,'authoring_method':Value('direct')})
class Raising:
    def __eq__(self, other): calls.append('raising-equality'); raise RuntimeError('must not execute')
check('raising selector remains inert', {'enabled':True,'authoring_method':Raising()})
class Meta(type):
    def __eq__(cls, other): calls.append('metaclass-equality'); return False
class Nested(metaclass=Meta): pass
check('nested custom metaclass inert', {'enabled':True,'nested':Nested()})
class DictTrap(dict):
    def get(self, *a): calls.append('dict-get'); raise RuntimeError('must not execute')
    def __iter__(self): calls.append('dict-iter'); raise RuntimeError('must not execute')
check('top-level dictionary subclass inert', DictTrap(enabled=True))
class Opaque:
    def __repr__(self): calls.append('repr'); raise RuntimeError('must not execute')
    def __str__(self): calls.append('str'); raise RuntimeError('must not execute')
    def __bool__(self): calls.append('bool'); raise RuntimeError('must not execute')
    def __eq__(self, other): calls.append('opaque-equality'); raise RuntimeError('must not execute')
check('disabled nested input not touched', {'enabled':False,'inventory':Opaque()})
check('declined nested input not touched', {'enabled':True,'declined':True,'inventory':Opaque()})
check('direct authoring nested input not touched', {'enabled':True,'authoring_method':'direct','inventory':Opaque()})
check('invalid opaque nested input not disclosed', {'enabled':True,'nested':Opaque()})
with tempfile.TemporaryDirectory(prefix='nf-independent-json-') as temporary:
    source = Path(temporary) / 'input.json'
    source.write_text('{"enabled":false,"enabled":true}')
    try:
        api.read_json(source, 1024)
    except ValueError as error:
        assert str(error) == 'duplicate-json-key'
    else:
        raise AssertionError('duplicate configuration keys accepted')
results.append('duplicate JSON keys rejected')
# Re-execute original independently authored assertions: no callback execution,
# and untracked inputs inserted at the second walk cannot reuse assessed bytes.
prior = Path(__file__).parent.parent / 'evaluator'
runpy.run_path(str(prior / 'prevalidation-probe.py'), run_name='__main__')
runpy.run_path(str(prior / 'independent-race.py'), run_name='__main__')
print(json.dumps({'scope':'independent synthetic host observation only','passed_controls':results,
                  'callback_invocations':calls,'qualification_verifier':'none',
                  'DS_qualification':'not_assessed'}, sort_keys=True))
