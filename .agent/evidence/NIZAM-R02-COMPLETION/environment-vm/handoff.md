# Qualified ephemeral Linux guest: environment handoff

Actual unmodified high-risk preflight passed with exit 0. This qualification belongs to the guest identified below; the host still lacks Landlock. No framework implementation was performed by the environment provisioner.

## Observed identity and source

- Full-system QEMU 8.2.2, TCG software emulation, actual Ubuntu kernel 6.8.0-147-generic.
- Running owned host process: PID 11130. Keep running until Root authorizes final cleanup.
- Guest hostname: nizam-landlock-vm; boot ID: 380fdeb3-fdb8-40f0-a67a-e18de3032f9d.
- Real Landlock ABI: 4; errno: 0.
- Guest checkout: /opt/nizam-work/nizam-framework.
- Exact HEAD: 00e0bcb1bd16ba2ddaf5774153bbf2c1e05244a6. Actual git status was empty.
- Origin: https://github.com/niq-cnr/nizam-framework.git.
- Git 2.43.0; Python 3.12.3; jsonschema 4.10.3.
- Passing preflight ran as guest UID 0 through sudo, with PYTHONDONTWRITEBYTECODE=1.

## Evidence

- guest/preflight.json: exact successful stdout; guest/preflight.stderr.txt: exact stderr; guest/preflight.exit.txt: exact exit.
- guest/identity.json: observed kernel, boot ID, source revision/status, critical hashes and full installed .nizam file hashes.
- guest/landlock-abi.txt: actual syscall ABI observation.
- guest/offline-install.stdout.txt, guest/offline-install.stderr.txt, guest/dpkg-audit.txt: guest dependency installation/audit.
- guest-handoff.execution.json and guest-handoff.stdout.json: retrieval argv/stdin/exit/timestamps and raw payload.
- offline/guest-offline-setup.execution.json, .sh, .stdout.txt, .stderr.txt: exact offline repair and successful preflight execution.
- offline/verified-packages.json: nine official Ubuntu package hashes independently matched to authenticated APT index SHA256/Size fields.
- verified-image.json and SHA256SUMS.gpg: Canonical image digest/signature verification evidence; cloud-image-signature.stderr.txt includes successful verification.
- qemu-argv-04.json: active full-system VM launch arguments; qemu-launch-04.execution.json: actual launch exit.
- Earlier failures are retained: guest-preflight.stderr.txt records the initial missing-Git error; serial-02.log records cloud-init DNS/package failure.

## Execution interface

Use this same guest for implementation, governance begin/done, and code/QA execution. Root must explicitly release the implementation hold under the reviewed contract before implementation begins.

```bash
ssh -i /tmp/nizam-landlock-vm/guest-access-key -p 22222   -o BatchMode=yes -o StrictHostKeyChecking=yes   -o UserKnownHostsFile=/tmp/nizam-landlock-vm/known_hosts   ubuntu@127.0.0.1 'sudo -n env PYTHONDONTWRITEBYTECODE=1 bash -s' <<'GUEST'
set -eu
cd /opt/nizam-work/nizam-framework
python3 .nizam/tools/start_path.py preflight --route high-risk --root /opt/nizam-work/nizam-framework
GUEST
```

SSH host key was verified against the VM serial console and pinned in the temporary known_hosts file. The temporary private key remains outside the repository; do not copy or commit it.

For reviewed inputs, use scp with the same identity and host-key options, replacing SSH `-p 22222` with SCP `-P 22222`, to `ubuntu@127.0.0.1:/tmp/<task-specific-input>`. Then copy/extract using sudo inside the guest. Retrieve only intended source/evidence outputs through the same interface. No host editing or host QA should be represented as guest-qualified work.

## Boundaries and provenance

The image is Canonical Ubuntu 24.04 minimal release-20261017, SHA256 b3296484e362ba2e713489a5de6225c719d9500962bde25d15f2f21e512c7658; its official signature verified using the Ubuntu cloud-image keyring. QEMU packages were downloaded from authenticated Ubuntu archives and extracted temporarily without installing host packages. Guest Git dependencies were installed offline from nine authenticated packages (13.4 MB, no existing packages upgraded). Guest DNS remains unavailable. No host sysctl, kernel, security policy, cloud service, or installed framework tool was changed.

An operational preflight does not replace subsequent contract approval, begin, QA, scope verification, or done gates. The guest capability is now real and available; workflow authorization remains Root's responsibility.
