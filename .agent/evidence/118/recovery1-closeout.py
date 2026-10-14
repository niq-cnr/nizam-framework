"""Root canonical-first closure after verified actual capture."""
from pathlib import Path
import datetime
import importlib.util
import json
import re
import subprocess
import yaml

root=Path.cwd(); E='.agent/evidence/118/'
spec=importlib.util.spec_from_file_location('close118',root/E/'scope-guard.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
c=g.approved();g.closure(c)
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
def obj(p):return json.loads((root/p).read_text())
def write(p,v): (root/p).write_text(json.dumps(v,indent=2)+'\n')
# Canonical phase and step first.
p='docs/planning/phase_017.yaml'; v=yaml.safe_load((root/p).read_text());assert v['status']=='in_progress' and v['steps'][3]['status']=='IN_PROGRESS';v['status']='complete';v['description']='Captured Workflow Assurance foundation features115-118; independent acceptance and Root evidence verified. Follow-on phase016 remains proposed.';v['steps'][3].update(status='COMPLETED',evidence=E+'evidence-capture.json');(root/p).write_text(yaml.safe_dump(v,sort_keys=False))
c['status']='complete';write('.agent/contracts/118.json',c)
p='.agent/feature_list_017.json';v=obj(p);v.update(phase_status='complete',spec_version='0.3.0');v['features'][3].update(status='complete',passes=True,contract_ref='.agent/contracts/118.json',qa_ref='.agent/qa/118.json',evidence_ref=E+'evidence-capture.json',completed_at=now);write(p,v)
p='docs/planning/manifest.json';v=obj(p);v['updated_at']=now
for row in v['phases']:
 if row['id']=='017-workflow-assurance-foundation':row.update(status='complete',finished_at=now,note='Foundation115-118 captured through independent QA and Root evidence. Phase016 controller core remains proposed.')
write(p,v)
p='docs/planning/backlog_dag.json';v=obj(p);v['generated_at']=now
for row in v['packets']:
 if row['id']=='A04b':row.update(status='complete',qa='.agent/qa/118.json',completion_evidence=E+'evidence-capture.json',completed_at=now)
for row in v['planned_additional_nodes']:
 if row['feature_id'] in ('117','118'):row.update(status='complete',evidence='.agent/evidence/'+row['feature_id']+'/evidence-capture.json')
v['phase017_execution'].update(status='complete',feature=None,feature_status='complete',qa='.agent/qa/118.json',evidence=E+'evidence-capture.json',completed_at=now);write(p,v)
def doc(p,old,new,summary,addition):
 text=(root/p).read_text();assert 'version: '+old+'\n' in text;text=text.replace('version: '+old+'\n','version: '+new+'\n',1);text=text.replace('change_log:\n','change_log:\n  - version: "'+new+'"\n    date: "2026-10-14"\n    summary: "'+summary+'"\n',1);parts=text.split('---',2);parts[2]+=addition;(root/p).write_text('---'.join(parts))
doc('.agent/product_spec_017.md','0.2.0','0.3.0','Record captured foundation115-118 and bounded phase completion after independent acceptance.', '\n## Captured foundation — 2026-10-14\n\nFeatures 115–118 are complete in [canonical phase017](../docs/planning/phase_017.yaml).\nThe [feature118 QA](qa/118.json) and [Root capture](evidence/118/evidence-capture.json)\nbind the actual implementation, independent prerequisite20 and final acceptance.\nThe [recovery authorization](evidence/118/recovery-authorization.json) preserves\nfailed attempts while permitting reviewed repair of the framework fixtures and\ncompletion projection. The scope measurement in [run state](run_state.json)\ncounts the whole feature once within the original 5,400 allowance and 7,020 ceiling.\nThe [reviewed closeout correction](evidence/118/recovery1-closeout-review.json)\nfixes debt table validation while preserving frozen acceptance inputs.\nThe activation and design sections above remain historical planning snapshots.\nPhase016 controller core is the next proposed stage; installed v1.5.0 remains pinned.\n')
doc('docs/planning/operator_gates.md','0.37.0','0.38.0','Record completed phase017 and exercised feature118 recovery; phase016 remains proposed.', '\n## Foundation completion — 2026-10-14\n\nH-PHASE-017 is fulfilled by captured features 115–118 in\n[phase017](phase_017.yaml). H-CONTRACT-118-RECOVERY was exercised under\n[the operator authorization](../../.agent/evidence/118/recovery-authorization.json),\nwith independently reviewed acceptance repairs, [fresh QA](../../.agent/qa/118.json)\nand [Root capture](../../.agent/evidence/118/evidence-capture.json).\nEarlier gate entries retain their historical decisions. H-PHASE-016 activation\nand its proposed 5,650 counted allowance / 7,345 ceiling remain future; this\ncompletion does not activate controller execution or alter the installed v1.5.0 pin.\n')
p='docs/planning/DEBT.md';text=(root/p).read_text();assert 'version: 0.74.0\n' in text;text=text.replace('version: 0.74.0\n','version: 0.75.0\n',1).replace('change_log:\n','change_log:\n  - version: "0.75.0"\n    date: "2026-10-14"\n    summary: "Resolve only NDEBT-054 after reviewed recovery, actual feature118 QA and Root capture."\n',1)
rows=[x for x in text.splitlines() if x.startswith('| NDEBT-054 |')];assert len(rows)==1;old=rows[0];parts=old.split('|');assert len(parts)==7;parts[5]=' RESOLVED: operator-authorized [recovery](../../.agent/evidence/118/recovery-authorization.json), repaired independently reviewed acceptance and [actual QA](../../.agent/qa/118.json) captured by [Root](../../.agent/evidence/118/evidence-capture.json). Historical failures remain preserved. ';new='|'.join(parts);text=text.replace(old+'\n','',1);start=text.index('## Resolved');pos=text.index('\n| NDEBT-',start)+1;text=text[:pos]+new+'\n'+text[pos:];(root/p).write_text(text)
p='.agent/run_state.json';v=obj(p);v.update(status='complete',current_feature=None,active_contract_id=None,updated_at=now,last_action='Foundation115-118 captured; phase017 complete. Next proposed phase016 controller core awaits activation.');assert '118' not in v['completed_contract_ids'];v['completed_contract_ids'].append('118');v['history'].append({'at':now,'event':'phase017-foundation-captured','detail':'Actual SourceC2 prerequisite20, Generator3, independent ModeB and freshQA3 plus ownspot captured by Root. Canonical phase/step completed first, then mirrors; NDEBT054 resolved. Original allowance and historical failures retained. Phase016 remains proposed.','evidence':E+'evidence-capture.json'});write(p,v)
print('Canonical and derived closure written after actual receipt verification; measure whole118 then append budget once before final scope.')
