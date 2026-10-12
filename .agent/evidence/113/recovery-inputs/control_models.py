"""Data-only debt projection; creates no QA, seal or evidence-capture artifact."""
import re
import copy


def table(lines, section, last_column):
    """Locate the actual table, preserving its header, separator and rows."""
    headings=[i for i,line in enumerate(lines) if line.rstrip('\n')=='## '+section]
    assert len(headings)==1, 'CONTROL_TABLE_SECTION:'+section
    start=headings[0]+1
    end=next((i for i in range(start,len(lines)) if lines[i].startswith('## ')),len(lines))
    content=[i for i in range(start,end) if lines[i].strip()]
    assert len(content)>=3, 'CONTROL_TABLE_CONTENT:'+section
    header,separator,first_row=content[:3]
    cells=lambda line:[value.strip() for value in line.strip().split('|')[1:-1]]
    assert cells(lines[header])==['ID','Date','Severity','Description',last_column], 'CONTROL_TABLE_COLUMNS:'+section
    separators=cells(lines[separator])
    assert len(separators)==5 and all(re.fullmatch(r':?-{3,}:?',value) for value in separators), 'CONTROL_TABLE_SEPARATOR:'+section
    assert lines[first_row].startswith('| NDEBT-'), 'CONTROL_TABLE_FIRST_ROW:'+section
    return first_row,end


def resolved_debt(text):
    # Frontmatter and table interfaces differ: Open has Notes, Resolved has
    # Resolution. Locate both structurally rather than replacing header bytes.
    lines=text.splitlines(keepends=True)
    delimiters=[i for i,line in enumerate(lines) if line=='---\n']
    assert len(delimiters)==2 and delimiters[0]==0, 'CONTROL_FRONTMATTER'
    front_end=delimiters[1]
    versions=[i for i in range(1,front_end) if lines[i].startswith('version: ')]
    logs=[i for i in range(1,front_end) if lines[i]=='change_log:\n']
    assert len(versions)==len(logs)==1 and lines[versions[0]]=='version: 0.64.0\n', 'CONTROL_VERSION_LOG_INTERFACE'
    open_start,open_end=table(lines,'Open','Notes')
    table(lines,'Resolved','Resolution')
    rows=[i for i,line in enumerate(lines) if line.startswith('| NDEBT-050 |')]
    assert len(rows)==1 and open_start<=rows[0]<open_end, 'CONTROL050_OPEN_ROW'
    row=lines[rows[0]].rstrip('\n');parts=row.split('|')
    assert len(parts)==7 and not parts[0] and not parts[-1], 'CONTROL050_ROW_FIELDS'
    parts[5]=parts[5].rstrip()+' RESOLVED CONTROL ONLY after modeled gates: .agent/evidence/113/evidence-gate.txt; these are data-only expectations, no real acceptance claim. '
    del lines[rows[0]]
    first_resolved,_=table(lines,'Resolved','Resolution')
    lines.insert(first_resolved,'|'.join(parts)+'\n')
    lines[versions[0]]='version: 0.65.0\n'
    log='  - version: "0.65.0"\n    date: "2026-10-12"\n    summary: "CONTROL ONLY: model verified050 resolution; no actual gate claimed."\n'
    lines.insert(logs[0]+1,log)
    return ''.join(lines)


def stage_records(c, features, phase, state, status):
    """CONTROL record projection only; no verdict/evidence artifact is created."""
    features,phase,state=copy.deepcopy((features,phase,state))
    row=next(x for x in features['features'] if x['id']=='113')
    step=next(x for x in phase['steps'] if x['id']=='113')
    for key in ('blocked_reason','completed_at','qa'):row.pop(key,None)
    for key in ('docs_updated','changelog_entry'):step.pop(key,None)
    row.update(status=status,passes=status=='complete',contract_ref='.agent/contracts/113.json')
    step['status']={'blocked':'BLOCKED','in_progress':'IN_PROGRESS','complete':'COMPLETED'}[status]
    state['status']='blocked' if status=='blocked' else 'in_progress'
    state['current_feature']='113'
    if status=='blocked':
        frozen=next(x for x in c.js(c.RECOVERY,'features.json')['features'] if x['id']=='113')
        row['blocked_reason']=frozen['blocked_reason']
    if status=='complete':
        row.update(completed_at='CONTROL_ONLY',qa='.agent/qa/113.json',evidence='.agent/evidence/113/evidence-gate.txt')
        step.update(evidence='.agent/evidence/113/evidence-gate.txt',docs_updated='CONTROL_ONLY',changelog_entry='CONTROL_ONLY')
    else:
        row['evidence']=step['evidence']='.agent/evidence/113/circuit-breaker-halt.json'
    return features,phase,state


def lifecycle_control(c, root):
    """Validate actual scratch data and three model origins without gate claims."""
    features=c.js(root,c.COORDINATION[0])
    phase=c.yaml.safe_load(c.read(root,c.COORDINATION[1]))
    state=c.js(root,c.COORDINATION[2])
    c.lifecycle_data(features,phase,state)
    c.require(c.js(root,'.agent/contracts/113.json')==c.contract(),'APPROVED_CONTRACT_IMMUTABLE')
    original=c.read(c.RECOVERY,'debt-original.md');halt=c.read(c.HERE,'recovery-debt-halt.md')
    recovered=c.read(c.RECOVERY,'debt-recovery.md')
    c.debt_text(original,halt,recovered,c.read(root,'docs/planning/DEBT.md'),allow_resolved=True)
    for status in ('blocked','in_progress','complete'):
        records=stage_records(c,features,phase,state,status)
        c.lifecycle_data(*records,completion=status=='complete')
        debt=resolved_debt(recovered) if status=='complete' else recovered
        c.debt_text(original,halt,recovered,debt,allow_resolved=status=='complete')
        print('CONTROL_LIFECYCLE_DATA_ORIGIN:'+status+':PASS; no production gate assumed')
