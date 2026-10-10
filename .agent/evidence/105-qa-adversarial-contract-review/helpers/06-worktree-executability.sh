# Executability: the Orchestrator runs the Generator in a DETACHED WORKTREE (design_notes.attempt_isolation). Prove the AT/S commands that copy the tree
# (scratch_run.py, S05, S06) work when cwd is a linked worktree whose .git is a file. The worktree is created from a SCRATCH clone, never from the repository.
H=$PWD/.agent/evidence/105-qa-adversarial-contract-review/helpers
rm -rf /home/cnross/.tmp/claude-1000/-home-cnross-workspace02-nizam-framework/b87ce099-80d9-4a17-8331-ff678f08d08a/scratchpad/wt105; git -C /home/cnross/.tmp/claude-1000/-home-cnross-workspace02-nizam-framework/b87ce099-80d9-4a17-8331-ff678f08d08a/scratchpad/gen/att worktree prune
git -C /home/cnross/.tmp/claude-1000/-home-cnross-workspace02-nizam-framework/b87ce099-80d9-4a17-8331-ff678f08d08a/scratchpad/gen/att worktree add --detach /home/cnross/.tmp/claude-1000/-home-cnross-workspace02-nizam-framework/b87ce099-80d9-4a17-8331-ff678f08d08a/scratchpad/wt105 HEAD
echo ".git in worktree is a file: $(test -f /home/cnross/.tmp/claude-1000/-home-cnross-workspace02-nizam-framework/b87ce099-80d9-4a17-8331-ff678f08d08a/scratchpad/wt105/.git && echo yes || echo no)"
TAIL=2 python3 "$H/runall.py" /home/cnross/.tmp/claude-1000/-home-cnross-workspace02-nizam-framework/b87ce099-80d9-4a17-8331-ff678f08d08a/scratchpad/wt105 AT1 AT2 AT3 AT4 AT5 S01 S02 S03 S04 S05 S06 S07 S08 S09
