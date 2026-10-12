#!/usr/bin/env python3
"""Independently authored114 capture adapter; executed by Parent after freshQA."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import jsonschema
import yaml

ROOT=Path(__file__).resolve().parents[3]
E='.agent/evidence/114/'
def raw(path):
 p=ROOT/path; assert p.is_file() and not p.is_symlink(),path; return p.read_bytes()
def obj(path): return json.loads(raw(path))
def digest(path): return hashlib.sha256(raw(path)).hexdigest()
def approve(record):
 assert record['final_verdict']['approved'] is True
 assert all(record[k]==[] for k in ('issues','missing_acceptance_coverage','unsupported_claims'))
def receipt(path,command,candidate):
 text=raw(path).decode(); assert text.startswith('COMMAND: '+command+'\n'),path
 assert 'CANDIDATE_SHA: '+candidate+'\n' in text,path
 assert re.findall(r'^EXIT:\s*(-?\d+)\s*$',text,re.M)==['0'] and text.rstrip().endswith('EXIT: 0'),path

def main():
 contract=obj('.agent/contracts/114.json'); qa=obj('.agent/qa/114.json')
 source=obj(E+'current-source-inputs.json'); fixed=obj(E+'fixed-inputs.json')
 mode_b=obj('.agent/validator/114-mode-b.json'); bundle=obj('.agent/validator/114-test-bundle-review.json'); semantic=obj(E+'source-review.json')
 for record in (qa,mode_b,bundle,semantic): approve(record)
 jsonschema.validate(qa,obj('.nizam/schema/qa_verdict.schema.json'))
 jsonschema.validate(contract,obj('.nizam/schema/contract.schema.json'))
 assert contract['status']=='approved' and qa['feature_id']=='114' and qa['qa_pass'] is True and qa['required_fixes']==[]
 assert qa['checks_run']==qa['checks_passed']==len(qa['checks'])==len(contract['verification'])==12
 assert yaml.safe_load(raw('docs/planning/phase_015.yaml'))['status']=='in_progress','capture before canonical completion'
 assert fixed['actors']['final_qa']==qa['actor']==semantic['actor']
 assert fixed['actors']['bundle_reviewer']==mode_b['actor']==bundle['actor']
 assert len(set(fixed['actors'].values()))==4
 candidate=source['candidate']['commit']; source_hash=digest(E+'current-source-inputs.json'); fixed_hash=digest(E+'fixed-inputs.json')
 for record in (qa,mode_b,semantic):
  assert record['candidate_commit']==candidate and record['source_manifest_sha256']==source_hash and record['fixed_inputs_sha256']==fixed_hash
 assert bundle['fixed_inputs_sha256']==fixed_hash
 assert qa['mode_b_sha256']==digest('.agent/validator/114-mode-b.json')
 assert qa['bundle_review_sha256']==digest('.agent/validator/114-test-bundle-review.json')
 spec=importlib.util.spec_from_file_location('capture114_checker',ROOT/(E+'check_114.py')); checker=importlib.util.module_from_spec(spec); spec.loader.exec_module(checker)
 checker.integrity(ROOT,source,fixed)
 assert hashlib.sha256(checker.git(ROOT,'show',candidate+':.agent/validator/114-test-bundle-review.json')).hexdigest()==qa['bundle_review_sha256']
 expected=[E+'qa-%02d.txt'%i for i in range(1,13)]
 for test,actual,path in zip(contract['verification'],qa['checks'],expected):
  assert actual['command']==test['command'] and actual['evidence']==path and actual['exit_code']==0
  receipt(path,test['command'],candidate)
 spot=E+'114-qa-adversarial.txt'; own=qa['adversarial']
 assert own['performed'] is True and own['evidence']==spot and own['command'] not in [x['command'] for x in contract['verification']]
 receipt(spot,own['command'],candidate)
 assert len(qa['evidence_files'])==13 and set(qa['evidence_files'])==set(expected+[spot])
 assert semantic['evidence'] and all(raw(p).strip() for p in semantic['evidence'])
 print('EVIDENCE GATE PASS: feature114 actual sealed candidate;12 independent checks, semantic review and ownspot; existing fixed/source Git bytes and modes verified before canonical closure.')
if __name__=='__main__': main()
