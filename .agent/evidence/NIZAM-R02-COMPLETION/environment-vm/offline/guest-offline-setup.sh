set -eu
mkdir -p /opt/nizam-offline
mkdir -p /opt/nizam-environment
tar -xf /tmp/nizam-guest-packages.tar -C /opt/nizam-offline
python3 - <<'VERIFY'
from pathlib import Path
import json,hashlib
p=Path('/opt/nizam-offline')
for item in json.loads((p/'verified-packages.json').read_text())['packages']:
 f=p/item['file']
 assert f.stat().st_size==item['bytes']
 assert hashlib.sha256(f.read_bytes()).hexdigest()==item['sha256']
print('all9 Ubuntu package bytes and hashes match host-verified downloads')
VERIFY
dpkg -i /opt/nizam-offline/*.deb > /opt/nizam-environment/offline-install.stdout.txt 2> /opt/nizam-environment/offline-install.stderr.txt
dpkg --audit > /opt/nizam-environment/dpkg-audit.txt
python3 -c 'import jsonschema; print(jsonschema.__version__)' > /opt/nizam-environment/jsonschema-version.txt
git --version > /opt/nizam-environment/git-version.txt
cd /opt/nizam-work/nizam-framework
git rev-parse HEAD > /opt/nizam-environment/revision.txt
git status --porcelain=v1 > /opt/nizam-environment/source-status.txt
sha256sum .nizam/tools/start_path.py .nizam/tools/isolated_trial_adapter.py .nizam/tools/linux_trial_sandbox.sh > /opt/nizam-environment/governance-sha256.txt
python3 -c 'import ctypes; c=ctypes.CDLL(None,use_errno=True); r=c.syscall(444,0,0,1); print("landlock_abi",r,"errno",ctypes.get_errno()); raise SystemExit(0 if r>0 else 1)' > /opt/nizam-environment/landlock-abi.txt
set +e
PYTHONDONTWRITEBYTECODE=1 python3 .nizam/tools/start_path.py preflight --route high-risk --root /opt/nizam-work/nizam-framework > /opt/nizam-environment/preflight.json 2> /opt/nizam-environment/preflight.stderr.txt
rc=$?
set -e
printf '%s\n' "$rc" > /opt/nizam-environment/preflight.exit.txt
cat /opt/nizam-environment/landlock-abi.txt /opt/nizam-environment/preflight.json /opt/nizam-environment/preflight.stderr.txt
printf 'NIZAM_VM_PREFLIGHT_DONE exit=%s\n' "$rc"
exit "$rc"
