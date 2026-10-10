# Positive control (b): faithful Generator-attempt simulation (B = approved-contract commit, attempt-base.txt first, 15 captured evidence files, ONE commit),
# then S02 and S03 after the commit together with the other checks. Sequential within the attempt tree.
H=$PWD/.agent/evidence/105-qa-adversarial-contract-review/helpers
python3 "$H/gen_attempt.py" /home/cnross/.tmp/claude-1000/-home-cnross-workspace02-nizam-framework/b87ce099-80d9-4a17-8331-ff678f08d08a/scratchpad/gen
echo "== after the attempt commit: AT1 AT3 AT4 AT5 S01 S02 S03 S04 S07 S08 S09 (S05/S06 already proven in 03a on the identical tree)"
TAIL=2 python3 "$H/runall.py" /home/cnross/.tmp/claude-1000/-home-cnross-workspace02-nizam-framework/b87ce099-80d9-4a17-8331-ff678f08d08a/scratchpad/gen/att AT1 AT2 AT3 AT4 AT5 S01 S02 S03 S04 S07 S08 S09
echo "== evidence-shape check of the captured Generator files (line 1 = invocation, last line EXIT:<code>)"
for f in /home/cnross/.tmp/claude-1000/-home-cnross-workspace02-nizam-framework/b87ce099-80d9-4a17-8331-ff678f08d08a/scratchpad/gen/att/.agent/evidence/105/*.txt; do echo "$(basename "$f"): line1=[$(head -n 1 "$f" | cut -c1-40)] last=[$(tail -n 1 "$f")]"; done
