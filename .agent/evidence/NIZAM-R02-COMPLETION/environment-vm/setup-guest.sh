#!/bin/bash
set -eu
exec > /var/log/nizam-environment-setup.log 2>&1
mkdir -p /opt/nizam-environment
mkdir -p /opt/nizam-work
 tar --no-same-owner -xzf /mnt/nizam-seed/framework.tar.gz -C /opt/nizam-work
cd /opt/nizam-work/nizam-framework
uname -a > /opt/nizam-environment/uname.txt
sha256sum .nizam/tools/start_path.py .nizam/tools/isolated_trial_adapter.py .nizam/tools/linux_trial_sandbox.sh > /opt/nizam-environment/governance-sha256.txt
git rev-parse HEAD > /opt/nizam-environment/revision.txt
python3 -c 'import ctypes; c=ctypes.CDLL(None,use_errno=True); r=c.syscall(444,0,0,1); print("landlock_abi",r,"errno",ctypes.get_errno()); raise SystemExit(0 if r>0 else 1)' > /opt/nizam-environment/landlock-abi.txt
set +e
PYTHONDONTWRITEBYTECODE=1 python3 .nizam/tools/start_path.py preflight --route high-risk --root /opt/nizam-work/nizam-framework > /opt/nizam-environment/preflight.json 2> /opt/nizam-environment/preflight.stderr.txt
rc=$?
set -e
printf '%s\n' "$rc" > /opt/nizam-environment/preflight.exit.txt
cat /opt/nizam-environment/landlock-abi.txt /opt/nizam-environment/preflight.json
printf 'NIZAM_VM_PREFLIGHT_DONE exit=%s\n' "$rc" > /dev/ttyS0
