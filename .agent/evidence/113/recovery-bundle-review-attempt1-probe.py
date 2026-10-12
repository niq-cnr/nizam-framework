#!/usr/bin/env python3
"""Reviewer-owned preregistered scratch probes; evidence only, no gates fabricated."""
from pathlib import Path
import argparse, tempfile, shutil, importlib.util, json
from html.parser import HTMLParser
from urllib.parse import urlsplit
parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True);args=parser.parse_args();root=args.root.resolve()
spec=importlib.util.spec_from_file_location('controls',root/'.agent/evidence/113/private/controls.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
PLAN=[
 ('prior-comment-only','<!-- [adapter interface](..&#47;tools/interface.md) -->',1),
 ('prior-html-double-entity','<a href="..&amp;#47;tools/interface.md">adapter interface</a>',1),
 ('independent-html-double-percent','<a href="..%252Ftools%252Finterface.md">adapter interface</a>',1),
 ('independent-script-across-blank-lines','<script>\n\n<a href="..&#47;tools/interface.md">adapter interface</a>\n\n</script>',1),
 ('independent-commented-anchor-across-lines','<!--\n\n<a href="..&#47;tools/interface.md">adapter interface</a>\n\n-->',1),
 ('independent-html-decoded-fragment','<a href="..&#47;tools/interface.md&#35;ignored">adapter interface</a>',1),
 ('independent-html-named-slash','<a href="..&sol;tools/interface.md">adapter interface</a>',0),
 ('independent-markdown-angle-destination','[adapter interface](<..&#x2f;tools/interface.md>)',0),
]
for name,markup,expected in PLAN:
 print('PREREGISTERED',json.dumps({'name':name,'markup':markup,'routing_exit':expected,'delta_exit':expected,'routing_diagnostic':'DOCUMENT_INTERFACE_LINK:methodology/11_sbcl_runtime_binding.md' if expected else 'PASS','delta_diagnostic':'SBCL_BOUNDED_LINK' if expected else 'PASS','scope':'SCRATCH COMPONENT CONTROL ONLY'},sort_keys=True),flush=True)
class Attribute(HTMLParser):
 def handle_starttag(self,tag,attrs):
  if tag=='a':self.href=dict(attrs)['href']
a=Attribute(convert_charrefs=False);a.feed(PLAN[1][1]);u=urlsplit(a.href)
print('INDEPENDENT_HTML_ATTRIBUTE_SINGLE_DECODE',repr(a.href),'PATH',repr(u.path),'FRAGMENT',repr(u.fragment),flush=True)
with tempfile.TemporaryDirectory(prefix='nizam113-recovery-independent-review-probe-') as tmp:
 scratch=Path(tmp)/'repo';shutil.copytree(root,scratch,ignore=shutil.ignore_patterns('.git','__pycache__'));m.fixture(scratch)
 p=scratch/'methodology/11_sbcl_runtime_binding.md';original=p.read_bytes();needle='[adapter interface](..&#47;tools/interface.md)';assert p.read_text().count(needle)==1
 for name,func in [('routing',m.c.routing),('delta',m.c.bounded_delta)]:func(scratch);print('BASELINE',name,'EXIT0',flush=True)
 for name,markup,expected in PLAN:
  p.write_text(original.decode().replace(needle,markup))
  try:
   for component,func,diagnostic in [('routing',m.c.routing,'DOCUMENT_INTERFACE_LINK:methodology/11_sbcl_runtime_binding.md'),('delta',m.c.bounded_delta,'SBCL_BOUNDED_LINK')]:
    try:func(scratch);actual=0;message='PASS'
    except m.c.Failure as error:actual=1;message=str(error)
    print('ACTUAL',name,component,'EXIT'+str(actual),message,flush=True)
    assert actual==expected and (not expected or diagnostic==message),(name,component,actual,message)
  finally:p.write_bytes(original)
  for component,func in [('routing',m.c.routing),('delta',m.c.bounded_delta)]:func(scratch);print('RESTORED',name,component,'EXIT0',flush=True)
print('INDEPENDENT_PROBES:PASS; scratch only; no production gate authored')
