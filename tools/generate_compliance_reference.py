#!/usr/bin/env python3
"""Generate or check compliance summaries against the actual validator sources."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
START = '<!-- BEGIN GENERATED COMPLIANCE CONTROLS -->'
END = '<!-- END GENERATED COMPLIANCE CONTROLS -->'
HELP_START = '  # BEGIN GENERATED COMPLIANCE CONTROLS'
HELP_END = '  # END GENERATED COMPLIANCE CONTROLS'


def load_and_validate(root: Path):
    data = json.loads((root / 'tools/compliance_checks.json').read_text(encoding='utf-8'))
    validator = (root / 'tools/validate.sh').read_text(encoding='utf-8')
    controls = data['controls']
    if not isinstance(controls, list) or not controls:
        raise ValueError('empty or invalid control inventory')
    ids = [item['id'] for item in controls]
    if len(set(ids)) != len(ids) or any(not re.fullmatch(r'C[1-9][0-9]*', ident) for ident in ids):
        raise ValueError('duplicate or invalid control ID')
    if ids != sorted(ids, key=lambda x: int(x[1:])):
        raise ValueError('control IDs are not in numeric order')
    reserved = [r['id'] for r in data['reserved']]
    if len(set(reserved)) != len(reserved) or set(ids) & set(reserved):
        raise ValueError('reserved control allocated or repeated')
    emitted = {'C' + n for n in re.findall(r'\[C([1-9][0-9]*)\]', validator)}
    defined = {'C' + n for n in re.findall(r'^check_c([1-9][0-9]*)_\w+\(\)', validator, re.M)}
    if set(ids) != emitted or set(ids) != defined:
        raise ValueError('registry IDs differ from emitted or implemented controls')
    main = validator[validator.index('main() {'):]
    payload_start = main.index('  elif [ "${VALIDATOR_MODE}" = "payload" ]; then')
    payload_end = main.index('    echo "SUMMARY (payload mode):', payload_start)
    payload_body = main[payload_start:payload_end]
    payload_actual = {}
    for line in payload_body.splitlines():
        match = re.search(r'\[C([1-9][0-9]*)\] (SKIP|OUT_OF_SCOPE)', line)
        if match:
            payload_actual['C' + match.group(1)] = {'SKIP': 'skipped', 'OUT_OF_SCOPE': 'out-of-scope'}[match.group(2)]
            continue
        match = re.search(r'\bcheck_c([1-9][0-9]*)_([a-z_]+)', line)
        if match:
            payload_actual['C' + match.group(1)] = 'not-applicable' if match.group(2).endswith('payload_skip') else 'exercised'
    if set(payload_actual) != set(ids):
        raise ValueError('payload dispatch differs from registry IDs')
    default_start = main.index('  else\n    local shipped_md=()', payload_end)
    default_end = main.index('    echo "SUMMARY:', default_start)
    default_body = main[default_start:default_end]
    default_calls = set(re.findall(r'\b(check_c[1-9][0-9]*_[a-z_]+)\b', default_body))
    for item in controls:
        if item['source_check'] not in default_calls:
            raise ValueError(f"{item['id']}: default dispatch omits source check")
    target_start = main.index('  if [ "${VALIDATOR_MODE}" = "target" ]; then')
    target_body = main[target_start:payload_start]
    target_sets = {}
    for extension in ('md', 'json', 'html'):
        match = re.search(r'\*\.' + extension + r'\)\s*([\s\S]*?)\n\s*;;', target_body)
        if not match:
            raise ValueError('target dispatch branch is missing: ' + extension)
        target_sets[extension] = set(re.findall(r'\bcheck_c([1-9][0-9]*)_', match.group(1)))
    # JSON target routes through a discriminator; inspect actual dispatched checks.
    if 'check_c11_or_c4_target' not in target_body:
        raise ValueError('JSON target dispatcher is missing')
    dispatcher = validator[validator.index('check_c11_or_c4_target() {'):validator.index('check_c14_workflow_pins() {')]
    target_sets['json'] = set(re.findall(r'\bcheck_c([1-9][0-9]*)_(?:index|dogfood_target|target|feature_list_target)', dispatcher))
    for item in controls:
        number = item['id'][1:]
        extensions = {extension for extension, numbers in target_sets.items() if number in numbers}
        if extensions == {'md'}:
            target_actual = 'markdown'
        elif extensions == {'md', 'html'}:
            target_actual = 'markdown and html'
        elif extensions == {'json'}:
            target_actual = {'4': 'json fallback', '16': 'feature-list json schema only'}.get(number, 'routed json')
        elif not extensions:
            target_actual = 'none'
        else:
            raise ValueError(f"{item['id']}: unsupported target dispatch")
        if item['modes']['target'] != target_actual:
            raise ValueError(f"{item['id']}: target mode differs from validator dispatch")
    for item in controls:
        ident = item['id']
        name = item['source_check']
        if item['status'] != 'active' or not item['name'] or not item['purpose']:
            raise ValueError(f'{ident}: retired, missing name or purpose')
        if not re.fullmatch('check_c' + ident[1:] + r'_[a-z_]+', name):
            raise ValueError(f'{ident}: mislabelled source check')
        if not re.search(r'^' + re.escape(name) + r'\(\) \{', validator, re.M):
            raise ValueError(f'{ident}: source check not found')
        modes = item['modes']
        if set(modes) != {'default', 'target', 'payload'} or modes['default'] != 'exercised':
            raise ValueError(f'{ident}: invalid applicability')
        if modes['target'] not in {'none', 'markdown', 'json fallback', 'routed json',
                                   'markdown and html', 'feature-list json schema only'}:
            raise ValueError(f'{ident}: invalid target mode')
        if modes['payload'] != payload_actual[ident]:
            raise ValueError(f'{ident}: payload mode differs from validator dispatch')
    return data


def markdown_table(data):
    lines = [START, '| Check | Purpose | Default | Target | Payload |', '| :--- | :--- | :--- | :--- | :--- |']
    for c in data['controls']:
        m = c['modes']
        lines.append(f"| {c['id']} | {c['purpose']} | {m['default']} | {m['target']} | {m['payload']} |")
    return '\n'.join(lines + [END])


def help_summary(data):
    lines = [HELP_START, '  Control inventory (default / target / payload):']
    for c in data['controls']:
        m = c['modes']
        lines.append(f"  {c['id']}: {c['name']} — {m['default']} / {m['target']} / {m['payload']}")
    return '\n'.join(lines + [HELP_END])


def replace_block(content, begin, end, rendered):
    if content.count(begin) != 1 or content.count(end) != 1:
        raise ValueError(f'expected exactly one generated block: {begin}')
    start = content.index(begin)
    finish = content.index(end, start) + len(end)
    return content[:start] + rendered + content[finish:]


def render_files(root: Path, data):
    result = {}
    for name in ('README.md', 'tools/README.md'):
        path = root / name
        result[name] = replace_block(path.read_text(encoding='utf-8'), START, END, markdown_table(data))
    path = root / 'tools/validate.sh'
    result['tools/validate.sh'] = replace_block(path.read_text(encoding='utf-8'), HELP_START, HELP_END,
                                                 help_summary(data))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Check parity without writing files.')
    args = parser.parse_args()
    try:
        data = load_and_validate(ROOT)
        expected = render_files(ROOT, data)
        stale = [name for name, content in expected.items() if (ROOT / name).read_text(encoding='utf-8') != content]
        if args.check:
            if stale:
                raise ValueError('generated summaries differ: ' + ', '.join(stale))
            print(f"compliance reference: {len(data['controls'])} controls; generated summaries match")
        else:
            for name in stale:
                (ROOT / name).write_text(expected[name], encoding='utf-8')
            print('generated compliance summaries: ' + (', '.join(stale) if stale else 'unchanged'))
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f'compliance reference: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
