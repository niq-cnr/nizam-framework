# S17 and S18 self-containment: (a) static scan for host-specific paths; (b) replay from the root of a FRESH clone at the attempt commit in a different
# directory, with a minimal environment (env -i), twice.
set -u
H=$PWD/.agent/evidence/103-qa-adversarial-contract-review/helpers/rev2
for id in S17 S18; do
  echo "== static scan $id: host-specific / scratch paths, absolute paths, cwd changes, network, env reads"
  python3 -I -c "
import re,sys
t=open('$H/cmds/$id.sh').read()
pats={'scratchpad/.tmp/home path':r'scratchpad|\.tmp|/home/|/Users/','absolute /tmp or /usr path':r'(?<![\w.])/(tmp|usr|var|opt)/','os.chdir/cd':r'os\.chdir|\bcd\b ','network':r'socket\.|https?://|curl|wget','repo-relative paths used':r'tools/test_convergent_review\.py|\.agent/contracts/103\.json'}
for k,p in pats.items(): print('  %-30s %s'%(k, sorted(set(re.findall(p,t)))[:4] if k!='repo-relative paths used' else sorted(set(re.findall(p,t)))))
print('  uses tempfile.TemporaryDirectory:', 'tempfile.TemporaryDirectory' in t, '| PATH shim built inside the temp dir:', \"'bin' / 'unshare'\" in t)"
done
R="$NIZAM_EVAL_SCRATCH/replay"
git clone -q "$NIZAM_EVAL_SCRATCH/base" "$R" && git -C "$R" checkout -q --detach "$(git -C "$NIZAM_EVAL_SCRATCH/att" rev-parse HEAD)"
echo "== fresh clone $(git -C "$R" rev-parse --short HEAD), different directory name, no .agent/evidence/103 scratch state beyond the commit; env -i replay:"
cd "$R"
for pass in 1 2; do for id in S17 S18; do
  env -i PATH="$PATH" HOME="${HOME:-/nonexistent}" bash "$H/cmds/$id.sh" | tail -2 | cut -c1-200; echo "$id pass $pass rc=${PIPESTATUS[0]}"
done; done
cd - >/dev/null
