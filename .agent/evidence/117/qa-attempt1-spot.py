import importlib.util, tempfile
from pathlib import Path
ROOT=Path.cwd().resolve()
assert ROOT==Path('/home/cnross/.tmp/nizam-117-qa-attempt1-spyqvr9j')
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result
api=module('qa117_product','tools/workflow_assurance.py')
fixtures=module('qa117_fixture','.agent/evidence/117/entry-fixtures.py')
with tempfile.TemporaryDirectory(prefix='nizam117-qa-ancestor-') as scratch:
    owned=Path(scratch).resolve()
    f=fixtures.EntryFixture(owned)
    assert f.root.resolve().parent==owned
    f.entry.update(role='Evaluator',profile='evaluator-adversarial',writes=[{
        'path':'.agent/evidence/117/qa-alias/fresh.json','fields':[],'operation':'write'}])
    assert api.verify_authorized_entry(f.root,f.entry) is True
    print('VALID CONTROL: absent owned evidence destination accepted')
    alias=f.root/'.agent/evidence/117/qa-alias'
    destination=f.root/'outside-approved-evidence'
    destination.mkdir();alias.symlink_to(destination,target_is_directory=True)
    try:
        try: api.verify_authorized_entry(f.root,f.entry)
        except api.AssuranceError as exc:
            assert str(exc)=='symlink write-intent path',str(exc)
            print('ADVERSARIAL CONTROL: ancestor points outside approved evidence; rejected: '+str(exc))
        else: raise AssertionError('symlink ancestor escaped approved evidence boundary')
        assert not (destination/'fresh.json').exists()
    finally:
        assert f.root.resolve().parent==owned and alias.is_symlink()
        alias.unlink()
    assert api.verify_authorized_entry(f.root,f.entry) is True
    print('RESTORED CONTROL: absent owned evidence destination accepted again')
    assert not (f.root/'.agent/evidence/117/qa-alias/fresh.json').exists()
    print('READ-ONLY CONTROL: entry preflight created no intended file')
assert not owned.exists()
print('PASS: one evaluator-originated symlink ancestor policy spot; owned scratch removed')
