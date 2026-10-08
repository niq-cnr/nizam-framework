#!/usr/bin/env python3
"""Unit 11: pin semantics. read_framework_pin returns provenance.json resolved_sha verbatim (no peeling in the
reader); the peel happens at write time in bootstrap.sh (git rev-parse HEAD^{commit}). Demonstrate both."""
import importlib.util, json, os, subprocess, sys, tempfile
spec = importlib.util.spec_from_file_location("emr", "tools/ecosystem_membership_run.py")
emr = importlib.util.module_from_spec(spec); spec.loader.exec_module(emr)
git = lambda *a: subprocess.run(["git", *a], capture_output=True, text=True, check=True).stdout.strip()
tagobj, peeled = git("rev-parse", "v1.4.0"), git("rev-parse", "v1.4.0^{commit}")
print("v1.4.0 object type:", git("cat-file", "-t", "v1.4.0"))
print("tag object:", tagobj, " peeled commit:", peeled, " commit type:", git("cat-file", "-t", peeled))
assert tagobj != peeled
def with_prov(value):
    d = tempfile.mkdtemp(prefix="pin-sem-"); os.makedirs(d + "/.nizam")
    json.dump({"resolved_sha": value}, open(d + "/.nizam/provenance.json", "w")); return d
r1 = emr.read_framework_pin(with_prov(peeled)); r2 = emr.read_framework_pin(with_prov(tagobj))
print("reader on peeled commit  ->", r1, "(equals peeled: %s)" % (r1 == peeled))
print("reader on tag object     ->", r2, "(verbatim passthrough, NOT peeled by reader: %s)" % (r2 == tagobj))
src = open("bootstrap.sh").read()
write_site = [i + 1 for i, l in enumerate(src.splitlines()) if 'rev-parse "HEAD^{commit}"' in l]
print("bootstrap.sh peel-at-write line(s):", write_site)
ok = r1 == peeled and r2 == tagobj and bool(write_site)
print("RESULT: %s -- the peeled commit is what bootstrap.sh records and the reader returns; the reader itself does not peel" % ("OK" if ok else "FAIL"))
sys.exit(0 if ok else 1)
