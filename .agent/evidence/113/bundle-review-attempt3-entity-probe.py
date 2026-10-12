#!/usr/bin/env python3
"""Independent reviewer3 scratch probe: HTML href single-decode boundary."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit
import argparse, tempfile, shutil, importlib.util, subprocess, json
parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=Path('.'));args=parser.parse_args();root=args.root.resolve()
spec=importlib.util.spec_from_file_location('controls',root/'.agent/evidence/113/private/controls.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
print('PREREGISTERED: HTML anchor href="..&amp;#47;tools/interface.md" decodes once to ..&#47;tools/interface.md, whose URL path is ..& and fragment47;tools/interface.md; it is not the required target. Expect routing exit1 DOCUMENT_INTERFACE_LINK and bounded_delta exit1 SBCL_BOUNDED_LINK. Evidence budget; scratch component proof only.')
markup='<a href="..&amp;#47;tools/interface.md">adapter interface</a>'
class Attribute(HTMLParser):
    def handle_starttag(self,tag,attrs):
        if tag=='a':self.href=dict(attrs)['href']
a=Attribute(convert_charrefs=False);a.feed(markup);parts=urlsplit(a.href)
print('INDEPENDENT_SINGLE_PARSE_ATTRIBUTE',repr(a.href),'URL_PATH',repr(parts.path),'URL_FRAGMENT',repr(parts.fragment))
print('CHECKER_HREFS',json.dumps(m.c.rendered_hrefs(markup)))
with tempfile.TemporaryDirectory(prefix='nizam113-controls-reviewer-entity-') as tmp:
    scratch=Path(tmp)/'repo';shutil.copytree(root,scratch,ignore=shutil.ignore_patterns('.git','__pycache__'));m.fixture(scratch)
    for name,func in [('routing',m.c.routing),('bounded_delta',m.c.bounded_delta)]:func(scratch);print('POSITIVE',name,'EXIT0')
    p=scratch/'methodology/11_sbcl_runtime_binding.md';before=p.read_text();needle='[adapter interface](..&#47;tools/interface.md)';assert before.count(needle)==1
    p.write_text(before.replace(needle,markup))
    for name,func in [('routing',m.c.routing),('bounded_delta',m.c.bounded_delta)]:
        try:func(scratch);rc=0;message='PASS'
        except m.c.Failure as error:rc=1;message=str(error)
        print('ACTUAL NEGATIVE',name,'EXIT'+str(rc),message)
    p.write_text(before);m.c.routing(scratch);m.c.bounded_delta(scratch);print('RESTORED positive EXIT0')
