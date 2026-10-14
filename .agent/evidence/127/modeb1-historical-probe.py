import hashlib,json,runpy,tempfile,subprocess,os
from pathlib import Path
root=Path.cwd(); module=runpy.run_path(str(root/'tools/test_runtime_session.py'))
with tempfile.TemporaryDirectory(prefix='mb127-',dir='/tmp') as home:
    s=module['Session'](home)
    try:
        s.open(); inputs=module['source_inputs'](s.home)
        s.record=s.call('reattach-session',module['attachment'](s,inputs))['result']
        snapshot=s.directory/'handoff.json'; raw=snapshot.read_bytes(); original_generation=s.record['generation']
        s.transfer(module['HUMAN']); s.execute('set','historical-snapshot')
        assert snapshot.read_bytes()==raw
        assert s.execute('get')=='historical-snapshot'
        module['validate_records'](s)
        s.transfer(module['OWNER']); module['restart'](s)
        assert s.record['generation']!=original_generation and snapshot.read_bytes()==raw
        s.record=s.call('reattach-session',module['attachment'](s,inputs))['result']
        s.execute('set','new-generation'); assert s.execute('get')=='new-generation'
        module['validate_records'](s)
        print('PASS historical handoff survives authorized transfer, operations and clean new generation; checked reattach still succeeds')
    finally:
        s.cleanup()
