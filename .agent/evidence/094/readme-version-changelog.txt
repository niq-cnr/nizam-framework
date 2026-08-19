$ python3 -c "import yaml; ... assert version==0.15.0 ... assert change_log[0].version==0.15.0" && grep -Fq dod_ref schema/README.md
PASS schema/README.md version+change_log
grep_rc=0
EXIT:0
