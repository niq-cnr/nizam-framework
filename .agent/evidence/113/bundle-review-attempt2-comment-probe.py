#!/usr/bin/env python3
"""Replay reviewer2 comment-only href probe; scratch component proof only."""
from pathlib import Path
import argparse, tempfile, shutil, importlib.util, subprocess, json
parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=Path('.'));args=parser.parse_args()
root=args.root.resolve()
spec=importlib.util.spec_from_file_location('controls',root/'.agent/evidence/113/private/controls.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
print('COMMAND: PYTHONDONTWRITEBYTECODE=1 python3 .agent/evidence/113/bundle-review-attempt2-comment-probe.py --root .')
print('EXERCISED_REVISION:',subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip())
print('PREREGISTERED: comment-only required interface href; expected routing rejection DOCUMENT_INTERFACE_LINK:methodology/11_sbcl_runtime_binding.md; evidence budget; scratch only')
with tempfile.TemporaryDirectory(prefix='nizam113-controls-reviewer-comment-') as tmp:
    scratch=Path(tmp)/'repo';shutil.copytree(root,scratch,ignore=shutil.ignore_patterns('.git','__pycache__'));m.fixture(scratch)
    for name,func in [('routing',m.c.routing),('bounded_delta',m.c.bounded_delta)]:
        func(scratch);print('POSITIVE',name,'EXIT0')
    p=scratch/'methodology/11_sbcl_runtime_binding.md';before=p.read_text();needle='[adapter interface](..&#47;tools/interface.md)';assert before.count(needle)==1
    p.write_text(before.replace(needle,'<!-- '+needle+' -->'))
    print('HELPER rendered_hrefs='+json.dumps(m.c.rendered_hrefs(m.c.doc(scratch,'methodology/11_sbcl_runtime_binding.md')[1])))
    rejected=[]
    for name,func in [('routing',m.c.routing),('bounded_delta',m.c.bounded_delta)]:
        try:func(scratch);rc=0;message='PASS'
        except m.c.Failure as error:rc=1;message=str(error)
        print('ACTUAL NEGATIVE',name,'EXIT'+str(rc),message);rejected.append(rc==1)
    p.write_text(before);m.c.routing(scratch);m.c.bounded_delta(scratch);print('RESTORED positive EXIT0')
print('COMMENT_ONLY_REJECTED:',all(rejected))
