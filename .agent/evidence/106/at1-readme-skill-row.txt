python3 -c "L=[l for l in open('tools/README.md') if l.startswith('| [\x60skill.json\x60]')]; assert len(L)==1 and 'intentional subset' in L[0] and 'NIZAM.json' in L[0], L"
EXIT:0
