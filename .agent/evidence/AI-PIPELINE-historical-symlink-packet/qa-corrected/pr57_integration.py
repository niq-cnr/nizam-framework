from pathlib import Path
import subprocess,importlib.util,json,hashlib
root=Path(__file__).parent;framework=root/'repo';hermes=Path('/home/cnross/code/nizamiq/hermes-config');base='4301be610bc0c673bd08cc3daf1e79e8ee99c995';head='c06a03b20903598a050c8416557f1cf9b88173c1'
spec=importlib.util.spec_from_file_location('source_review',framework/'tools/convergent_review.py');cr=importlib.util.module_from_spec(spec);spec.loader.exec_module(cr)
def git(*args):return subprocess.check_output(['git','-C',str(hermes),'--no-replace-objects','--literal-pathspecs',*args])
expected={p.decode() for p in git('diff','--no-renames','--name-only','-z',base,head).split(b'\0') if p};assert len(expected)==306
old_path='skills/typesafe-ai';meta,_=git('ls-tree','-z',base,'--',old_path).split(b'\t',1);old_mode,kind,old_oid=meta.decode().split();old_raw=git('cat-file','blob',old_oid);assert old_mode=='120000' and old_raw==b'../../.agents/skills/typesafe-ai'
assert git('ls-tree','-z',head,'--',old_path)==b''
records=[]
for mode in ('ordinary','full_audit'):
 packet=cr.build_packet_from_git(hermes,'nizamiq/hermes-config','pr57-complete-source-qa',mode,base,head,packet_version='auto');cr.validate_packet(packet)
 actual={x['path'] for x in packet['delta']};assert actual==expected,(len(actual),sorted(expected-actual),sorted(actual-expected))
 item=next(x for x in packet['delta'] if x['path']==old_path);assert item['old_mode']==old_mode and item['old_content'].encode()==old_raw and item['old_digest']==hashlib.sha256(old_raw).hexdigest() and item['new_digest'] is None and item['new_mode'] is None
 if packet['schema_version']=='1.1.0':assert item['old_object_id']==old_oid and item['old_byte_length']==len(old_raw) and item['change_kind']=='deleted'
 tomb=next(x for x in packet['review_files'] if x['path']==old_path);assert tomb['content'] is None and tomb['content_digest']==hashlib.sha256(b'').hexdigest()
 raw=cr.canonical_json_bytes(packet);dest=root/('pr57-'+mode+'.packet.json');dest.write_bytes(raw)
 records.append({'mode':mode,'version':packet['schema_version'],'changed_paths':len(actual),'review_files':len(packet['review_files']),'packet_path':str(dest),'packet_sha256':hashlib.sha256(raw).hexdigest(),'packet_bytes':len(raw),'historical_path':old_path,'old_mode':old_mode,'old_blob_oid':old_oid,'old_digest':item['old_digest'],'old_content':item['old_content'],'new_mode':item['new_mode'],'new_digest':item['new_digest']})
print(json.dumps({'framework_candidate':'aaca37cc4575306f433c300c40aed038e4552a8f','upstream_repository':str(hermes),'base_sha':base,'head_sha':head,'complete_expected_paths':sorted(expected),'packets':records,'adoption_claim':False},indent=2))
