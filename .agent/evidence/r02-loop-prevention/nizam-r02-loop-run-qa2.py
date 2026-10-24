import os,sys,json,subprocess,hashlib,concurrent.futures
from pathlib import Path
root=Path('/home/cnross/.tmp/nizam-r02-loop-qa2');sys.path.insert(0,str(root/'tools'))
import start_path as sp,workflow_assurance as wa
os.environ['XDG_CACHE_HOME']='/home/cnross/.tmp/nizam-r02-loop-qa2-cache'
files=subprocess.check_output(['git','ls-files','-z'],cwd=root).decode().split('\0');files=[x for x in files if x]
selected={'source':[],'contracts':['.agent/evidence/r02-loop-prevention/change-brief.json'],'tests':['tools/test_start_path.py','tools/test_workflow_assurance.py','tools/test_convergent_review.py'],'tools':['tools/start_path.py','tools/workflow_assurance.py','tools/validate.sh']}
used=set(sum(selected.values(),[]));selected['source']=[x for x in files if x not in used]
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root).decode().strip()
selected['unknown_dependencies']=[]
candidate=wa.assess_repository(root,head,selected,['GIT_CONFIG_GLOBAL','PYTHONDONTWRITEBYTECODE','XDG_CACHE_HOME'])
out=root/'.agent/evidence/r02-loop-prevention/root-qa-attempt2';out.mkdir(parents=True)
(out/'candidate.json').write_text(json.dumps(candidate,indent=2)+'\n')
commands={'start-path':['python','tools/test_start_path.py'],'workflow-assurance':['python','tools/test_workflow_assurance.py'],'compliance':['bash','tools/validate.sh'],'isolation':['python','tools/test_convergent_review.py']}
def run(item):
 step,argv=item
 cap=sp.capture_command_evidence(root,task_id='r02-loop-prevention',step=step,attempt=2,output_dir=out,argv=argv,candidate_sha256=candidate,timeout_sec=1200)
 print(json.dumps({'step':step,'exit_code':cap['exit_code'],'capture':cap['capture_path']}),flush=True)
 return step,cap
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 results=dict(pool.map(run,commands.items()))
wa._receipt_candidate(root,candidate)
result={'candidate_commit':head,'checks':{k:{'exit_code':v['exit_code'],'capture_path':v['capture_path']} for k,v in results.items()},'passed':all(x['exit_code']==0 for x in results.values()),'candidate_revalidated':True}
(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
sys.exit(0 if result['passed'] else 1)
