#!/usr/bin/env bash
# Handover 2026-10 housekeeping inventory (read-only; deletes nothing).
# Run from the repository root: bash .agent/evidence/handover-2026-10/branch_inventory.sh
# Lists every local and origin branch with its head, the PR(s) whose head is that branch
# (via gh), and its commit count ahead of main; then the worktrees (home directory shown
# as ~) and any untracked files inside each non-main worktree.
set -euo pipefail
# Uses the remote-tracking refs as last fetched (no fetch, so the script stays read-only).
# One gh call (head branch -> PR numbers/states), so a flaky network fails once, not per branch.
pr_map="$(gh pr list --state all --limit 200 --json number,state,headRefName \
          -q '.[]|"\(.headRefName)\t#\(.number) \(.state)"')"
echo "== branches (ref | head | PR | ahead-of-main)"
git for-each-ref --format='%(refname:short)' refs/heads refs/remotes/origin \
  | grep -v -E '^origin$|^origin/HEAD$' | while read -r ref; do
  name="${ref#origin/}"
  prs="$(printf '%s\n' "${pr_map}" | awk -F'\t' -v b="${name}" '$1==b{print $2}' | paste -sd, -)"
  echo "${ref} | $(git log -1 --format='%h %cs' "${ref}") | PR: ${prs:-none} | ahead-of-main: $(git rev-list --count "main..${ref}")"
done
# mask: home directory -> ~ ; per-session temporary directories -> <session-scratch>
mask() { sed -E -e "s#${HOME}#~#g" -e 's#~/\.tmp/[^ ]*/(wt-[^ /]*)#~/.tmp/<session-scratch>/\1#g'; }
echo "== worktrees"
git worktree list | mask
echo "== untracked/modified files per extra worktree"
git worktree list --porcelain | awk '/^worktree /{print $2}' | tail -n +2 | while read -r wt; do
  echo "-- ${wt}" | mask
  git -C "${wt}" status --porcelain --untracked-files=normal
done
echo "== attempt worktrees left (nizam-wt-*)"
git worktree list | grep -c 'nizam-wt-' || true
