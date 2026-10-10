python3 - <<'PY'
import json, re, subprocess, sys
import yaml
A = "7972e4f2d46abf6b8e0f02e8c11e94ac0f7aa0f4"
run = lambda *a: subprocess.run(a, capture_output=True, text=True, check=True).stdout
bad = []
pins = json.load(open(".agent/contracts/107.json"))["design_notes"]["pinned_interface"]

def show(path):
    return run("git", "show", A + ":" + path)

def between(text, start, end):
    i = text.index(start)
    j = text.index(end, i)
    return text[i:j]

base_v = show("tools/validate.sh")
new_v = open("tools/validate.sh").read()
expect_v = base_v.replace(pins["c1_help_old"], pins["c1_help_new"], 1)
expect_v = expect_v.replace(pins["c2_help_old"], pins["c2_help_new"], 1)
expect_v = expect_v.replace(pins["call_old"], pins["call_new"], 1)
if new_v != expect_v:
    bad.append("tools/validate.sh is not base plus the three pinned edits")
if new_v.count(pins["c1_fail_echo"]) != 1 or new_v.count(pins["c2_fail_echo"]) != 1:
    bad.append("the C1 or C2 fail echo is not exactly once")
if new_v.count(pins["c1_banner"]) != 1 or new_v.count(pins["c2_banner"]) != 1:
    bad.append("the C1 or C2 failure banner text is not exactly once")
for token in ("[C17]", "[C18]", "[C19]", "check_c17", "check_c18", "check_c19"):
    if token in new_v:
        bad.append("new check text present: " + token)
for start, end in pins["unchanged_regions"]:
    if between(new_v, start, end) != between(base_v, start, end):
        bad.append("forbidden region changed: " + start[:48])
shipped_fn = between(new_v, "build_shipped_md_set() {", "build_payload_md_set() {")
payload_fn = between(new_v, "build_payload_md_set() {", "# Shared frontmatter parser")
if shipped_fn != between(base_v, "build_shipped_md_set() {", "build_payload_md_set() {"):
    bad.append("build_shipped_md_set changed")
if payload_fn != between(base_v, "build_payload_md_set() {", "# Shared frontmatter parser"):
    bad.append("build_payload_md_set changed")
if "docs/nips" in shipped_fn or "docs/nips" in payload_fn:
    bad.append("a set builder mentions docs/nips")
c1 = new_v.split("  C1 ")[1].split("  C2 ")[0]
c2 = new_v.split("  C2 ")[1].split("  C3 ")[0]
if "docs/nips/" not in c1 or "docs/nips/" not in c2:
    bad.append("help C1 or C2 paragraph lost docs/nips/")
if new_v.count(pins["nip_append_line"]) != 1:
    bad.append("the NIP append line is not exactly once")

base_n = show(pins["nip2"])
new_n = open(pins["nip2"]).read()
expect_n = base_n.replace("version: 0.2.0\n", "version: 0.2.1\n", 1)
expect_n = expect_n.replace("status: accepted\n", "status: active\n", 1)
expect_n = expect_n.replace("change_log:\n", "change_log:\n" + pins["nip2_changelog_entry"], 1)
if base_n.count("version: 0.2.0\n") != 1 or base_n.count("status: accepted\n") != 1:
    bad.append("NIP-0002 anchors are not unique at base")
if new_n != expect_n:
    bad.append("NIP-0002 is not base plus the three frontmatter edits")
if new_n.count("status: active\n") != 1:
    bad.append("status: active is not exactly once in NIP-0002")
if new_n.split("---", 2)[2] != base_n.split("---", 2)[2]:
    bad.append("NIP-0002 body changed")
front = yaml.safe_load(new_n.split("---", 2)[1])
if front.get("status") != "active" or front.get("version") != "0.2.1":
    bad.append("NIP-0002 frontmatter status or version")
if front.get("authoritative_source") != pins["nip2"]:
    bad.append("NIP-0002 authoritative_source")

def frontmatter(text):
    return yaml.safe_load(text.split("---", 2)[1])

def body(text):
    return text.split("---", 2)[2]

old_r, new_r = show("tools/README.md"), open("tools/README.md").read()
old_fm, new_fm = frontmatter(old_r), frontmatter(new_r)
if (str(old_fm["version"]), str(new_fm["version"])) != ("0.15.0", "0.16.0"):
    bad.append("README version is not 0.15.0 -> 0.16.0")
head = new_fm["change_log"][0]
if head["version"] != "0.16.0" or head["summary"] != pins["readme_summary"] or str(head["date"]) != pins["readme_date"]:
    bad.append("README change_log head")
if new_fm["change_log"][1:] != old_fm["change_log"]:
    bad.append("older README change_log entries changed")
if {k: v for k, v in new_fm.items() if k not in ("version", "change_log")} != {k: v for k, v in old_fm.items() if k not in ("version", "change_log")}:
    bad.append("another README frontmatter key changed")
old_lines, new_lines = body(old_r).splitlines(), body(new_r).splitlines()
diffs = [(a, b) for a, b in zip(old_lines, new_lines) if a != b]
if len(old_lines) != len(new_lines) or diffs != [(pins["c1_row_old"], pins["c1_row_new"])]:
    bad.append("README body differs by more than the pinned C1 row")
c1_lines = [line for line in new_r.splitlines() if line.startswith("| C1 ")]
if c1_lines != [pins["c1_row_new"]] or "docs/nips/" not in pins["c1_row_new"]:
    bad.append("AT4 C1 row is not exactly the pinned line")
c2_old = [line for line in old_r.splitlines() if line.startswith("| C2 ")]
c2_new = [line for line in new_r.splitlines() if line.startswith("| C2 ")]
if c2_old != c2_new or len(c2_new) != 1:
    bad.append("C2 README row changed")

for path in pins["unchanged_files"]:
    if open(path).read() != show(path):
        bad.append("file that must stay byte-identical changed: " + path)
print("problems:", bad)
sys.exit(1 if bad else 0)
PY
