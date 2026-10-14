import copy, hashlib, json, subprocess
from pathlib import Path
import jsonschema
p=Path(".agent/contracts/126.json")
c=json.loads(p.read_text())
old=json.loads(subprocess.check_output(["git","show","88798968d016b7e56766f24c7a871eacc164085c:.agent/contracts/126.json"]))
jsonschema.Draft202012Validator(json.loads(Path(".nizam/schema/contract.schema.json").read_text())).validate(c)
normalized=copy.deepcopy(c)
for key in ["contract_attempt","approvals","interface","verification"]: normalized[key]=old[key]
assert normalized==old
assert c["contract_attempt"]==2 and c["approvals"]==dict(old["approvals"],revisions=1)
interface=copy.deepcopy(c["interface"]); interface["serialization"]=old["interface"]["serialization"]
assert interface==old["interface"]
verification=copy.deepcopy(c["verification"]); verification[1]["acceptance_test"]=old["verification"][1]["acceptance_test"]
assert verification==old["verification"]
f=next(x for x in json.loads(Path(".agent/feature_list_016.json").read_text())["features"] if x["id"]=="126")
assert [v["command"] for v in c["verification"]]==f["acceptance_tests"]
assert c["estimated_lines"]==2900 and c["budget"]["phase_total"]==5650 and c["budget"]["phase_ceiling"]==7345
paths=subprocess.check_output(["git","diff","--name-only","HEAD"],text=True).splitlines()+subprocess.check_output(["git","ls-files","--others","--exclude-standard"],text=True).splitlines()
assert all(x in [str(p),".agent/run_state.json"] or x.startswith(".agent/evidence/126/") for x in paths)
subprocess.run(["git","diff","--check","HEAD"],check=True)
print(json.dumps({"pass":True,"contract_sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"checks":["installed schema","only round metadata, serialization precedence and AT2 changed","nine exact commands","original budgets","current amendment scope with attributed Root coordination","whitespace"]}))
