"""Independent focused producer regressions; execute only after Root release."""
import gc
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import stat
import subprocess
import sys
import tempfile
import tracemalloc

ROOT=Path(__file__).resolve().parents[3]
EXPECTED='7ab3b092188383897900b7f84af2c22156d662ebe355e25b837b250123b49905'
LIMIT=2*1024*1024
MEMORY=32*1024*1024

def require(value,message):
    if not value:raise AssertionError(message)

def sha(data):return hashlib.sha256(data).hexdigest()

def git(root,*args):
    return subprocess.check_output(['git','-C',str(root),*args],stderr=subprocess.PIPE).decode().strip()

def snapshot():
    paths=git(ROOT,'ls-files','.nizam').splitlines()
    paths+=['tools/workflow_assurance.py','tools/test_workflow_assurance.py','tools/workflow_assurance_ci.py',
        '.agent/contracts/123.json','.agent/run_state.json','.agent/feature_list_018.json','docs/planning/phase_018.yaml']
    return {p:(stat.S_IMODE((ROOT/p).lstat().st_mode),(ROOT/p).lstat().st_nlink,sha((ROOT/p).read_bytes())) for p in paths}

def measured(operation):
    gc.collect();tracemalloc.start()
    try:
        result=operation();peak=tracemalloc.get_traced_memory()[1]
    finally:tracemalloc.stop()
    require(peak<MEMORY,'parent buffered offered oversized payload: peak='+str(peak))
    return result,peak

def failure_frame(output,label,argv,fixture,process):
    frame=json.loads((output/(label+'-failure.json')).read_bytes())
    require(frame['argv']==argv and frame['cwd']==str(fixture),'failure actual argv/cwd')
    require(frame['revision']==git(fixture,'rev-parse','HEAD') and frame['actual_exit']==process.returncode,'failure actual revision/exit')
    for name in ('stdout','stderr'):
        path=Path(frame[name]);require(not path.is_absolute() and len(path.parts)==1,'safe retained stream path')
        require((output/path).read_bytes()==getattr(process,name),'exact retained '+name)
    return frame

def main():
    require(os.environ.get('PYTHONDONTWRITEBYTECODE')=='1','explicit no-bytecode environment')
    runner_path=ROOT/'tools/workflow_assurance_ci.py'
    require(sha(runner_path.read_bytes())==EXPECTED,'exact committed collector pin')
    before=snapshot()
    require(sha((ROOT/'tools/workflow_assurance.py').read_bytes())=='7385ee079e47c70e7939692f7505898f2dc81f07629a5d9dc11e89ded3cf90ae','unchanged verifier pin')
    require(sha((ROOT/'tools/test_workflow_assurance.py').read_bytes())=='9bafd83bb18933bf103930d461fe681e42804f45ec7cdd065d74a7ffb5c75d00','unchanged acceptance pin')
    spec=importlib.util.spec_from_file_location('independent_focused_collector',runner_path)
    runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
    results=[]
    def passed(name,**details):
        results.append(dict(name=name,passed=True,**details));print('PASS '+name,flush=True)
    with tempfile.TemporaryDirectory(prefix='nizam123-focused-collector-') as directory:
        fixture=Path(directory)/'repo';fixture.mkdir();output=Path(directory)/'output';output.mkdir()
        git(fixture,'init','-q');git(fixture,'config','user.name','Independent collector check')
        git(fixture,'config','user.email','collector@example.invalid');git(fixture,'config','gc.auto','0');git(fixture,'config','maintenance.auto','false')
        sentinel=fixture/'sentinel';sentinel.write_bytes(b'owned fixture unchanged\n')
        git(fixture,'add','sentinel');git(fixture,'commit','-qm','independent fixture anchor')
        original=sentinel.read_bytes();original_mode=sentinel.stat().st_mode
        stdout=b'zero\x00\xff UTF8 \xe2\x98\x83\n';stderr=b'error\x00\xfe\n'
        code='import os;os.write(1,'+repr(stdout)+');os.write(2,'+repr(stderr)+')'
        result=runner.command([sys.executable,'-c',code],fixture)
        require(result.returncode==0 and result.stdout==stdout and result.stderr==stderr,'exact binary-safe successful streams')
        passed('small-success',actual_exit=result.returncode)
        incoming=b'input\x00\xff\n'
        result=runner.command([sys.executable,'-c','import sys;sys.stdout.buffer.write(sys.stdin.buffer.read());sys.stderr.buffer.write(b"stdin-complete")'],fixture,input=incoming)
        require(result.returncode==0 and result.stdout==incoming and result.stderr==b'stdin-complete','exact optional small stdin')
        passed('small-stdin',actual_exit=result.returncode)
        result=runner.command([sys.executable,'-c','import os;os.write(1,b"x"*'+str(LIMIT)+');os.write(2,b"edge")'],fixture)
        require(result.returncode==0 and result.stdout==b'x'*LIMIT and result.stderr==b'edge','admitted exact2MiB boundary')
        passed('exact-admitted-boundary',stdout_bytes=len(result.stdout))
        failed_out=b'PASS favorable label\n';failed_err=b'actual child exit7\n'
        argv=[sys.executable,'-c','import os;os.write(1,'+repr(failed_out)+');os.write(2,'+repr(failed_err)+');raise SystemExit(7)']
        result=runner.stage_command(output,'exit7',argv,fixture)
        require(result.returncode==7 and result.stdout==failed_out and result.stderr==failed_err,'nonzero child remains failed with exact streams')
        failure_frame(output,'exit7',argv,fixture,result);passed('nonzero-child',actual_exit=7)
        for stream,fd,other_fd,byte in [('stdout',1,2,b'O'),('stderr',2,1,b'E')]:
            marker=b'other-stream-before-overflow\n';label=stream+'-overflow'
            code='import os;os.write('+str(other_fd)+','+repr(marker)+');block='+repr(byte)+'*65536\nfor n in range(1024):\n os.write('+str(fd)+',block)\n'
            argv=[sys.executable,'-c',code]
            def overflow():
                try:runner.stage_command(output,label,argv,fixture)
                except runner.OutputLimitExceeded as exc:return exc.process
                raise AssertionError('oversized child output accepted as successful proof')
            process,peak=measured(overflow);metadata=process.output_limit
            require(metadata['exceeded_stream']==stream and metadata['limit_bytes']==LIMIT,'overflow stream and admitted bound')
            require(metadata['unobserved_tail'] is True and metadata['streams_complete'][stream] is False,'overflow explicitly partial, not complete success')
            require(metadata['observed_bytes'][stream]>LIMIT,'overflow actually observed')
            for name in ('stdout','stderr'):
                raw=getattr(process,name);require(len(raw)<=LIMIT and metadata['retained_bytes'][name]==len(raw),'bounded retained '+name)
                expected=byte*len(raw) if name==stream else marker[:len(raw)]
                require(raw==expected,'truthful actual retained prefix '+name)
            require(type(process.returncode) is int,'actual observed termination type')
            if metadata['terminated_owned_child']:require(process.returncode<0,'owned child kill reports actual signal exit')
            frame=failure_frame(output,label,argv,fixture,process)
            require(frame['output_limit']==metadata,'retained overflow metadata exact')
            passed(label,actual_exit=process.returncode,parent_peak_bytes=peak,retained_bytes=metadata['retained_bytes'])
        value={'unicode':'雪☃é🙂','controls':'quote" slash\\ newline\n tab\t NUL\x00 other\x01','nested':[True,None,3,1.25]}
        expected=(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)+'\n').encode()
        require(runner.bounded_encoded(value)==expected,'canonical Unicode/control escaping exact')
        target=runner.put(output,'valid.json',value);require(target.read_bytes()==expected,'valid JSON exact payload write')
        passed('json-valid-unicode-controls',payload_bytes=len(expected))
        # Construct large input before tracemalloc: measure serialization overhead only.
        oversized={'payload':'\x00'*(16*1024*1024)};target=output/'oversized.json'
        def reject_json():
            try:runner.put(output,'oversized.json',oversized)
            except RuntimeError as exc:
                require('bound' in str(exc).lower(),'JSON refusal identifies bound');return str(exc)
            raise AssertionError('oversized escaped JSON serialized/written')
        diagnostic,peak=measured(reject_json)
        require(not target.exists(),'oversized JSON creates no payload file')
        passed('json-oversized-before-allocation-write',parent_peak_bytes=peak,diagnostic=diagnostic)
        require(sentinel.read_bytes()==original and sentinel.stat().st_mode==original_mode,'owned outside sentinel unchanged')
    require(snapshot()==before,'repository Source/tests/contract/installed/current coordination bytes/modes unchanged')
    print(json.dumps(dict(focused_checks=results,checks_run=len(results),checks_passed=len(results),runner_sha256=EXPECTED,
        preserved_inputs=len(before),scope='Independent producer-helper behavior only; no mandatory suite, namespace, hosted workflow or final gate.'),sort_keys=True))
    return 0

def timeout(signum,frame):raise TimeoutError('focused helper exceeded60s timeout')

if __name__=='__main__':
    signal.signal(signal.SIGALRM,timeout);signal.setitimer(signal.ITIMER_REAL,60)
    try:raise SystemExit(main())
    finally:signal.setitimer(signal.ITIMER_REAL,0)
