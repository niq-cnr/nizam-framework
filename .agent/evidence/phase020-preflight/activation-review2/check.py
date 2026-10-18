import hashlib,json,subprocess
from pathlib import Path
root=Path.cwd();git=lambda *args:subprocess.check_output(['git',*args])
old='385f376fb8360db94242df2c33acdeaf1ab5f2df';new='2508a71768111e015f36a87ddb08e7b0b135ecb7'
read=lambda rev,path:git('show',rev+':'+path)
specpath='.agent/product_spec_020.md';before=read(old,specpath).decode();after=read(new,specpath).decode()
assert after==before.replace('[Current intake delta]','[Original intake snapshot]').replace('Local 133 gates/capture are complete; its frozen PR 105 still awaits capable CI,\nnormal merge and main delivery. No current controls-ready/live Root 120 adoption is claimed.','At that snapshot, local 133 gates/capture were complete; PR 105 at frozen head\n441d292559eacb95c778b4e20bcc62350e9f31a8 still awaited capable CI, normal merge\nand main delivery. That historical snapshot is not current delivery proof.\nBefore applying activation, Root rechecks the actual current PR 105 head, all six\nrequired checks, clear feedback and normal merge. No current controls-ready/live\nRoot 120 adoption is claimed.')
for path in ('.agent/feature_list_020.json','docs/planning/phase_020.yaml','docs/planning/manifest.json','.agent/evidence/phase020-preflight/intake-current-context1.json'):
    assert read(old,path)==read(new,path),path
review=(root/'.agent/validator/phase020-activation1.json').read_bytes()
assert hashlib.sha256(review).hexdigest()=='c3884c6353646b88ccfc902851e86c1f3260c29a482cd18a71086cfadbd7603a'
assert [i['id'] for i in json.loads(review)['issues']]==['P020-ACTIVATION1-CURRENT-CONTEXT']
receipt=json.loads((root/'.agent/evidence/phase020-preflight/activation-proposal2/proposal.json').read_bytes())
for item in receipt['fourfile_inputs']:
    raw=read(new,item['path']);assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256']
for path,expected in {'.agent/contracts/129.json':'71c6374a6bd88a1110de3fceb612a1392f0b203736e13843caace9fec52c26e6','tools/test_runtime_session.py':'81a7299120ad79cca1765e6c4c47f0d8907bfa6e593804a9ffd97210700dffe4'}.items():
    assert hashlib.sha256((root/path).read_bytes()).hexdigest()==expected,path
assert not (root/'tools/sbcl_session_loop.lisp').exists()
print('STATIC_PASS exact paragraph-only correction;other3activationfiles/historicalintake unchanged;allreview1structural/budget/DAG/acceptance/ref/schema invariants retained;currentcontract/frozenbundle pins unchanged;no backend')
print('APPLICATION_BOUNDARY conditional proposal valid only with actual Root currenthead/all6/clearfeedback/normalmerge recheck and separate H-PHASE020 allocation decision;no future merge/main success asserted')
