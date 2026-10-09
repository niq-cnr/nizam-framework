python3 -c "s=open('tools/README.md').read().split('## Machine Validation')[1].split('\n## ')[0]; miss=[k for k in ('--allow-unsupported-isolation','CONFORMANCE: NOT FULL','CONFORMANCE: FULL','UNSUPPORTED') if k not in s]; assert not miss, miss"
EXIT:0
