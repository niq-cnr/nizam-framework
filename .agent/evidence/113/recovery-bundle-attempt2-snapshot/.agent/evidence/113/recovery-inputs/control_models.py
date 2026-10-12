"""Data-only debt projection; creates no QA, seal or evidence-capture artifact."""
import re


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
