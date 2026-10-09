#!/usr/bin/env python3
"""mutate.py IMPLTREE WORKDIR [ID...] : single-point mutants of the contract-faithful implementation (positive control tree).
Each mutant = a fresh cp -a copy of IMPLTREE with ONE defect; the contract's pre-commit checks run in it; the output lists which check(s) catch it.
Order (stop at first catch for the expensive ones): fast {AT4 S01 S03 S04 S07 S08} always; for script/tree mutants AT1 first; if nothing caught: AT2 AT3 S05 S06 AT5 S09.
Mutants run 4 at a time, each in its own tree (checks inside one tree are strictly sequential: C13 race)."""
import os, pathlib, re, shutil, subprocess, sys, time, concurrent.futures
H = pathlib.Path(__file__).resolve().parent / 'cmds'
impl, work = sys.argv[1], pathlib.Path(sys.argv[2]); only = sys.argv[3:]
FAST = ['AT4', 'S01', 'S03', 'S04', 'S07', 'S08']
SCRIPT = 'tools/fixtures_self_test.sh'; README = 'tools/README.md'; CL = 'CHANGELOG.md'; PY = 'docs/planning/phase_014.yaml'

def rd(t, p): return (pathlib.Path(t) / p).read_text()
def wr(t, p, s): (pathlib.Path(t) / p).write_text(s)
def sub(t, p, old, new, count=1, nth=None):
    s = rd(t, p); assert s.count(old) >= 1, (p, old)
    if nth == 'last':
        i = s.rindex(old); s = s[:i] + new + s[i + len(old):]
    else:
        s = s.replace(old, new, count)
    wr(t, p, s)
def line_sub(t, p, fragment, new_line):
    """replace the single line containing fragment"""
    s = rd(t, p).split('\n'); hits = [i for i, l in enumerate(s) if fragment in l]; assert len(hits) == 1, (fragment, hits)
    s[hits[0]] = new_line; wr(t, p, '\n'.join(s))
def mk(t, rel, text='{}'):
    p = pathlib.Path(t) / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(text)

M = []   # (id, kind, description, function)   kind: S script/tree (AT1 first), D doc (fast + S09)
def mut(i, kind, d):
    def deco(f): M.append((i, kind, d, f)); return f
    return deco
ROW = '  "convergent_review|tools/test_convergent_review.py"'

# ---- A. claim map present but not consulted
mut('a01', 'S', 'real guard no longer calls claim_map_check (map not consulted for claim violations)')(lambda t: sub(t, SCRIPT, 'claim_out=$(claim_map_check tools/fixtures "${REPO}" "${FIXTURE_CLAIMS[@]}") || {', 'claim_out=$(true) || {'))
mut('a02', 'S', 'real guard calls claim_map_check but never sets fail=1 on its result')(lambda t: sub(t, SCRIPT, '  printf \'%s\\n\' "${claim_out}"\n  fail=1\n}', '  printf \'%s\\n\' "${claim_out}"\n}'))
mut('a03', 'S', 'real guard calls claim_map_check but swallows its output (fail=1 only)')(lambda t: sub(t, SCRIPT, '  printf \'%s\\n\' "${claim_out}"\n  fail=1\n}', '  fail=1\n}'))
mut('a04', 'S', 'map not consulted at all: no call AND claimed_dir hard-coded to convergent_review')(lambda t: (sub(t, SCRIPT, 'claim_out=$(claim_map_check tools/fixtures "${REPO}" "${FIXTURE_CLAIMS[@]}") || {', 'claim_out=$(true) || {'), sub(t, SCRIPT, 'for _row in "${FIXTURE_CLAIMS[@]}"; do claimed_dir["${_row%%|*}"]=1; done', 'claimed_dir[convergent_review]=1')))
mut('a05', 'S', 'claimed_dir built from the nested subdirectories on disk (every subdir counts as claimed), call kept')(lambda t: sub(t, SCRIPT, 'for _row in "${FIXTURE_CLAIMS[@]}"; do claimed_dir["${_row%%|*}"]=1; done', 'for _f in "${ondisk[@]}"; do case "${_f}" in */*) claimed_dir["${_f%%/*}"]=1 ;; esac; done'))
mut('a06', 'S', 'claim_map_check called with no rows (the real array is ignored)')(lambda t: sub(t, SCRIPT, 'claim_out=$(claim_map_check tools/fixtures "${REPO}" "${FIXTURE_CLAIMS[@]}")', 'claim_out=$(claim_map_check tools/fixtures "${REPO}")'))
mut('a07', 'S', 'claim_map_check body is a stub returning 0 (map exists, demonstrations and guard see no violations)')(lambda t: sub(t, SCRIPT, 'claim_map_check() {\n', 'claim_map_check() {\n  return 0\n'))
mut('a08', 'S', 'accounting ignores the claim: every nested file counted as claimed')(lambda t: sub(t, SCRIPT, '*/*) if [ -n "${claimed_dir["${f%%/*}"]:-}" ]; then nested_claimed=$((nested_claimed + 1)); else nested_unclaimed+=("${f}"); fi ;;', '*/*) nested_claimed=$((nested_claimed + 1)) ;;'))

# ---- B. subdirectory-level detections (one at a time), plus variants
DET = {'unclaimed': 'unclaimed subdirectory: ', 'doubly': 'doubly-claimed subdirectory: ', 'missing': 'names a suite file that does not exist: ', 'absent': 'names a subdirectory that is not on disk: '}
def ablate(t, frag):
    s = rd(t, SCRIPT); a = s.index('claim_map_check() {\n'); b = s.index('\n}\n', a)
    lines = s[a:b].split('\n'); hits = [i for i, l in enumerate(lines) if frag in l]; assert len(hits) == 1, hits
    lines[hits[0]] = ':'; wr(t, SCRIPT, s[:a] + '\n'.join(lines) + s[b:])
for k, frag in DET.items():
    mut('b-' + k, 'S', 'claim_map_check: the %s detection removed' % k)(lambda t, frag=frag: ablate(t, frag))
mut('b05', 'S', 'doubly-claimed threshold -le 1 -> -le 2 (two rows tolerated)')(lambda t: sub(t, SCRIPT, '-le 1 ]', '-le 2 ]'))
mut('b06', 'S', 'doubly-claimed: duplicates deduplicated before counting (claim_count set to 1)')(lambda t: sub(t, SCRIPT, 'claim_count["${key}"]=$(( ${claim_count["${key}"]:-0} + 1 ))', 'claim_count["${key}"]=1'))
mut('b07', 'S', 'malformed-row detection removed (row without | accepted)')(lambda t: line_sub(t, SCRIPT, 'malformed claim row: ${row}', '      :'))
mut('b08', 'S', 'suite existence test -f -> -e (a directory counts as a suite)')(lambda t: sub(t, SCRIPT, '[ -f "${repo_root}/${suite}" ]', '[ -e "${repo_root}/${suite}" ]'))
mut('b09', 'S', 'suite existence resolved against the fixtures root instead of the repo root')(lambda t: sub(t, SCRIPT, '[ -f "${repo_root}/${suite}" ]', '[ -f "${fixtures_root}/${suite}" ] || [ "${suite}" = "tools/test_convergent_review.py" ]'))
mut('b10', 'S', 'unclaimed-subdirectory enumeration: prefix match (convergent_review_x/ covered by the convergent_review claim)')(lambda t: sub(t, SCRIPT, '[ -n "${claim_count["${entry}"]:-}" ] ||', '[ -n "${claim_count["${entry}"]:-}" ] || [[ "${entry}" == convergent_review* ]] ||'))
mut('b11', 'S', 'subdirectory enumeration lists only subdirectories that contain files (empty unclaimed dir invisible)')(lambda t: sub(t, SCRIPT, "find . -mindepth 1 -maxdepth 1 -type d | sed 's#^\\./##'", "find . -mindepth 2 -type f | sed 's#^\\./##; s#/.*##' | sort -u"))
mut('b12', 'S', 'subdirectory enumeration is recursive (every nested case directory must be claimed): false-fail control')(lambda t: sub(t, SCRIPT, 'find . -mindepth 1 -maxdepth 1 -type d', 'find . -mindepth 1 -type d'))
mut('b13', 'S', 'subdirectory enumeration finds nothing (find limited to maxdepth 0)')(lambda t: sub(t, SCRIPT, 'find . -mindepth 1 -maxdepth 1 -type d', 'find . -mindepth 1 -maxdepth 0 -type d'))

# ---- C. depth-limited on-disk enumeration
for n in (1, 2, 3, 5, 6, 8):
    mut('c%d' % n, 'S', 'on-disk enumeration limited to -maxdepth %d (path components)' % n)(lambda t, n=n: sub(t, SCRIPT, 'find . -mindepth 1 ! -type d', 'find . -mindepth 1 -maxdepth %d ! -type d' % n))
mut('c10', 'S', 'on-disk enumeration uses the OLD form: find . -maxdepth 1 -type f')(lambda t: sub(t, SCRIPT, 'find . -mindepth 1 ! -type d', 'find . -maxdepth 1 -type f'))
mut('c11', 'S', 'on-disk enumeration skips dot-files')(lambda t: sub(t, SCRIPT, 'find . -mindepth 1 ! -type d', "find . -mindepth 1 ! -type d ! -name '.*'"))
mut('c12', 'S', 'on-disk enumeration -type f (symlinks not counted)')(lambda t: sub(t, SCRIPT, 'find . -mindepth 1 ! -type d', 'find . -mindepth 1 -type f'))
mut('c13', 'S', 'accounted := total (count cosmetic: accounted always equals total)')(lambda t: sub(t, SCRIPT, 'accounted=$(( ${#toplevel[@]} - $(printf \'%s\\n\' "${unaccounted}" | grep -c .) + nested_claimed ))', 'accounted=${total}'))
mut('c14', 'S', 'total hard-coded to 146')(lambda t: sub(t, SCRIPT, 'total=${#ondisk[@]}', 'total=146'))
mut('c15', 'S', 'unlisted top-level fixture check removed (unaccounted never reported)')(lambda t: sub(t, SCRIPT, 'if [ -n "${unaccounted}" ]; then', 'if false; then'))
mut('c16', 'S', 'phantom COVERED row check removed')(lambda t: sub(t, SCRIPT, 'if [ -n "${phantom}" ]; then', 'if false; then'))
mut('c17', 'S', 'files below an unclaimed subdirectory not reported / not failing (nested_unclaimed branch off)')(lambda t: sub(t, SCRIPT, 'if [ "${#nested_unclaimed[@]}" -gt 0 ]; then', 'if false; then'))

# ---- D. demonstrations: OK lines printed without the cases actually failing
mut('d01', 'S', '_claim_map_case stub: returns 0 immediately after the scratch is built (OK lines printed without testing)')(lambda t: sub(t, SCRIPT, '  local -a rows=("owned|suites/a.py")\n  scratch_dirs d || return 1\n', '  local -a rows=("owned|suites/a.py")\n  scratch_dirs d || return 1\n  return 0\n'))
mut('d02', 'S', '_claim_map_case stub: returns 0 as its first statement')(lambda t: sub(t, SCRIPT, '_claim_map_case() (\n', '_claim_map_case() (\n  return 0\n'))
mut('d03', 'S', 'loop: if _claim_map_case ... || true (OK printed regardless)')(lambda t: sub(t, SCRIPT, 'if _claim_map_case "${_case%%|*}"; then', 'if _claim_map_case "${_case%%|*}" || true; then'))
mut('d04', 'S', 'loop: failing case branch removed (never sets fail=1)')(lambda t: sub(t, SCRIPT, '    fail=1\n  fi\ndone\n\n# ---------------------------------------------------------------------------\n# COMPLETENESS GUARD', '  fi\ndone\n\n# ---------------------------------------------------------------------------\n# COMPLETENESS GUARD'))
mut('d05', 'S', 'the four OK lines emitted as literal echoes, _claim_map_case never invoked')(lambda t: sub(t, SCRIPT, 'for _case in "unclaimed|unclaimed subdirectory" "doubly|doubly-claimed subdirectory" \\\n             "missing-suite|claim naming a missing suite" "absent-subdir|claim naming an absent subdirectory"; do\n  if _claim_map_case "${_case%%|*}"; then\n    echo "OK   claim-map   ${_case#*|} -> FAIL"\n  else\n    echo "FAIL claim-map   ${_case#*|}: the guard did not behave as claimed"\n    fail=1\n  fi\ndone', 'echo "OK   claim-map   unclaimed subdirectory -> FAIL"\necho "OK   claim-map   doubly-claimed subdirectory -> FAIL"\necho "OK   claim-map   claim naming a missing suite -> FAIL"\necho "OK   claim-map   claim naming an absent subdirectory -> FAIL"'))
mut('d06', 'S', 'positive control removed from _claim_map_case')(lambda t: sub(t, SCRIPT, '  [ "${rc}" -eq 0 ] && [ -z "${out}" ] || { echo "  control: a complete claim map must pass (rc=${rc}): ${out}"; return 1; }\n', ''))
mut('d07', 'S', 'negative assertion: exactly-one-line test removed')(lambda t: sub(t, SCRIPT, ' && [ "$(printf \'%s\\n\' "${out}" | wc -l)" -eq 1 ]', ''))
mut('d08', 'S', 'negative assertion: defect-name test removed')(lambda t: sub(t, SCRIPT, ' && [[ "${out}" == *"${want}"* ]]', ''))
mut('d09', 'S', 'negative assertion: rc test -eq 1 weakened to -ne 99')(lambda t: sub(t, SCRIPT, '[ "${rc}" -eq 1 ] &&', '[ "${rc}" -ne 99 ] &&'))
mut('d10', 'S', 'negative assertion evaluated on the POSITIVE rows (the row-level defect is not what the second check sees)')(lambda t: sub(t, SCRIPT, '  out=$(claim_map_check "${d}/fixtures" "${d}" "${rows[@]}"); rc=$?\n  [ "${rc}" -eq 1 ]', '  out=$(claim_map_check "${d}/fixtures" "${d}" "owned|suites/a.py"); rc=$?\n  [ "${rc}" -eq 1 ]'))
mut('d11', 'S', 'fourth demonstration dropped from the loop (three OK lines only)')(lambda t: sub(t, SCRIPT, ' \\\n             "missing-suite|claim naming a missing suite" "absent-subdir|claim naming an absent subdirectory"; do', ' \\\n             "missing-suite|claim naming a missing suite"; do'))
mut('d12', 'S', 'OK label of the second demonstration swapped with the third (label bound to the wrong mode)')(lambda t: sub(t, SCRIPT, '"doubly|doubly-claimed subdirectory" \\\n             "missing-suite|claim naming a missing suite"', '"doubly|claim naming a missing suite" \\\n             "missing-suite|doubly-claimed subdirectory"'))
mut('d13', 'S', 'the demonstration case "doubly" really tests the unclaimed mode (case body swapped)')(lambda t: sub(t, SCRIPT, '    doubly)        rows+=("owned|suites/b.py"); want="doubly-claimed subdirectory: owned" ;;', '    doubly)        mkdir "${d}/fixtures/zz_unclaimed"; want="unclaimed subdirectory: zz_unclaimed" ;;'))

# ---- E. containment: the negative-case harness writes inside tools/fixtures/
mut('e01', 'S', 'leak: demonstration scratch root := ${REPO}/tools/fixtures/zz_trip (S06 own mutant)')(lambda t: sub(t, SCRIPT, '  scratch_dirs d || return 1\n  mkdir -p "${d}/fixtures/owned"', '  d="${REPO}/tools/fixtures/zz_trip"; mkdir -p "${d}" || return 1\n  mkdir -p "${d}/fixtures/owned"'))
mut('e02', 'S', 'leak: extra write into the real tree inside _claim_map_case, no cleanup (relative path)')(lambda t: sub(t, SCRIPT, '  local -a rows=("owned|suites/a.py")\n  scratch_dirs d || return 1\n', '  local -a rows=("owned|suites/a.py")\n  scratch_dirs d || return 1\n  mkdir -p tools/fixtures/zz_leak\n'))
mut('e03', 'S', 'leak: write into the real tree inside _claim_map_case, cleaned up afterwards (relative path)')(lambda t: sub(t, SCRIPT, '  local -a rows=("owned|suites/a.py")\n  scratch_dirs d || return 1\n', '  local -a rows=("owned|suites/a.py")\n  scratch_dirs d || return 1\n  mkdir -p tools/fixtures/zz_leak && rmdir tools/fixtures/zz_leak\n'))
mut('e04', 'S', 'leak: obfuscated path write (no literal tools/fixtures, no REPO) inside _claim_map_case, cleaned up')(lambda t: sub(t, SCRIPT, '  local -a rows=("owned|suites/a.py")\n  scratch_dirs d || return 1\n', '  local -a rows=("owned|suites/a.py")\n  scratch_dirs d || return 1\n  f=fixtures; mkdir -p "${PWD}/tools/${f}/zz_leak" && rmdir "${PWD}/tools/${f}/zz_leak"\n'))
mut('e05', 'S', 'leak: write into the real tree in the demonstration loop (outside the function), no cleanup')(lambda t: sub(t, SCRIPT, 'echo "== claim map demonstrations (guarded scratch area) =="\n', 'echo "== claim map demonstrations (guarded scratch area) =="\n: > tools/fixtures/zz_loop_trace\n'))
mut('e06', 'S', 'leak: write into the real tree in the demonstration loop (outside the function), cleaned up')(lambda t: sub(t, SCRIPT, 'echo "== claim map demonstrations (guarded scratch area) =="\n', 'echo "== claim map demonstrations (guarded scratch area) =="\n: > tools/fixtures/zz_loop_trace; rm -f tools/fixtures/zz_loop_trace\n'))
mut('e07', 'S', 'leak: _claim_map_case is a plain function (not a subshell) so the scratch trap replaces the global one')(lambda t: (sub(t, SCRIPT, '_claim_map_case() (\n', '_claim_map_case() {\n'), sub(t, SCRIPT, '    || { echo "  ${case_name}: rc=${rc}: ${out}"; return 1; }\n)\n', '    || { echo "  ${case_name}: rc=${rc}: ${out}"; return 1; }\n}\n')))
mut('e08', 'S', 'leak: claim_map_check writes (touch) into the fixtures root it inspects')(lambda t: sub(t, SCRIPT, '  return "${bad}"\n}', '  touch "${fixtures_root}/.probe"; rm -f "${fixtures_root}/.probe"\n  return "${bad}"\n}'))
mut('e09', 'S', 'scratch root = repo-relative ./zz_scratch (scratch_dirs bypassed) inside the case, in the repository root')(lambda t: sub(t, SCRIPT, '  local -a rows=("owned|suites/a.py")\n  scratch_dirs d || return 1\n', '  local -a rows=("owned|suites/a.py")\n  d="./zz_scratch_$$"; mkdir -p "${d}" || return 1\n'))

# ---- F. state mutants of the tree (the real guard must FAIL these; the mutants are the broken states)
def mkdirs(t, rel): (pathlib.Path(t) / rel).mkdir(parents=True, exist_ok=True)
mut('t01', 'S', 'state: unclaimed subdirectory tools/fixtures/zz_new/ with one file')(lambda t: mk(t, 'tools/fixtures/zz_new/a.json'))
mut('t02', 'S', 'state: EMPTY unclaimed subdirectory tools/fixtures/zz_empty/')(lambda t: mkdirs(t, 'tools/fixtures/zz_empty'))
mut('t03', 'S', 'state: unclaimed subdirectory whose only file is 6 components deep')(lambda t: mk(t, 'tools/fixtures/zz_deep/a/b/c/d/x.json'))
mut('t04', 'S', 'state: doubly-claimed row (both suites exist)')(lambda t: sub(t, SCRIPT, ROW, ROW + '\n  "convergent_review|tools/validate.sh"'))
mut('t05', 'S', 'state: claim naming a nonexistent suite')(lambda t: sub(t, SCRIPT, ROW, '  "convergent_review|tools/no_such_suite.py"'))
mut('t06', 'S', 'state: extra claim naming an absent subdirectory')(lambda t: sub(t, SCRIPT, ROW, ROW + '\n  "zz_ghost|tools/validate.sh"'))
mut('t07', 'S', 'state: the real claim row deleted')(lambda t: sub(t, SCRIPT, ROW + '\n', ''))
mut('t08', 'S', 'state: claim key mistyped (convergent_reviw)')(lambda t: sub(t, SCRIPT, '"convergent_review|', '"convergent_reviw|'))
mut('t09', 'S', 'state: owning suite file deleted')(lambda t: os.remove(pathlib.Path(t) / 'tools/test_convergent_review.py'))
mut('t10', 'S', 'state: fixture moved - a nested file moved up one level inside the claimed subdirectory')(lambda t: shutil.move(str(pathlib.Path(t) / 'tools/fixtures/convergent_review/01-no-findings/' ) + '/' + sorted(os.listdir(pathlib.Path(t) / 'tools/fixtures/convergent_review/01-no-findings'))[0], str(pathlib.Path(t) / 'tools/fixtures/convergent_review/moved_file')))
def t11(t):
    top = sorted(f for f in os.listdir(pathlib.Path(t) / 'tools/fixtures') if (pathlib.Path(t) / 'tools/fixtures' / f).is_file())[0]
    shutil.move(str(pathlib.Path(t) / 'tools/fixtures' / top), str(pathlib.Path(t) / 'tools/fixtures/convergent_review' / top))
mut('t11', 'S', 'state: fixture moved - a top-level fixture moved into the claimed subdirectory')(t11)
def t12(t):
    top = sorted(f for f in os.listdir(pathlib.Path(t) / 'tools/fixtures') if (pathlib.Path(t) / 'tools/fixtures' / f).is_file())[0]
    mkdirs(t, 'tools/fixtures/zz_moved'); shutil.move(str(pathlib.Path(t) / 'tools/fixtures' / top), str(pathlib.Path(t) / 'tools/fixtures/zz_moved' / top))
mut('t12', 'S', 'state: fixture moved - a top-level fixture moved into a new unclaimed subdirectory')(t12)
mut('t13', 'S', 'state: unlisted top-level fixture added')(lambda t: mk(t, 'tools/fixtures/zz_top.json'))
mut('t14', 'S', 'state: dotfile 6 components deep inside the claimed subdirectory (guard must count it, pass 147/147)')(lambda t: mk(t, 'tools/fixtures/convergent_review/01-no-findings/d1/d2/d3/.deep.json'))

# ---- G. docs and versions unsynced
FS = '### Fixture self-test'
mut('g01', 'D', 'README version not bumped (0.13.0 kept)')(lambda t: sub(t, README, 'version: 0.14.0\n', 'version: 0.13.0\n'))
mut('g02', 'D', 'README head change_log entry missing')(lambda t: sub(t, README, '  - version: "0.14.0"\n    date: "2026-10-09"\n    summary: "Describe the fixtures self-test claim map', '  - version: "0.13.0"\n    date: "2026-10-09"\n    summary: "Describe the fixtures self-test claim map'))
mut('g03', 'D', 'README head change_log summary altered (one word)')(lambda t: sub(t, README, 'is claimed by exactly one owning suite, the completeness guard accounts', 'is claimed by at most one owning suite, the completeness guard accounts'))
def g04(t):
    s = rd(t, README); i = s.index('The completeness guard also consults a **claim map**'); wr(t, README, s[:i].rstrip('\n') + '\n')
mut('g04', 'D', 'README paragraph removed')(g04)
mut('g05', 'D', 'README paragraph says "three" cases (code has four)')(lambda t: sub(t, README, 'The guard fails on an unclaimed subdirectory, on a doubly-claimed subdirectory, on a claim naming a suite file that does not exist, and on a claim naming a subdirectory that is not on disk.', 'The guard fails on an unclaimed subdirectory, on a doubly-claimed subdirectory and on a claim naming a suite file that does not exist.'))
mut('g06', 'D', 'README wording "claim map" -> "claim table" everywhere in the paragraph')(lambda t: wr(t, README, rd(t, README).replace('**claim map**', '**claim table**').replace('claim map', 'claim table')))
def g07(t):
    s = rd(t, README); i = s.index('The completeness guard also consults a **claim map**'); para = s[i:].rstrip('\n'); s = s[:i].rstrip('\n') + '\n'
    j = s.index(FS); k = s.index('\n', j)
    wr(t, README, s[:k + 1] + '\n' + para + '\n' + s[k + 1:])
mut('g07', 'D', 'README paragraph moved to the top of the Fixture self-test section (not last paragraph)')(g07)
mut('g08', 'D', 'README paragraph cites a nonexistent backticked path (C9)')(lambda t: sub(t, README, '(`tools/test_convergent_review.py` owns', '(`tools/test_convergent_reviewx.py` owns'))
mut('g09', 'D', 'README completeness-guard sentence edited')(lambda t: sub(t, README, 'A\n**completeness guard** fails if any file under', 'A\n**completeness guard** fails if any top-level file under'))
mut('g10', 'D', 'CHANGELOG bullet missing')(lambda t: sub(t, CL, '- **Phase 014 feature 105: Nested-fixture ownership**', '- **Phase 014 feature 105: Nested fixture ownership**'))
def g11(t):
    s = rd(t, CL); i = s.index('- **Phase 014 feature 105'); j = s.index('\n\n## [1.4.0]'); b = s[i:j]; s = s[:i].rstrip('\n') + s[j:]
    k = s.index('\n- **Phase 014 feature 104'); wr(t, CL, s[:k + 1] + b + '\n' + s[k + 1:])
mut('g11', 'D', 'CHANGELOG bullet placed before the feature-104 bullet')(g11)
mut('g12', 'D', 'CHANGELOG bullet says "three" cases')(lambda t: sub(t, CL, 'a claim naming a suite file that does not exist and a claim naming an absent subdirectory', 'and a claim naming a suite file that does not exist'))
mut('g13', 'D', 'phase yaml: changelog_entry missing')(lambda t: line_sub(t, PY, '    changelog_entry: "Fixtures self-test claim map', ''))
mut('g14', 'D', 'phase yaml: step 105 BLOCKED')(lambda t: sub(t, PY, 'NDEBT-042).\n    status: PENDING\n    docs_updated', 'NDEBT-042).\n    status: BLOCKED\n    docs_updated'))
mut('g15', 'D', 'phase yaml: evidence path wrong')(lambda t: sub(t, PY, '.agent/evidence/105/at1-completeness-any-depth.txt', '.agent/evidence/105/at1.txt'))
mut('g16', 'D', 'phase yaml: docs_updated names the wrong doc')(lambda t: sub(t, PY, 'docs_updated: tools/README.md', 'docs_updated: CHANGELOG.md'))
mut('g17', 'D', 'extra stray file: tools/FIXTURE_CLAIMS.md (second registry)')(lambda t: mk(t, 'tools/FIXTURE_CLAIMS.md', 'FIXTURE_CLAIMS second registry\n'))
mut('g18', 'D', 'out-of-scope edit: tools/validate.sh touched')(lambda t: sub(t, 'tools/validate.sh', '#!/usr/bin/env bash', '#!/usr/bin/env bash\n# stray', count=1))
mut('g19', 'D', 'prefix invariance broken: a pre-separator probe comment edited')(lambda t: sub(t, SCRIPT, 'Fixture dormancy self-test', 'Fixture dormancy self-test!', count=1))
mut('g20', 'D', 'runtime_session row registered (claim naming an absent subdirectory) instead of the comment')(lambda t: sub(t, SCRIPT, ROW, ROW + '\n  "runtime_session|tools/test_runtime_session.py"'))
mut('g21', 'D', 'runtime_session directory created')(lambda t: mk(t, 'tools/fixtures/runtime_session/stub_runtime.py', ''))

def run_one(entry):
    i, kind, desc, f = entry
    d = work / i
    shutil.rmtree(d, ignore_errors=True); shutil.copytree(impl, d, symlinks=True)
    f(str(d)); t0 = time.time(); res = {}
    if os.environ.get('DRY'):
        shutil.rmtree(d, ignore_errors=True); return i, kind, desc, ['DRY-APPLIED'], '0s'
    def go(n):
        p = subprocess.run(['bash', str(H / (n + '.sh'))], cwd=d, capture_output=True, text=True); res[n] = p.returncode; return p.returncode
    first = []
    if kind == 'S':
        order = ['AT1'] + FAST
    else:
        order = FAST
    for n in order: go(n)
    caught = [n for n, r in res.items() if r != 0]
    if not caught:
        extra = (['AT2', 'AT3', 'S05', 'S06', 'AT5', 'S09'] if kind == 'S' else ['AT5', 'S09'])
        for n in extra:
            if go(n) != 0: break
    else:
        # also run AT2/AT3 for script mutants to record the extra catchers cheaply only if AT1 was the sole catcher? skip: keep time bounded
        pass
    caught = [n for n, r in res.items() if r != 0]
    shutil.rmtree(d, ignore_errors=True)
    return i, kind, desc, caught, '%.0fs' % (time.time() - t0)

work.mkdir(parents=True, exist_ok=True)
sel = [m for m in M if not only or m[0] in only or any(m[0].startswith(o) for o in only)]
with concurrent.futures.ThreadPoolExecutor(max_workers=int(os.environ.get('JOBS', '4'))) as ex:
    for i, kind, desc, caught, dt in ex.map(run_one, sel):
        print('%-7s %s %-70s %s %s' % (i, 'CAUGHT  ' if caught else 'SURVIVED', desc[:120], ','.join(caught) or '-', dt)); sys.stdout.flush()
