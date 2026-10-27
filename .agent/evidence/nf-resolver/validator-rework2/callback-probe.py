"""Independent callback/refusal probe; no real package or trusted verifier."""
import sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
import skill_recommendations as api

calls=[]
class Key:
    def __hash__(self): return hash('enabled')
    def __eq__(self, other): calls.append('key'); raise RuntimeError('unexpected key comparison')
class Bad(str):
    __hash__=str.__hash__
    def __eq__(self, other): calls.append('str'); raise RuntimeError('unexpected string comparison')
class Meta(type):
    def __eq__(self, other): calls.append('meta'); raise RuntimeError('unexpected type comparison')
class Obj(metaclass=Meta): pass
class Mapping(dict):
    def get(self,*a): calls.append('get'); raise RuntimeError('unexpected lookup')
    def items(self): calls.append('items'); raise RuntimeError('unexpected iteration')
class Raising:
    def __eq__(self, other): calls.append('value'); raise RuntimeError('unexpected comparison')

cases=[{Key(): 'x'}, {Bad('enabled'): True}, {'enabled':True,'authoring_method':Bad('direct')},
       {'enabled':True,'authoring_method':Raising()}, {'enabled':True,'nested':Obj()}, Mapping(enabled=True),
       {'enabled':False,'inventory':Obj()}, {'enabled':True,'declined':True,'inventory':Obj()}]
for config in cases:
    calls.clear()
    with patch('os.open', side_effect=AssertionError('unexpected package read')) as opened:
        result=api.resolve(config, {}, required_checks=('host-required',))
        assert result['offer'] is None and result['required_checks']==['host-required']
        assert not calls, calls
        opened.assert_not_called()
print('eight callback/malformed/disabled/declined cases: no callbacks, reads, offers or assurance downgrade')
