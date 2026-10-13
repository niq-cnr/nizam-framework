import hashlib,importlib.util,os,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
r=load("reviewed_tests",ROOT/"tools/test_workflow_assurance.py");a=load("source_candidate",ROOT/"tools/workflow_assurance.py")
os.environ["NIZAM_WA_TEST_VALUE"]="initial-observed-value"
with tempfile.TemporaryDirectory(prefix="nizam115-modeb-ownprobe-") as temp:
 f=r.Fixture(temp);before=f.assess(a);p=f.root/"other.txt";saved=p.read_bytes()
 assert before["source_commit"]==f.commit
 r.git(f.root,"update-index","--assume-unchanged","other.txt");p.write_bytes(saved+b"hidden unknown drift\n")
 assert r.git(f.root,"diff","--name-only")=="", "Git assume-unchanged setup must actually hide diff"
 print("PASS valid baseline/setup: actual immutable Git fixture; ordinary Git diff hides changed unknown tracked path")
 try:f.assess(a)
 except a.AssuranceError as exc:
  assert str(exc)=="unknown/assessed bytes changed: other.txt";print("PASS own adversary: actual raw-byte assessment rejects assume-unchanged hidden unknown drift:",str(exc))
 else:raise AssertionError("hidden unknown drift false pass")
 p.write_bytes(saved);r.git(f.root,"update-index","--no-assume-unchanged","other.txt")
 assert a.compare_identity(before,f.assess(a)) is True
 print("PASS own adversary restored clean assessed identity")
print("EXIT 0")
