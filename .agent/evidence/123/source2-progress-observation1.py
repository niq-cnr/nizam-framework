"""Root-requested read-only progress snapshot; no product imports or recursive census."""
from pathlib import Path
import datetime,json,os,subprocess,tempfile
print(json.dumps(dict(observed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),kind='Read-only progress, not semantic outcome, stall diagnosis or benchmark')))
print(json.dumps(dict(kind='Original result transcription; original exact command not retained in repository',original_wall_time='not recorded',original_tool_exits=[0,0,0],tool_chunks=['c5c564','f3c2ad','66e425'],original_test_elapsed_seconds=1526.55,parser_parent='/home/cnross/.tmp/nizam123-SYNTHETIC-parser-r6iv3zr1',first_census=dict(direct_children=5,recursive_files=49669,recursive_directories=1539,lstat_bytes=774159859),later_split=dict(root_files=49832,root_lstat_bytes=768463467,experiment_files=375,experiment_lstat_bytes=13274827),later_restoration_commit_count=93,limit='Separate observations while fixture was active; counts are not an atomic snapshot or completed-selector claim')))
pid=1797490;records={};uptime=float(Path('/proc/uptime').read_text().split()[0])
for name in os.listdir('/proc'):
 if not name.isdigit():continue
 try:
  root=Path('/proc')/name;fields=(root/'stat').read_text().rsplit(')',1)[1].split()
  records[int(name)]=dict(pid=int(name),ppid=int(fields[1]),elapsed_seconds=round(uptime-int(fields[19])/os.sysconf('SC_CLK_TCK'),2),argv=[x.decode(errors='replace') for x in (root/'cmdline').read_bytes().split(b'\0') if x],cwd=os.readlink(root/'cwd'))
 except (FileNotFoundError,ProcessLookupError,PermissionError):pass
if pid in records:
 assert records[pid]['argv']==['python3','tools/test_workflow_assurance.py','--case','ci-candidate-bound']
 assert records[pid]['cwd']=='/home/cnross/.tmp/nizam-feature123-source2'
 selected={pid}
 while True:
  extra={p for p,r in records.items() if r['ppid'] in selected}-selected
  if not extra:break
  selected|=extra
 print(json.dumps(dict(parent=records.get(records[pid]['ppid']),test=records[pid],active_descendants=[records[p] for p in sorted(selected-{pid})][:8])))
else:print(json.dumps(dict(test_pid=pid,proc_present=False,meaning='No semantic completion inferred; wrapper owns actual outcome')))
base=Path(tempfile.gettempdir())
for prefix in ['nizam123-SYNTHETIC-parser-','nizam123-SYNTHETIC-variant-']:
 parents=sorted(base.glob(prefix+'*'),key=lambda p:p.stat().st_ctime,reverse=True)
 if parents:
  parent=parents[0];print(json.dumps(dict(path=str(parent),direct_children=sorted(p.name for p in parent.iterdir()),recursive_census='not repeated')))
  root=parent/'root'
  if (root/'.git').exists():
   argv=['git','-C',str(root),'log','-3','--format=%H %s'];p=subprocess.run(argv,capture_output=True)
   print(json.dumps(dict(argv=argv,actual_exit=p.returncode,stdout=p.stdout.decode(errors='replace')[:1800],stderr=p.stderr.decode(errors='replace')[:300])))
