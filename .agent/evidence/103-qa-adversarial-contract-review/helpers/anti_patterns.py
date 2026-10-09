#!/usr/bin/env python3
"""Static scan of the 24 contract commands for 02 section 10 anti-patterns and testability hazards."""
import json, re
c = json.load(open('.agent/contracts/103.json'))
ats = 0; sups = 0
for v in c['verification']:
    if v.get('supplementary'): sups += 1; n = 'S%02d' % sups
    else: ats += 1; n = 'AT%d' % ats
    cmd = v['command']
    findings = []
    if re.search(r'^[^#\n]*\|\s*(grep|tail|head|tee|sed|awk|wc|cut)\b', cmd, re.M): findings.append('pipeline into filter (exit swallowed?)')
    if re.search(r'\|\|\s*(true|:)', cmd): findings.append('|| true')
    if re.search(r'2>&1\s*\|', cmd): findings.append('2>&1 |')
    if re.search(r'\bcurl\b|\bwget\b|https?://|socket\.|\bgh\b', cmd): findings.append('network use')
    if re.search(r'\btime\.sleep\b|datetime\.now|time\.time\(', cmd): findings.append('wall-clock use')
    if re.search(r'(?<!\w)/home/|/tmp/', cmd): findings.append('absolute path')
    if re.search(r'os\.chdir|\bcd\b ', cmd): findings.append('chdir')
    exits = bool(re.search(r'sys\.exit|SystemExit|assert |test \$\? -eq 0|^git diff --exit-code|^python3 \.agent', cmd, re.M))
    sw = re.findall(r'except[^\n]*:\s*(?:pass|continue)\b', cmd)
    print('%-5s exit-signalled=%s findings=%s bare-except-pass=%d len=%d' % (n, exits, findings or '-', len(sw), len(cmd)))
