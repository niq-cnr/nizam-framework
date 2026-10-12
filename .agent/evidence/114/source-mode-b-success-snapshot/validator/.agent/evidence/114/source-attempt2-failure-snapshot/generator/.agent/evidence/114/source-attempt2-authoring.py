from pathlib import Path
import json,re,subprocess,datetime
p=Path('.'); base='45ceeb80eabc823400f2bb6044edcb4fa3aa9b2f'; day=datetime.datetime.now(datetime.timezone.utc).date().isoformat()
paths=['CHANGELOG.md','docs/planning/ROADMAP.md','docs/planning/manifest.json','docs/planning/backlog_dag.json','docs/planning/backlog_reconciliation.md']
old={}
for f in paths:
 q=p/f; b=q.read_bytes(); original=subprocess.run(['git','show',base+':'+f],capture_output=True,check=True).stdout
 assert b==original,'Unexpected pre-write source '+f
 old[f]=b.decode()
q=p/'.agent/evidence/114/release-readiness.md'; assert not q.exists()
q.write_text('''---
id: nizam-phase015-release-readiness
title: "Normative-stage next MINOR readiness"
description: "Candidate-bound normative assessment and independent acceptance, phase-close and human release boundaries."
version: 0.1.0
status: active
authoritative_source: .agent/evidence/114/release-readiness.md
change_log:
  - version: "0.1.0"
    date: "'''+day+'''"
    summary: "Describe normative delivery, actual predecessor inputs and separate candidate acceptance, close and release obligations."
---

# Normative-stage next MINOR readiness

## Assessment inputs

The approved scope is `.agent/product_spec_015.md` and feature114 in
`.agent/feature_list_015.json`, implemented under `.agent/contracts/114.json`.
Canonical lifecycle comes from that feature list and `docs/planning/phase_015.yaml`;
this dossier does not declare their completion.

Feature113 completed and merged through PR88 at the actual Main baseline
`45ceeb80eabc823400f2bb6044edcb4fa3aa9b2f`. Its independent sixteen-command QA is
`.agent/qa/113.json`, with Mode B at `.agent/validator/113-mode-b.json` and capture
at `.agent/evidence/113/evidence-gate.txt`. The six successful PR checks and five
successful Main jobs are preserved in `.agent/evidence/114/predecessor113-pr-premerge.json`
and `.agent/evidence/114/predecessor113-merge-main.json`. These are predecessor
proofs and do not substitute for fresh feature114 acceptance.

Parent binds the assessed six source files to an actual immutable Git candidate
and tree through `.agent/evidence/114/current-source-inputs.json` and its separate
source seal after the source commit exists. The sidecar also records the reviewed
fixed-input digest, approved-contract pin and three canonical precompletion
snapshots. This dossier refers to that external binding; it contains no future
candidate, self, QA or capture hash.

## Delivered normative scope

| Feature | Delivered boundary |
| --- | --- |
| 110 | Neutral session protocol and generic attempt, acceptance, permission and handoff rules. |
| 111 | Closed session/operation schemas, eighteen fixtures and shared C12 relational record checks. |
| 112 | Consumer-aspirational SBCL binding, profile, condition/restart and fresh acceptance rules. |
| 113 | Optional adapter calls, conditional S1–S9 and routing; existing ten mandatory items and consumers remain compatible. |

Schema/C12 validity proves record structure and relations. Normative rules and
fixtures do not prove executable runtime enforcement or any live case.

## Human release boundary

The next MINOR release needs a separate H-FRAMEWORK-RELEASE decision, including
operator sign-off and explicit tag authority. Those acts are outstanding for a
new candidate. Normative phase closure selects no fixed release number and creates
no release, tag or publication. Historical published v1.5.0 release authority was
executed; it does not authorize the next candidate's release.

### Consumer upgrade boundary

H-CONSUMER-UPGRADE is distinct and remains outstanding for adopting a new
candidate. Historical local self-adoption was authorized and commissioned at
v1.5.0; that installed pin remains unchanged. A later authorized upgrade needs
its reviewed immutable pin and re-bootstrap. Authored source changes do not
upgrade the installed payload or imply external organization adoption.

## Independent acceptance and canonical close

The actual candidate requires independent Mode B, then fresh independent QA for
all twelve contract commands and exactly one additional adversarial spot. These
include the existing validator, payload sweep, fixture self-test, end-to-end
bootstrap and PR-mode release closeout; feature114 checks bind predecessor,
readiness, planning, scope/history, discriminating controls and the frozen
Git-numstat budget classifier. Historical QA and checker-development results
cannot stand in for this acceptance.

Fresh QA personally reviews all six source files against the approved scope and
records semantic evidence before the readiness check consumes the source map.
The actual evidence-capture gate checks typed results, command output, exit
status, exercised revision and referenced files. Only after that approval may
Parent mark feature114 and phase015 complete, then update the manifest and derived
run state and finalize the permitted planning projections. Canonical records and
`.agent/qa/114.json` with `.agent/evidence/114/evidence-gate.txt` supply actual
results when produced; this conditional sequence asserts no future PASS.

## Runtime and subsequent planning

The phase016 controller, executable adapter, SBCL launcher, isolated capable live
CI and all thirteen live proofs remain pending. Phase015 schemas, illustrative
binding and optional capability cannot claim live-conformance acceptance.

PLAN-WA remains a pending planning packet after normative close; PLAN-016 depends
on that close and serializes after PLAN-WA. Neither receives an allocation or
activation here. The six selected WA choices are candidate invalidation,
acceptance ownership, routing profiles, shadow profiles, cause routing and
conflict/retry handling. They are selected planning inputs; no WA implementation
or active-gate reduction is delivered. Relative WA implementation versus phase016
remains open and requires its own planning and authority.
''')
ch=old['CHANGELOG.md']; anchor='### Changed\n\n'
unreleased_heading='## [Unreleased]\n'; assert ch.count(unreleased_heading)==1
section_start=ch.index(unreleased_heading)+len(unreleased_heading)
next_h2=re.search(r'(?m)^## ',ch[section_start:])
section_end=section_start+next_h2.start() if next_h2 else len(ch)
unreleased=ch[section_start:section_end]; assert unreleased.count(anchor)==1
anchor_end=section_start+unreleased.index(anchor)+len(anchor)
addition='''- **Normative-stage readiness (feature114).** Added a candidate-bound next MINOR
  dossier and narrow current planning projections. Closure requires independent
  Mode B, fresh twelve-command QA, one additional adversarial spot, actual evidence
  capture and Parent canonical completion. Human release/tag and consumer upgrade
  remain separate decisions; published/installed v1.5.0 is unchanged. Schema/C12
  record validity and normative adapter/binding rules establish no executable
  controller, SBCL launcher, capable live CI or thirteen live proofs. WA choices
  remain selected planning inputs without new allocation or gate reduction.

'''
(p/'CHANGELOG.md').write_text(ch[:anchor_end]+addition+ch[anchor_end:])
rd=old['docs/planning/ROADMAP.md']; assert rd.startswith('---\n') and 'version: 0.59.1\n' in rd
rd=rd.replace('version: 0.59.1\n','version: 0.60.0\n',1)
log='  - version: "0.60.0"\n    date: "'+day+'"\n    summary: "Prepare feature114 normative readiness and bounded current projections; independent acceptance and canonical close remain required."\n'
rd=rd.replace('change_log:\n','change_log:\n'+log,1)
marker='## Current Position (2026-10-11)'; assert rd.count(marker)==1
rd=rd.replace(marker,'''### Feature114 readiness projection

Features110–113 are complete; feature114 and phase015 are in_progress. The
candidate-bound next MINOR dossier is prepared at
`.agent/evidence/114/release-readiness.md`. Its source sidecar and fresh independent
Mode B, twelve-command QA, own adversarial spot and evidence capture precede
Parent canonical close. No release/tag or consumer upgrade is authorized by
this projection. Published/installed v1.5.0 remains unchanged; executable
phase016 controller/SBCL/live13 proofs and PLAN-WA/PLAN-016 planning remain pending,
without allocation or gate reduction. Historical prose above retains its dated
assessment; canonical records and current DEBT supply current lifecycle/debt facts.

'''+marker.replace('2026-10-11',day),1)
pos=rd.index('## Current Position '); m=re.search(r'(?ms)^- .*?(?=^- |^## |\Z)',rd[pos:]); assert m is not None
bullet='''- **Phase015 normative readiness is prepared.** Features110–113 are complete;
  feature114 is in_progress under its renewed approved contract and independently
  reviewed bundle. The readiness dossier and four bounded planning projections
  await actual candidate Mode B, fresh QA/ownspot and capture before Parent closes
  canonical phase015. PLAN-WA/PLAN-016 stay pending and unallocated; future release,
  tag and consumer upgrade authority remain outstanding. Historical release and
  installed v1.5.0 records are preserved.
'''
rd=rd[:pos+m.start()]+bullet+rd[pos+m.end():]; (p/'docs/planning/ROADMAP.md').write_text(rd)
f='docs/planning/backlog_reconciliation.md'; rec=old[f]; assert 'version: 0.1.13\n' in rec
rec=rec.replace('version: 0.1.13\n','version: 0.1.14\n',1)
rec=rec.replace('change_log:\n','change_log:\n  - version: "0.1.14"\n    date: "'+day+'"\n    summary: "Add bounded current114 readiness projection while preserving prior reconciliation; canonical close follows actual independent capture."\n',1)
rec=rec.replace('## Current planning view — 2026-10-11','## Current planning view — '+day,1)
marker='## Prior reconciliation history'; assert rec.count(marker)==1
rec=rec.replace(marker,'''### Feature114 readiness projection

Canonical110–113 are complete; feature114 and phase015 are in_progress. The
readiness dossier is prepared for an actual Git candidate and external source
sidecar. Parent closes canonical records and finalizes this projection only after
independent Mode B, fresh twelve-command QA plus ownspot and actual evidence
capture. NIP3-113 reflects accepted predecessor proof; NIP3-114 awaits capture.
PLAN-WA and PLAN-016 remain pending, with PLAN-016 serialized after PLAN-WA;
selected WA choices create no allocation or gate reduction. Controller/SBCL/live13
proofs, new release/tag and consumer upgrade remain outstanding. Earlier prose
and reconciliation history are dated snapshots; current lifecycle and debt follow
canonical records and DEBT.

'''+marker,1); (p/f).write_text(rec)
f='docs/planning/manifest.json'; m=json.loads(old[f]); m['updated_at']=day; row=next(x for x in m['phases'] if x['id']=='015-live-runtime-normative')
assert row['status']=='in_progress' and row['activation_state']=='active'
row['note']='H-PHASE-015 approved7200/9360;110–113 complete with preserved independent proof. Feature114 in_progress under renewed approved contract and reviewed bundle; next MINOR readiness is prepared, with actual candidate ModeB/freshQA/ownspot/capture required before Parent canonical close. Prior recovery and historical assessments remain preserved. No WA/phase016 allocation, release/tag or installed upgrade.'
(p/f).write_text(json.dumps(m,indent=2,ensure_ascii=True)+'\n')
f='docs/planning/backlog_dag.json'; d=json.loads(old[f]); d['generated_at']=day; d['activated_phase']['current_status']='in_progress'; d['activated_phase']['run_state_position']='Canonical110–113 complete;114 in_progress under renewed approved contract and independently reviewed bundle, awaiting actual candidate ModeB/freshQA/ownspot/capture before phase015 close.'
packets={x['id']:x for x in d['packets']}
a=packets['NIP3-113']; a['status']='complete'; a['authority_status']='authorized'
a['prerequisites']['technical']={'satisfied':True,'reason':'Canonical112 and113 complete with independent QA/evidence capture;113 merged through PR88 at actual postmerge Main45ceeb.'}
a['prerequisites']['authority']={'satisfied':True,'reason':'H-PHASE-015 and both actual113 pre-code approvals authorized original113 scope; completed113 independent gates remain immutable.'}
a['prerequisites']['evidence']={'satisfied':True,'reason':'Actual113 ModeB, fresh16-command QA and capture plus six PR/five Main success receipts establish predecessor completion.'}
a['evidence']+=['.agent/validator/113-mode-b.json','.agent/qa/113.json','.agent/evidence/113/evidence-gate.txt','.agent/evidence/114/predecessor113-pr-premerge.json','.agent/evidence/114/predecessor113-merge-main.json']
a=packets['NIP3-114']; a['status']='in_progress'; a['authority_status']='authorized'
a['prerequisites']['technical']={'satisfied':True,'reason':'Canonical113 complete and merged at45ceeb with actual six PR/five Main success; predecessor proofs remain required inputs.'}
a['prerequisites']['authority']={'satisfied':True,'reason':'Both renewed actual114 pre-code gates approved original scope and authorized bounded recovery; corrected bundle independently approved before source.'}
a['prerequisites']['evidence']={'satisfied':False,'reason':'Prepared readiness awaits actual candidate ModeB, fresh twelve-command QA/ownspot and evidence capture before Parent114/phase015 close.'}
a['evidence']+=['.agent/contracts/114.json','.agent/validator/114-mode-a.json','.agent/qa/114-contract-review.json','.agent/validator/114-test-bundle-review.json']
for name in ['PLAN-WA','PLAN-016']:
 a=packets[name]; assert a['status']=='pending' and a['authority_status']=='authorized'
 a['prerequisites']['technical']['reason']='Canonical114/phase015 close requires actual QA/capture; PLAN-WA remains pending and PLAN-016 serializes after PLAN-WA. No new phase is allocated.'
 a['prerequisites']['evidence']['reason']='Six selected WA choices and historical inputs remain available; actual114 close and separate pending planning gates are still required.'
(p/f).write_text(json.dumps(d,indent=2,ensure_ascii=True)+'\n')
print('Authored exactly six pending Source deliverables; no tests run.')
