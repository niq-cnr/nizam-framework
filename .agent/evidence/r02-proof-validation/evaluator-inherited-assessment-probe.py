import sys,tempfile,os,json
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/"tools"))
import test_workflow_assurance as t
api=t.load_api();os.environ["NIZAM_WA_TEST_VALUE"]="probe"
with tempfile.TemporaryDirectory(prefix="r02-evaluator-inherited-") as d:
 f=t.Fixture(d);identity=f.assess(api)
 f.write("other.txt","inherited unrelated work\n")
 try:f.assess(api);raise AssertionError("global assessor unexpectedly accepted drift")
 except api.AssuranceError as e:refusal=str(e)
 api._receipt_candidate(f.root,identity)
 print(json.dumps({"case":"unselected inherited tracked bytes","global_assessor_refusal":refusal,"selected_identity_verifier":"accepted"}))
 f.write("scratch.txt","inherited untracked\n")
 (f.root/"dangling").symlink_to("/nonexistent-evaluator-r02")
 try:f.assess(api);raise AssertionError("global assessor unexpectedly accepted untracked")
 except api.AssuranceError as e:refusal=str(e)
 api._receipt_candidate(f.root,identity)
 print(json.dumps({"case":"unselected inherited untracked and dangling symlink","global_assessor_refusal":refusal,"selected_identity_verifier":"accepted"}))
