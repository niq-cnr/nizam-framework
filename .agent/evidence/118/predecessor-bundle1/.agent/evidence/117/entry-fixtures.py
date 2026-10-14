"""Independent entry tests using actual, immutable, approved local snapshots.

No synthetic production verdicts: the real proposal, independent gate bytes and
approved contract are copied in their historical production order from Git.
Only the scratch origin and test input/observations are subsequently mutated.
"""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
APPROVED = '970ea233f77b4468105ddf6e401babbd0049d0b2'
PROPOSAL = 'f42e1b91d21c99a16d90f1e403f48ec37341b1ac'
CASES = ('accepted-entry', 'reject-foreign-repo', 'reject-stale-pin', 'reject-role-write')
CONTRACT = '.agent/contracts/117.json'
AUTH = '.agent/evidence/phase017-activation/authorization.json'
API = '.agent/evidence/117/api-interface.json'
GATES = ('.agent/validator/117-mode-a-recovery1.json', '.agent/qa/117-contract-review-recovery1.json')
CRITICAL = ('NIZAM.json', 'tools/SKILL.md', 'standard/AGF.md',
            'standard/capability_profiles.md', 'standard/permission_classes.md')
SNAPSHOT_PATHS = (AUTH, '.nizam/provenance.json', *('.nizam/' + p for p in CRITICAL),
                  CONTRACT, API, *GATES, '.agent/run_state.json', '.agent/feature_list_017.json',
                  'tools/workflow_assurance.py', 'tools/test_workflow_assurance.py')


def canonical(v): return json.dumps(v, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
def sha(data): return hashlib.sha256(data).hexdigest()
def require(ok, message):
    if not ok: raise AssertionError('POLICY_ASSERTION: ' + message)
def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], stderr=subprocess.PIPE).decode().strip()


class EntryFixture:
    def __init__(self, parent):
        self.root = Path(parent) / 'entry-repo'
        subprocess.run(['git', 'clone', '-q', '--shared', '--no-checkout', str(ROOT), str(self.root)],
                       check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        git(self.root, 'remote', 'set-url', 'origin', 'https://github.com/niq-cnr/nizam-framework.git')
        # All referenced immutable authority/proposal/tag commits are actual local objects.
        for path in SNAPSHOT_PATHS:
            data = subprocess.check_output(['git', '-C', str(ROOT), 'show', APPROVED + ':' + path])
            self.write(path, data)
            mode = git(ROOT, 'ls-tree', APPROVED, path).split()[0]
            (self.root / path).chmod(0o755 if mode == '100755' else 0o644)
        self.contract = self.read(CONTRACT)
        self.entry = {'schema_version': 1, 'repository': 'niq-cnr/nizam-framework',
                      'authorization': {'path': AUTH,
                         'revision': self.contract['entry_authority']['authorization_revision'],
                         'sha256': sha((self.root / AUTH).read_bytes())},
                      'installed': {k: self.contract['entry_authority']['installed_pin'][k]
                                    for k in ('tag', 'resolved_sha')},
                      'contract': {'path': CONTRACT, 'sha256': sha((self.root / CONTRACT).read_bytes()),
                                   'feature_id': '117'},
                      'role': 'Generator', 'profile': 'generator-deterministic',
                      'writes': [{'path': 'tools/workflow_assurance.py', 'fields': [], 'operation': 'write'}]}

    def write(self, path, data):
        p = self.root / path; p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data if isinstance(data, bytes) else canonical(data))

    def read(self, path): return json.loads((self.root / path).read_bytes())

    def rehash_contract(self):
        self.entry['contract']['sha256'] = sha((self.root / CONTRACT).read_bytes())


def mutate(f, name):
    if name == 'accepted-entry':
        f.entry.update(role='Evaluator', profile='evaluator-adversarial')
        f.entry['writes'] = [{'path': 'tools/test_workflow_assurance.py', 'fields': [], 'operation': 'write'}]
    elif name == 'reject-foreign-repo':
        git(f.root, 'remote', 'set-url', 'origin', 'https://github.com/foreign/foreign.git')
    elif name == 'reject-stale-pin':
        v = f.read('.nizam/provenance.json'); v['resolved_sha'] = '0' * 40
        f.write('.nizam/provenance.json', v)
    elif name == 'reject-role-write':
        f.entry['writes'] = [{'path': '.agent/run_state.json', 'fields': ['/current_feature'], 'operation': 'write'}]
    else: raise ValueError('unknown entry case')


def reject(api, f, label):
    try: api.verify_authorized_entry(f.root, f.entry)
    except api.AssuranceError as exc:
        require(bool(str(exc)), label + ': diagnostic'); return
    require(False, label + ': invalid entry accepted')


def isolated(api, mutation, label):
    with tempfile.TemporaryDirectory(prefix='nizam117-negative-') as parent:
        f = EntryFixture(parent)
        require(api.verify_authorized_entry(f.root, f.entry) is True, label + ': valid positive')
        mutation(f); reject(api, f, label)


def run_case(name, api):
    require(name in CASES and callable(api.verify_authorized_entry), 'real entry API is callable')
    with tempfile.TemporaryDirectory(prefix='nizam117-entry-') as parent:
        f = EntryFixture(parent)
        require(api.verify_authorized_entry(f.root, f.entry) is True, name + ': Generator source positive')
        mutate(f, name)
        if name == 'accepted-entry':
            require(api.verify_authorized_entry(f.root, f.entry) is True, 'explicit Evaluator test write accepted')
            cli_controls(api, f)
        else: reject(api, f, name)
    if name == 'accepted-entry':
        for role, profile in [('Orchestrator','orchestrator-primary'), ('Planner','planner-creative'),
                              ('Validator','validator-structural'), ('Evaluator','evaluator-adversarial')]:
            with tempfile.TemporaryDirectory(prefix='nizam117-role-positive-') as parent:
                f = EntryFixture(parent); f.entry.update(role=role, profile=profile, writes=[])
                require(api.verify_authorized_entry(f.root, f.entry) is True, 'known role with no write')
        for change in (lambda f: f.entry.update(schema_version=True),
                       lambda f: f.entry.update(profile='planner-creative'),
                       lambda f: f.entry.update(role='Unknown'),
                       lambda f: f.entry.update(extra='caller authority'),
                       lambda f: f.entry['contract'].update(feature_id='118')):
            isolated(api, change, 'closed typed entry and installed role/profile')
    elif name == 'reject-foreign-repo':
        def authority(f):
            obj=f.read(AUTH); obj['project']='foreign/repo'; f.write(AUTH,obj)
            f.entry['authorization']['sha256']=sha((f.root/AUTH).read_bytes())
        for change in (authority, lambda f: f.entry.update(repository='foreign/repo'),
                       lambda f: git(f.root,'remote','remove','origin')):
            isolated(api, change, 'observed immutable local authorization')
        for field,value in [('active_contract_id','118'),('current_feature',None),('status','complete')]:
            def state(f, field=field, value=value):
                s=f.read('.agent/run_state.json');s[field]=value;f.write('.agent/run_state.json',s)
            isolated(api,state,'actual active117 state')
    elif name == 'reject-stale-pin':
        for path in ('.nizam/NIZAM.json','.nizam/tools/SKILL.md','.nizam/standard/AGF.md',
                     '.nizam/standard/capability_profiles.md','.nizam/standard/permission_classes.md'):
            isolated(api, lambda f,p=path:f.write(p,(f.root/p).read_bytes()+b'\n'), 'critical pinned bytes')
        isolated(api, lambda f:(f.root/'.nizam/tools/SKILL.md').chmod(0o755), 'critical installed mode')
        def stale_gate(f):
            p=GATES[1];v=f.read(p);v['revision_reviewed']=True;f.write(p,v)
            c=f.read(CONTRACT);c['approvals']['gate_refs']['evaluator_contract_review']['sha256']=sha((f.root/p).read_bytes());f.write(CONTRACT,c);f.rehash_contract()
        isolated(api,stale_gate,'typed current revision gate')
        def stale_proposal(f):
            c=f.read(CONTRACT);c['estimated_lines']=1;f.write(CONTRACT,c);f.rehash_contract()
        isolated(api,stale_proposal,'unchanged proposed obligations')
    else:
        for path,fields,op in [('tools/test_workflow_assurance.py',[],'write'),
                               ('.agent/run_state.json',[],'write'),
                               ('.agent/run_state.json',['/history'],'write'),
                               ('.agent/run_state.json',['/scope_budget'],'write'),
                               ('../escape',[],'write'),('.nizam/tools/SKILL.md',[],'write')]:
            isolated(api, lambda f,p=path,x=fields,o=op:f.entry.update(writes=[{'path':p,'fields':x,'operation':o}]), 'explicit operation/field/path ownership')
        with tempfile.TemporaryDirectory(prefix='nizam117-root-positive-') as parent:
            f=EntryFixture(parent); f.entry.update(role='Orchestrator',profile='orchestrator-primary',
                writes=[{'path':'.agent/run_state.json','fields':['/history'],'operation':'append'}])
            require(api.verify_authorized_entry(f.root,f.entry) is True,'Root owned history append')
            f.entry['writes'][0]['operation']='write'; reject(api,f,'history overwrite forbidden')
        with tempfile.TemporaryDirectory(prefix='nizam117-evidence-positive-') as parent:
            f=EntryFixture(parent); f.entry.update(role='Evaluator',profile='evaluator-adversarial',
                writes=[{'path':'.agent/evidence/117/new-owned.json','fields':[],'operation':'write'}])
            require(api.verify_authorized_entry(f.root,f.entry) is True,'new owned evidence explicit grant')
            f.write('.agent/evidence/117/new-owned.json',{}); reject(api,f,'create-only cannot overwrite')


def cli_controls(api, f):
    p=f.root/'entry-input.json';f.write('entry-input.json',f.entry)
    cmd=[sys.executable,api.__file__,'entry','--repo',str(f.root),'--entry',str(p)]
    result=subprocess.run(cmd,capture_output=True,text=True)
    require(result.returncode==0 and 'PASS' in result.stdout,'actual valid CLI entry')
    good=p.read_text()
    for data in (good[:-1]+',"schema_version":1}', '{"x":NaN}', '[]', '{broken'):
        p.write_text(data);result=subprocess.run(cmd,capture_output=True,text=True)
        require(result.returncode!=0 and result.stderr.strip() and 'PASS' not in result.stdout,
                'strict malformed CLI entry after valid positive')
