"""Data-only debt projection; creates no QA, seal or evidence-capture artifact."""
def resolved_debt(text):
    from datetime import date
    import re
    text=text.replace('version: 0.64.0','version: 0.65.0',1)
    log='  - version: "0.65.0"\n    date: "2026-10-12"\n    summary: "CONTROL ONLY: model verified050 resolution; no actual gate claimed."\n'
    text=text.replace('change_log:\n','change_log:\n'+log,1)
    row=next(line for line in text.splitlines() if line.startswith('| NDEBT-050 |'))
    text=text.replace(row+'\n','',1)
    parts=row.split('|')
    parts[5]=parts[5].rstrip()+' RESOLVED CONTROL ONLY after modeled gates: .agent/evidence/113/evidence-gate.txt; these are data-only expectations, no real acceptance claim. '
    row='|'.join(parts)
    header='## Resolved\n\n| ID | Date | Severity | Description | Notes |\n|----|------|----------|-------------|-------|\n'
    assert header in text
    return text.replace(header,header+row+'\n',1)
