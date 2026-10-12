#!/usr/bin/env python3
"""Readonly ModeB metadata audit; never executes product acceptance commands."""
import pathlib,subprocess,json,hashlib,stat,re
r=pathlib.Path('.').resolve();E=r/'.agent/evidence/113'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
git=lambda *a:subprocess.check_output(['git',*a],text=True).strip()
C='79baee0c54f4b7b7c01c419fd843d6d1842d5ee1';B='0ae15a77d6dcf745bcae6c878d34d20fd2b6633e';A='a57c860a18c82990c4a43deed1465bd052bb4c3f'
source=json.loads((E/'current-source-inputs.json').read_text());fixed=json.loads((E/'fixed-inputs.json').read_text());contract=json.loads((r/'.agent/contracts/113.json').read_text())
assert git('rev-parse','HEAD')==B and git('rev-parse',C+'^')==B and git('rev-parse',C+'^{tree}')==source['candidate']['tree']=='51211ec0be1fc1bcb7ad11dfad030e9e7c3f4f80'
assert sha(E/'current-source-inputs.json')=='96ab81350cc2936abe173aa66fb3ee4cccf08c0390ad2ccbf1f06dbac06fbb3d'
assert source['fixed_inputs_sha256']==sha(E/'fixed-inputs.json')=='ea9bdf44ae248ca7c82699a953b9abd82c70763ccb13568cdd5dc7351864f9af'
assert source['contract_sha256']==fixed['contract_sha256']==sha(r/'.agent/contracts/113.json')=='e4fa0058a7f46c1da91a114c243942decbb4f85d4174007b9a07bc005f0a29ea'
assert json.loads((E/'current-source-seal.json').read_text())=={'manifest_sha256':sha(E/'current-source-inputs.json'),'candidate_commit':C}
assert json.loads((E/'fixed-inputs-seal.json').read_text())=={'manifest_sha256':sha(E/'fixed-inputs.json')}
assert len(source['source_paths'])==8 and len(fixed['files'])==360
for category,members in [('source',source['source_paths']),('fixed',fixed['files'])]:
 for path,meta in members.items():
  p=r/path
  assert p.is_file() and not p.is_symlink() and sha(p)==meta['sha256'] and ('100755' if p.stat().st_mode&0o111 else '100644')==meta['mode'],path
  assert hashlib.sha256(subprocess.check_output(['git','show',C+':'+path])).hexdigest()==meta['sha256'],path
  assert git('ls-tree',C,'--',path).split()[0]==meta['mode'],path
 print('CURRENT_AND_CANDIDATE_REPLAY',category,len(members),'PASS')
assert sha(r/'.agent/validator/113-test-bundle-review.json')=='5f23145555e5e2748c80efcee2f056277918b6055e72b4e2e08667b240d7da98'
assert subprocess.check_output(['git','show',C+':.agent/validator/113-test-bundle-review.json'])==(r/'.agent/validator/113-test-bundle-review.json').read_bytes()
public=set(source['source_paths']);assert set(git('diff','--name-only',B,C).splitlines())==public
allowed=public|{'.agent/contracts/113.json','.agent/feature_list_015.json','.agent/run_state.json','docs/planning/phase_015.yaml','docs/planning/DEBT.md','.agent/validator/113-mode-a.json','.agent/validator/113-test-bundle-review.json','.agent/validator/113-mode-b.json','.agent/qa/113-contract-review.json','.agent/qa/113.json'}
branch=git('diff','--name-only',A,C).splitlines();working=set(git('diff','--name-only',B).splitlines()+git('ls-files','--others','--exclude-standard').splitlines())
assert all(p in allowed or p.startswith('.agent/evidence/113/') for p in set(branch)|working)
print('SCOPE_ALLOWED_BRANCH_PATHS',len(branch),'PASS; B..C exactly8; untracked-aware current scope bounded')
h=json.loads((E/'private/history.json').read_text());mapping=contract['recovery']['historical_contract_map'];assert len(h)==4279
for path,meta in h.items():
 p=E/'recovery-inputs/debt-original.md' if path=='docs/planning/DEBT.md' else r/mapping['archive_path'] if path==mapping['original_history_entry'] else r/path
 assert p.is_file() and not p.is_symlink() and sha(p)==meta['sha256'] and stat.S_IMODE(p.stat().st_mode)==meta['permissions'],path
assert {str(p.relative_to(r)) for p in (r/'.nizam').rglob('*') if p.is_file() or p.is_symlink()}=={p for p in h if p.startswith('.nizam/')}
print('HISTORY4279_INSTALL239_EXACT', 'PASS; only two authorized mappings')
receipts=json.loads((E/'source-attempt2-development-result.json').read_text());indices=[1,2,3,4,5,6,8,9,10,11,12,13,15,16]
assert [x['index'] for x in receipts['checks']]==indices and receipts['candidate_commit']==C and receipts['formal_acceptance'] is False
for x in receipts['checks']:
 i=x['index'];assert x['command']==contract['verification'][i-1]['command'] and x['actual_exit']==0
 p=r/x['evidence'];text=p.read_text();assert text.startswith('COMMAND: '+x['command']+'\nCANDIDATE_SHA: '+C+'\n') and re.findall(r'(?m)^EXIT:\s*(-?\d+)\s*$',text)==['0'] and text.rstrip().endswith('EXIT: 0'),i
 output=r/x['output'];assert output.is_file() and not output.is_symlink()
 header='PROOF_SCOPE: Development only; no independent acceptance or gate verdict.\n'
 captured=text.split(header,1)[1].rsplit('EXIT: 0',1)[0]
 assert captured==output.read_text()+('' if output.read_text().endswith('\n') else '\n'),(i,'output bytes')
 print('DEVELOPMENT_RECEIPT',i,'ACTUAL_EXIT0','SHA256',sha(p),'OUTPUT_SHA256',sha(output))
numstat=git('diff','--numstat',B,C).splitlines();assert sum(sum(map(int,line.split('\t')[:2])) for line in numstat)==193
print('PUBLIC_NUMSTAT193', 'PASS; no measurement algorithm replacement')
print('METADATA_AUDIT:PASS; source8/fixed360/history4279/install239/receipt14/scope; formal QA unexecuted')
