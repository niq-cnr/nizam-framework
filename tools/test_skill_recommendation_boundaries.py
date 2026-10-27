#!/usr/bin/env python3
"""Real temporary-root Nizam host-boundary controls; no DS conformance claim."""
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tracemalloc
import unittest
from unittest import mock
from test_skill_recommendations import SyntheticFixture


class BoundaryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='nf-boundary-');self.addCleanup(self.tmp.cleanup)
        self.f=SyntheticFixture(self.tmp.name)

    def assertClosed(self):
        result=self.f.run();self.assertIsNone(result['offer']);self.assertNotEqual(result['local_state'],'compatible')

    def test_opaque_selector_values_keys_and_types_never_run_callbacks(self):
        api=self.f.api;calls=[]
        class Opaque:
            def __eq__(self,other):calls.append('opaque-equality');return False
        class Raising:
            def __eq__(self,other):calls.append('raising-equality');raise RuntimeError('forbidden comparison')
            def __hash__(self):return hash('enabled')
        class StringSubclass(str):
            __hash__=str.__hash__
            def __eq__(self,other):calls.append('string-subclass-equality');raise RuntimeError('forbidden selector')
        class HostileMeta(type):
            def __eq__(cls,other):calls.append('metaclass-equality');raise RuntimeError('forbidden type comparison')
        class Nested(metaclass=HostileMeta):pass
        class DictSubclass(dict):
            def get(self,*args):calls.append('dict-get');raise RuntimeError('forbidden lookup')
            def items(self):calls.append('dict-items');raise RuntimeError('forbidden iteration')
        cases=[{'enabled':True,'authoring_method':Opaque()},
               {'enabled':True,'authoring_method':Raising()},
               {'enabled':True,'authoring_method':StringSubclass('direct')},
               {Raising():'opaque-key'}, {StringSubclass('enabled'):True},
               {'enabled':True,'nested':Nested()},DictSubclass(enabled=True),
               {'enabled':False,'inventory':Nested()},
               {'enabled':True,'declined':True,'inventory':Nested()}]
        for config in cases:
            calls.clear()
            try:
                with mock.patch('os.open',side_effect=AssertionError('unexpected package read')) as opening:
                    result=api.resolve(config,self.f.catalogue,framework=self.f.framework)
                    opening.assert_not_called()
            except Exception as exc:self.fail('untrusted selector escaped advisory boundary: '+type(exc).__name__)
            self.assertIsNone(result['offer']);self.assertEqual(calls,[],'untrusted data invoked Python callbacks')
        calls.clear();self.assertIsNone(api.route(StringSubclass('readme')));self.assertEqual(calls,[])

    def test_disabled_header_cardinality_is_bounded_before_snapshot(self):
        api=self.f.api;config={str(n):object() for n in range(65536)}
        config['enabled']=False
        with mock.patch.object(api,'bounded_snapshot',side_effect=AssertionError('overflow snapshot')) as snapshot, mock.patch('os.open',side_effect=AssertionError('package open')) as opening:
            tracemalloc.start()
            try:
                result=api.resolve(config,self.f.catalogue)
                _,peak=tracemalloc.get_traced_memory()
            finally:tracemalloc.stop()
            self.assertEqual(result['reason'],'configuration-too-many-items')
            self.assertIsNone(result['offer']);snapshot.assert_not_called();opening.assert_not_called()
            self.assertLess(peak,64*1024)

    def test_programmatic_configuration_allocation_bound(self):
        for label,target in [('configuration',self.f.config),('catalogue',self.f.catalogue)]:
            target['note']='x'*(8*1024*1024)
            tracemalloc.start()
            try:
                result=self.f.run(verifier=None)
                _,peak=tracemalloc.get_traced_memory()
            finally:tracemalloc.stop()
            self.assertIsNone(result['offer'])
            self.assertLess(peak,512*1024, f'oversized scalar allocated {peak} bytes before refusal')
            print(f'{label}: 8MiB input, additional traced allocation={peak}, rejected before encoding')
            target.pop('note')

    def test_bounded_json_depth_cycles_cardinality_and_snapshot(self):
        api=self.f.api
        cycle=[];cycle.append(cycle)
        deep=0
        for _ in range(40):deep=[deep]
        for value,reason in [(cycle,'cyclic-configuration'),(deep,'configuration-too-deep'),
                  ([0]*65537,'configuration-too-many-items'),(b'x'*(2*1024*1024),'invalid-configuration-type'),
                  (1<<8192,'invalid-configuration-number')]:
            self.f.config['note']=value
            result=self.f.run(verifier=None)
            self.assertIsNone(result['offer']);self.assertEqual(result['reason'],reason)
        original={'name':['safe',{'size':3}]}
        snapshot=api.bounded_snapshot(original,1024)
        original['name'].append('x'*(2*1024*1024))
        self.assertEqual(snapshot,{'name':['safe',{'size':3}]})
        for value in ['a','quote"slash\\',chr(0),chr(0x1f600),{'x':[True,None,2,1.5]}]:
            size=len(api.canonical(value))
            self.assertEqual(api.bounded_snapshot(value,size),value)
            with self.assertRaises(api.ObservationError):api.bounded_snapshot(value,size-1)
        self.f.config['enabled']=False
        with mock.patch.object(api,'bounded_snapshot',side_effect=AssertionError('disabled snapshot')) as called:
            self.assertIsNone(self.f.run(verifier=None)['offer']);called.assert_not_called()

    def test_real_links_special_files_and_escaping_roots(self):
        outer=Path(tempfile.mkdtemp(prefix='nf-outside-')).resolve();self.addCleanup(shutil.rmtree,outer)
        secret=outer/'private';secret.write_bytes(b'OUTSIDE_SENTINEL')
        target=self.f.package/'SKILL.md';target.unlink();target.symlink_to(secret)
        with mock.patch('os.read', wraps=os.read) as reads:
            self.assertClosed()
        target.unlink();target.symlink_to(outer/'absent');self.assertClosed()
        target.unlink();os.link(secret,target);self.assertClosed()
        target.unlink();os.mkfifo(target);self.assertClosed()
        target.unlink();target.mkdir();self.assertClosed()
        alias=self.f.root/'alias';alias.symlink_to(self.f.package,target_is_directory=True)
        self.f.config['package']='alias';self.assertClosed()
        self.f.config['root']=str(alias);self.f.config['package']='x';self.assertClosed()

    def test_valid_empty_dirs_and_selected_only(self):
        (self.f.package/'empty').mkdir();(self.f.package/'empty/nested').mkdir()
        unrelated=self.f.root/'tutorial-docs';unrelated.mkdir();(unrelated/'SKILL.md').symlink_to('/no/read')
        reads=[];actual=os.open
        def guarded(path,*a,**kw):
            reads.append(str(path));return actual(path,*a,**kw)
        with mock.patch('os.open',side_effect=guarded):self.assertEqual(self.f.run()['local_state'],'compatible')
        self.assertNotIn('tutorial-docs',reads)

    def test_operation_wide_incremental_empty_directory_bounds(self):
        for p in self.f.package.iterdir():p.unlink()
        for n in range(20):(self.f.package/f'empty{n:02}').mkdir()
        anchor_entries=len(self.f.root.parts)-1+1
        anchor_directories=anchor_entries+1
        original=os.scandir;seen=[]
        class Counted:
            def __init__(self,fd):self.it=original(fd)
            def __enter__(self):return self
            def __exit__(self,*args):self.it.close()
            def __iter__(self):return self
            def __next__(self):
                x=next(self.it);seen.append(x.name);return x
        with mock.patch('os.scandir',side_effect=Counted):
            result=self.f.run(limits=self.f.api.Limits(total_visited_entries=anchor_entries+5))
        self.assertIsNone(result['offer']);self.assertEqual(len(seen),6)
        self.assertEqual(result['reason'],'entry-budget-exceeded')
        result=self.f.run(limits=self.f.api.Limits(total_visited_directories=anchor_directories+3))
        self.assertIsNone(result['offer']);self.assertEqual(result['reason'],'directory-budget-exceeded')
        # Initial walk fits but repeated verification walk exhausts the SAME budget.
        for p in self.f.package.iterdir():
            if p.is_dir():p.rmdir()
        (self.f.package/'SKILL.md').write_bytes(b'# Synthetic selected body\n')
        (self.f.package/'.hidden').write_bytes(b'included')
        result=self.f.run(limits=self.f.api.Limits(total_visited_entries=anchor_entries+3))
        self.assertIsNone(result['offer']);self.assertEqual(result['reason'],'entry-budget-exceeded')

    def test_read_once_and_concurrent_byte_change(self):
        original=os.read;seen=[]
        def read(fd,n):seen.append(os.fstat(fd).st_ino);return original(fd,n)
        with mock.patch('os.read',side_effect=read):self.assertEqual(self.f.run()['local_state'],'compatible')
        # Two small files: one data read and one EOF read per file; never re-read to hash.
        self.assertEqual(len(seen),4)
        fired=False
        def change(fd,n):
            nonlocal fired
            chunk=original(fd,n)
            if chunk and not fired:
                fired=True
                current=next(p for p in self.f.package.iterdir() if p.stat().st_ino==os.fstat(fd).st_ino)
                current.write_bytes(b'concurrently changed')
            return chunk
        with mock.patch('os.read',side_effect=change):self.assertClosed()
        self.assertTrue(fired)

    def test_real_ancestor_replacement_and_link_swap(self):
        original=os.read;done=False
        def swap(fd,n):
            nonlocal done
            chunk=original(fd,n)
            if chunk and not done:
                done=True;self.f.package.rename(self.f.root/'moved');self.f.package.symlink_to(self.f.root/'moved',target_is_directory=True)
            return chunk
        with mock.patch('os.read',side_effect=swap):self.assertClosed()
        self.assertTrue(done)

    def test_unsupported_host_and_path_aliases_fail_closed(self):
        with mock.patch.object(self.f.api,'nofollow_supported',return_value=False):self.assertClosed()
        for path in ('../escape','/absolute','x//y','x/./y','x/../y','x\\y','x\0y'):
            self.f.config['package']=path;self.assertClosed()
        self.f.config['package']='readme-docs'
        for path in ('../SKILL.md','SKILL.md/','a//b'):
            self.f.config['inventory']=[dict(path=path,size=0,sha256='0'*64)];self.assertClosed()

    def test_real_file_swap_before_open_does_not_read_outside(self):
        with tempfile.TemporaryDirectory(prefix='nf-outside-race-') as tmp:
            secret=Path(tmp)/'outside';secret.write_bytes(b'OUTSIDE_SECRET_BYTES')
            original=os.open;escaped=[];swapped=[]
            def racing(path,flags,*args,**kwargs):
                if path=='SKILL.md' and not flags & os.O_DIRECTORY and not swapped:
                    swapped.append(True);target=self.f.package/'SKILL.md';target.unlink();target.symlink_to(secret)
                fd=original(path,flags,*args,**kwargs)
                if os.fstat(fd).st_ino==secret.stat().st_ino:escaped.append(True)
                return fd
            with mock.patch('os.open',side_effect=racing):self.assertClosed()
            self.assertTrue(swapped);self.assertFalse(escaped)

    def test_unsafe_observation_mutant_cannot_pass_boundaries(self):
        with tempfile.TemporaryDirectory(prefix='nf-unsafe-mutant-') as tmp:
            root=Path(tmp);source=Path(self.f.api.__file__).resolve().parents[1]
            shutil.copytree(source/'tools',root/'tools',ignore=shutil.ignore_patterns('__pycache__'))
            shutil.copytree(source/'schema',root/'schema')
            path=root/'tools/skill_recommendations.py';text=path.read_text()
            begin=text.index('def observe(');end=text.index('\ndef validate_catalogue(',begin)
            text=text[:begin]+"def observe(root, package, inventory, entrypoint, limits):\n    return host_digest(inventory)\n\n"+text[end:]
            path.write_text(text)
            command=[sys.executable,'tools/test_skill_recommendation_boundaries.py']
            env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
            valid=subprocess.run(command+['BoundaryTests.test_valid_empty_dirs_and_selected_only'],cwd=root,env=env,capture_output=True,text=True)
            bad=subprocess.run(command+['BoundaryTests.test_real_links_special_files_and_escaping_roots'],cwd=root,env=env,capture_output=True,text=True)
            self.assertEqual(valid.returncode,0,valid.stdout+valid.stderr)
            self.assertEqual(bad.returncode,1,bad.stdout+bad.stderr)
            self.assertIn("'compatible'",bad.stderr)

    def test_subprocess_no_execution_network_or_mutation(self):
        # A real poison body remains inert, and outside data never enters output.
        marker=self.f.root/'executed';body=b"import os;os.system('touch executed');https://example.invalid/secret"
        (self.f.package/'SKILL.md').write_bytes(body);self.f.config['inventory']=self.f.inventory()
        config=self.f.root/'config.json';config.write_text(json.dumps(self.f.config))
        catalogue=self.f.root/'catalogue.json';catalogue.write_text(json.dumps(self.f.catalogue))
        script=Path(self.f.api.__file__)
        before={p.relative_to(self.f.root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in self.f.root.rglob('*') if p.is_file()}
        run=subprocess.run([sys.executable,str(script),'--config',str(config),'--catalogue',str(catalogue)],capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stderr);self.assertNotIn('example.invalid',run.stdout)
        after={p.relative_to(self.f.root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in self.f.root.rglob('*') if p.is_file()}
        self.assertEqual(before,after);self.assertFalse(marker.exists())
        # Real selected-byte observation with a programmatic synthetic verifier,
        # under a subprocess audit hook denying process/network/write effects.
        harness='''import json,sys,os
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from test_skill_recommendations import SyntheticFixture
import skill_recommendations as api
f=object.__new__(SyntheticFixture);f.api=api
f.config=json.loads(Path(sys.argv[2]).read_text());f.catalogue=json.loads(Path(sys.argv[3]).read_text())
f.framework=api.FrameworkIdentity('c'*40,'e'*64,'d'*64)
verifier=f.verifier();api.validate_catalogue(f.catalogue)
events=[]
def audit(event,args):
 if event in ('socket.__new__','socket.connect','subprocess.Popen','os.system','os.remove','os.rename','os.mkdir','os.rmdir','os.link','os.symlink'):
  raise AssertionError('forbidden effect '+event)
 if event=='open':
  flags=args[2]
  if isinstance(flags,int) and flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):
   raise AssertionError('forbidden write')
  events.append(str(args[0]))
sys.addaudithook(audit)
result=f.run(verifier=verifier)
assert result['local_state']=='compatible',result
assert 'SKILL.md' in events,events
assert 'example.invalid' not in str(result)
print('selected synthetic bytes observed; process/network/mutation guards held')
'''
        guarded=subprocess.run([sys.executable,'-c',harness,str(script.parent),str(config),str(catalogue)],
             env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True)
        self.assertEqual(guarded.returncode,0,guarded.stdout+guarded.stderr)
        self.assertEqual(before,{p.relative_to(self.f.root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in self.f.root.rglob('*') if p.is_file()})


if __name__=='__main__':unittest.main()
