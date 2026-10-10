python3 - <<'PY'
import json, os, subprocess, sys
bad = []

def serial_guard():
    ancestors, pid = set(), os.getpid()
    while pid > 1:
        ancestors.add(pid)
        try:
            pid = int(open("/proc/%d/stat" % pid).read().rsplit(")", 1)[1].split()[1])
        except (OSError, ValueError, IndexError):
            break
    for name in filter(str.isdigit, os.listdir("/proc")):
        if int(name) in ancestors:
            continue
        try:
            argv = [part.decode() for part in open("/proc/%s/cmdline" % name, "rb").read().split(b"\0") if part]
            cwd = os.readlink("/proc/%s/cwd" % name)
        except OSError:
            continue
        if cwd == os.getcwd() and len(argv) > 1 and os.path.basename(argv[0]) in ("bash", "sh") and argv[1].endswith(("tools/fixtures_self_test.sh", "tools/validate.sh")):
            print("REFUSED (exit 4): process %s is already running %s in this tree" % (name, argv[1]))
            sys.exit(4)

serial_guard()
pins = json.load(open(".agent/contracts/107.json"))["design_notes"]["pinned_interface"]

def mutate(rel, old, new):
    return (
        "p = root / {rel!r}\n"
        "t = p.read_text()\n"
        "old = {old!r}\n"
        "new = {new!r}\n"
        "assert t.count(old) == 1, t.count(old)\n"
        "p.write_text(t.replace(old, new, 1))\n"
    ).format(rel=rel, old=old, new=new)

def append_suffix(rel, suffix):
    return (
        "p = root / {rel!r}\n"
        "t = p.read_text()\n"
        "suffix = {suffix!r}\n"
        "assert suffix not in t\n"
        "p.write_text(t + suffix)\n"
    ).format(rel=rel, suffix=suffix)

NIP1 = pins["nip1"]
NIP2 = pins["nip2"]
ablate_c1 = mutate("tools/validate.sh", pins["c1_fail_echo"], pins["c1_fail_ablation"])
ablate_c2 = mutate("tools/validate.sh", pins["c2_fail_echo"], pins["c2_fail_ablation"])
drop_join = mutate("tools/validate.sh", pins["nip_append_line"], "        :\n")
poison = append_suffix(NIP1, pins["poison_suffix"])
SR = [sys.executable, ".agent/evidence/phase-014-activation/gates/scratch_run.py"]
VAL = ["bash", "tools/validate.sh"]
CASES = [
    ("AT2 mutation: exact C1 schema banner and detail; C2 status banner also fires",
     ["--replace", NIP1, "status: active", "status: accepted"], 1,
     [r"^\[C1\] FAIL frontmatter-schema$", pins["c1_schema_detail"], r"^\[C2\] FAIL format$", pins["c2_status_detail"]],
     [r"^\[C1[7-9]\]"], VAL),
    ("silencing the C1 fail echo removes [C1] FAIL; the C2 status banner remains",
     ["--replace", NIP1, "status: active", "status: accepted", "--py-mutate", ablate_c1], 1,
     [r"^\[C2\] FAIL format$", pins["c2_status_detail"]],
     [r"^\[C1\] FAIL"], VAL),
    ("AT3 mutation: exact C2 format banner and authoritative_source detail; no C1 fail",
     ["--replace", NIP1, "authoritative_source: docs/nips/NIP-0001-ecosystem-engineering-cycle.md", "authoritative_source: docs/nips/NIP-0001-moved.md"], 1,
     [r"^\[C2\] FAIL format$", pins["c2_source_detail"], r"^\[C1\] PASS frontmatter-schema$"],
     [r"^\[C1\] FAIL"], VAL),
    ("silencing the C2 fail echo removes [C2] FAIL from the AT3 mutation; C1 stays passing",
     ["--replace", NIP1, "authoritative_source: docs/nips/NIP-0001-ecosystem-engineering-cycle.md", "authoritative_source: docs/nips/NIP-0001-moved.md", "--py-mutate", ablate_c2], 0,
     [r"^\[C1\] PASS frontmatter-schema$", r"^\[C2\] PASS format$", r"^SUMMARY: 16 passed, 0 failed$"],
     [r"^\[C1\] FAIL", r"^\[C2\] FAIL"], VAL),
    ("payload mode ignores a NIP status of accepted",
     ["--replace", NIP2, "status: active", "status: accepted"], 0,
     [r"^SUMMARY \(payload mode\): 12 passed, 0 failed$", r"^\[C1\] PASS frontmatter-schema$"],
     [r"^\[C1\] FAIL", r"^\[C2\] FAIL"], VAL + ["--payload"]),
    ("a bare fence and a missing path in a NIP body do not fail C3, C9, or C10",
     ["--py-mutate", poison], 0,
     [r"^SUMMARY: 16 passed, 0 failed$", r"^\[C1\] PASS frontmatter-schema$", r"^\[C3\] PASS untagged-fence-sweep$", r"^\[C9\] PASS path-resolution$", r"^\[C10\] PASS consistency$"],
     [r"^\[C3\] FAIL", r"^\[C9\] FAIL", r"^\[C10\] FAIL", "DOES-NOT-EXIST"], VAL),
    ("dropping the NIP append makes the AT2 mutation invisible to C1 and C2",
     ["--replace", NIP1, "status: active", "status: accepted", "--py-mutate", drop_join], 0,
     [r"^\[C1\] PASS frontmatter-schema$", r"^\[C2\] PASS format$", r"^SUMMARY: 16 passed, 0 failed$"],
     [r"^\[C1\] FAIL", r"^\[C2\] FAIL"], VAL),
]

def one(case):
    name, mutations, rc, expects, forbids, command = case
    argv = SR + mutations + ["--expect-rc", str(rc)]
    for pattern in expects:
        argv += ["--expect", pattern]
    for pattern in forbids:
        argv += ["--forbid", pattern]
    argv += ["--"] + command
    proc = subprocess.run(argv, capture_output=True, text=True)
    print(("PASS " if proc.returncode == 0 else "FAIL ") + name)
    if proc.returncode != 0:
        print("\n".join("    " + line for line in (proc.stdout + proc.stderr).splitlines()[-25:]))
        bad.append(name)

for case in CASES:
    one(case)
print("cases:", len(CASES), "problems:", bad)
sys.exit(1 if bad else 0)
PY
