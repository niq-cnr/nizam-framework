# Can the Orchestrator perform the CI choreography exactly as written? READ-ONLY gh/git probes against the real remote (no write, no push, no PR, no rerun).
set -u
SC="$NIZAM_EVAL_SCRATCH"
echo "== (1) gh run view <id> --json headSha,headBranch,conclusion,jobs : shape, stderr empty, compact one-line JSON when piped (run 37967901131 = the 103 feature PR's pull_request run)"
gh run view 37967901131 --json headSha,headBranch,conclusion,jobs > "$SC/e1.json" 2> "$SC/e1.err"; echo "rc=$? stderr_bytes=$(wc -c < "$SC/e1.err") lines=$(wc -l < "$SC/e1.json")"
python3 -I -c "
import json; d=json.load(open('$SC/e1.json')); print('keys', sorted(d), '| headBranch', d['headBranch'], '| conclusion', d['conclusion']); print('job keys', sorted(d['jobs'][0])); print('jobs', [(j['name'], j['databaseId'], j['conclusion']) for j in d['jobs']])
print('job name == workflow key for a job with no name: (validate/e2e_bootstrap/fixtures_self_test) ->', sorted(j['name'] for j in d['jobs']))"
echo "== (2) gh run view --job <databaseId> --log (no run id): works, stderr empty, DETERMINISTIC across two fetches (S10's no-normalization premise), no 'skipped'/'UNSUPPORTED' in the three existing jobs' logs"
for i in 1 2; do gh run view --job 113955339005 --log > "$SC/l$i.out" 2> "$SC/l$i.err"; echo "fetch $i rc=$? stderr_bytes=$(wc -c < "$SC/l$i.err") lines=$(wc -l < "$SC/l$i.out")"; done
cmp "$SC/l1.out" "$SC/l2.out" && echo "two log fetches byte-identical"
for id in 113955338795 113955339001 113955339005; do echo "job $id: skipped/UNSUPPORTED matches = $(gh run view --job $id --log 2>/dev/null | grep -c -i -E 'skipped|UNSUPPORTED')"; done
echo "== (3) completed FAILED/CANCELLED pull_request runs exist and have the same JSON shape (conclusion failure / cancelled)"
gh run list --status failure --event pull_request --limit 1 --json databaseId,headBranch,conclusion,event
gh run list --status cancelled --event pull_request --limit 1 --json databaseId,headBranch,conclusion,event
echo "== (4) gh pr view <n> --json state,mergedAt,headRefName,baseRefName on a CLOSED-unmerged PR (#21): mergedAt is JSON null, so S11's s.get('mergedAt') is falsy"
gh pr view 21 --json state,mergedAt,headRefName,baseRefName 2> "$SC/e4.err"; echo "rc=$? stderr_bytes=$(wc -c < "$SC/e4.err")"
echo "== (5) refs/pull/<n>/head survives for a closed unmerged PR (S11's fallback fetch) and is fetchable into a FRESH repo"
git ls-remote origin refs/pull/21/head
T=$(mktemp -d -p "$SC"); git init -q "$T/f"; git -C "$T/f" fetch -q --depth 1 https://github.com/niq-cnr/nizam-framework.git refs/pull/21/head; echo "fetch rc=$? type=$(git -C "$T/f" cat-file -t FETCH_HEAD)"
echo "== (6) git ls-remote --heads origin <absent branch>: rc 0 and EMPTY output (the ci-negative-branch-absent.txt shape)"
git ls-remote --heads origin throwaway/104-isolation-removal; echo "rc=$?"
echo "== (7) preconditions: no remote phase/014-104* or throwaway/* branch, no PR for the feature branch, attempt/throwaway worktree paths free"
git ls-remote --heads origin 'phase/014-104*' 'throwaway/*'; echo "ls-remote rc=$?"
echo "PRs for head phase/014-104-sandbox-ci: $(gh pr list --state all --head phase/014-104-sandbox-ci --json number | tr -d '\n')"
for p in /home/cnross/workspace02/nizam-wt-104-attempt1 /home/cnross/workspace02/nizam-wt-104-attempt2 /home/cnross/workspace02/nizam-wt-104-attempt3 /home/cnross/workspace02/nizam-wt-104-throwaway; do test -e "$p" && echo "EXISTS $p" || echo "free   $p"; done
echo "== (8) compliance.yml triggers: pull_request (all types incl. draft) + push to main; concurrency group is per ref so the feature PR and the throwaway PR do not cancel each other"
sed -n 1,15p .github/workflows/compliance.yml
echo "== (9) the contract's two mutation_replacements each occur exactly once in the sources at <A>"
grep -c 'exec unshare --user --map-root-user --net --ipc --uts --pid --fork --mount-proc' tools/linux_trial_sandbox.sh
grep -c 'syscall(SYS_LANDLOCK_RESTRICT_SELF, ruleset_fd, 0)' tools/isolated_trial_adapter.py
echo "== (10) host: AppArmor key unchanged (this workstation is restricted, so no capable-host branch can be exercised locally)"
cat /proc/sys/kernel/apparmor_restrict_unprivileged_userns
