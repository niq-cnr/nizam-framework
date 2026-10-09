# Static scan of the 14 extracted commands for non-determinism hazards: network, wall clock, randomness, pipelines that swallow the exit code, sudo.
H=$PWD/.agent/evidence/105-qa-adversarial-contract-review/helpers
cd "$H/cmds" && for f in AT1 AT2 AT3 AT4 AT5 S01 S02 S03 S04 S05 S06 S07 S08 S09; do
  n=$(wc -c < $f.sh)
  hits=$(grep -noE "curl|wget|requests|urllib|socket|gh |time\.time|datetime|random|sudo|\| *tee|\|\| *true|sleep" $f.sh | tr '\n' ' ')
  echo "$f bytes=$n hazards=[${hits}]"
done
echo "-- serial-guard presence (S05 S06 S09 must hold the flock)"
grep -c "fcntl.flock" S05.sh S06.sh S09.sh
echo "-- python compile of every heredoc payload"
for f in S01 S02 S03 S04 S05 S06 S07 S08 S09; do python3 - "$f" <<'PY'
import sys, re
t = open(sys.argv[1] + '.sh').read()
m = re.match(r"python3 - <<'PY'\n(.*)\nPY\n$", t, re.S)
compile(m.group(1), sys.argv[1], 'exec'); print(sys.argv[1], 'compiles')
PY
done
