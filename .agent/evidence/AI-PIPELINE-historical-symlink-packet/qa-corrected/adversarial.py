from pathlib import Path
import subprocess,importlib.util,json,hashlib,os,tempfile
root=Path(__file__).parent;framework=root/'repo';scratch=Path(tempfile.mkdtemp(prefix='hostile-inert-target-',dir=root));repo=scratch/'repo';repo.mkdir();marker=scratch/'shell-marker';fifo=scratch/'outside-fifo';os.mkfifo(fifo)
spec=importlib.util.spec_from_file_location('source_review_probe',framework/'tools/convergent_review.py');cr=importlib.util.module_from_spec(spec);spec.loader.exec_module(cr)
def git(*args,data=None):return subprocess.check_output(['git','-C',str(repo),*args],input=data).decode().strip()
git('init','-q','--template=');git('config','user.name','Independent Evaluator');git('config','user.email','evaluator@example.test');git('config','commit.gpgsign','false')
target=('%PDF-../../$(touch '+str(marker)+');<script>\u2028</script>').encode();oid=git('hash-object','-w','--stdin',data=target);git('update-index','--add','--cacheinfo','120000,'+oid+',link');git('commit','-qm','hostile-looking immutable link');base=git('rev-parse','HEAD');git('update-index','--force-remove','link');git('commit','-qm','delete link');head=git('rev-parse','HEAD');(repo/'link').symlink_to(fifo)
assert not marker.exists();records=[]
for version in ('1.0.0','1.1.0','auto'):
 for mode in ('ordinary','full_audit'):
  p=cr.build_packet_from_git(repo,'example/repo','independent-shell-looking-link',mode,base,head,packet_version=version);cr.validate_packet(p);item=p['delta'][0];assert item['old_content'].encode()==target and item['old_digest']==hashlib.sha256(target).hexdigest() and item['old_mode']=='120000';assert not marker.exists();assert os.readlink(repo/'link')==str(fifo);records.append({'version':version,'mode':mode,'digest':item['old_digest']})
# Same target as a current candidate must still be refused.
git('update-index','--add','--cacheinfo','120000,'+oid+',link');git('commit','-qm','unsafe current candidate');unsafe=git('rev-parse','HEAD')
try:cr.build_packet_from_git(repo,'example/repo','independent-candidate-control','ordinary',head,unsafe)
except cr.ReviewError as exc:
 assert 'new blob' in str(exc) and 'symlink' in str(exc);refusal=str(exc)
else:raise AssertionError('unsafe current target unexpectedly accepted')
assert not marker.exists();print(json.dumps({'scenario':'One evaluator-originated adversarial spot-check: immutable historical media/shell-looking target versus FIFO worktree drift, then unsafe candidate control.','positive_variants':records,'shell_marker_created':marker.exists(),'worktree_link_unchanged':os.readlink(repo/'link')==str(fifo),'candidate_refusal':refusal,'scratch_root':str(scratch)},indent=2))
