#!/usr/bin/env python3
"""Independent feature113 acceptance. Private controls are development proof only.

Expected values come from the approved contract, accepted NIP3, existing schemas,
and immutable pre-source snapshots. Text checks require later independent source
review; they cannot prove consumer runtime behavior.
"""
import copy
import hashlib
import html
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
from urllib.parse import unquote, urlsplit

import yaml

HERE = Path(__file__).resolve().parent
PRIVATE = HERE / 'private'
BASE = PRIVATE / 'base'
RECOVERY = HERE / 'recovery-inputs'
ROOT = Path.cwd().resolve()
PRODUCT = ('tools/interface.md', 'tools/skill.json', 'tools/SKILL.md', 'NIZAM.json',
           'tools/README.md', 'methodology/10_live_runtime_sessions.md',
           'methodology/11_sbcl_runtime_binding.md', 'CHANGELOG.md')
COORDINATION = ('.agent/feature_list_015.json', 'docs/planning/phase_015.yaml', '.agent/run_state.json')
MODES = ('surface', 'routing', 'compatibility', 'scope-history', 'lifecycle',
         'negative-controls', 'claim-boundary', 'input-integrity')


class Failure(Exception):
    pass


def require(value, diagnostic):
    if not value:
        raise Failure(diagnostic)


def read(root, path):
    p = root / path
    require(p.is_file() and not p.is_symlink(), 'MISSING_OR_SYMLINK:' + path)
    return p.read_text()


def js(root, path):
    return json.loads(read(root, path))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(root, *args):
    p = subprocess.run(['git', '-C', str(root), *args], capture_output=True, text=True)
    require(p.returncode == 0, 'GIT:' + ' '.join(args))
    return p.stdout.strip()


def mode(path):
    return '100755' if path.stat().st_mode & 0o111 else '100644'


def doc(root, path):
    text = read(root, path)
    require(text.startswith('---\n'), 'FRONTMATTER:' + path)
    _, front, body = text.split('---', 2)
    return yaml.safe_load(front), body


def section(body, number, title=None):
    heads = list(re.finditer(r'(?m)^## (\d+)\. ([^\n]+)\n', body))
    selected = [(i, h) for i, h in enumerate(heads) if int(h.group(1)) == number]
    require(len(selected) == 1, 'SECTION:' + str(number))
    i, h = selected[0]
    if title:
        require(h.group(2) == title, 'SECTION_TITLE:' + str(number))
    return body[h.end():heads[i + 1].start() if i + 1 < len(heads) else len(body)]


def escaped(text, position):
    start = position
    while start and text[start - 1] == '\\':
        start -= 1
    return (position - start) % 2 == 1


def blank_markup(text):
    # Keep boundaries/newlines: removing hidden text must not join two fragments
    # into a new synthetic link that did not exist in the original source.
    return ''.join('\n' if char == '\n' else ' ' for char in text)


def visible_link_source(body):
    """Conservative supported source regions, before decoding any entities.

    Simple unindented Markdown paragraphs and standalone HTML anchors qualify.
    Comments, fenced/indented code and exact-delimiter inline code do not.
    Reference links, nested Markdown brackets and Markdown mixed with raw HTML
    in one paragraph are deliberately unsupported, never guessed into a PASS.
    """
    body = re.sub(r'<!--(?s:.*?)(?:-->|\Z)', lambda m: blank_markup(m.group()), body)
    lines, fence_char, fence_size = [], None, 0
    for line in body.splitlines(keepends=True):
        opening = re.match(r'^ {0,3}(`{3,}|~{3,})([^\n]*)', line)
        if fence_char:
            close = re.match(r'^ {0,3}(' + re.escape(fence_char) + r'{'+str(fence_size)+r',})[ \t]*(?:\n|$)', line)
            lines.append(blank_markup(line))
            if close:
                fence_char, fence_size = None, 0
        elif opening:
            fence_char, fence_size = opening.group(1)[0], len(opening.group(1))
            lines.append(blank_markup(line))
        elif line.startswith(('    ', '\t')):
            lines.append(blank_markup(line))
        else:
            lines.append(line)
    body = ''.join(lines)
    original, pieces, cursor = body, [], 0
    runs = list(re.finditer(r'`+', original))
    for opening in runs:
        if opening.start() < cursor or escaped(original, opening.start()):
            continue
        closing = next((candidate for candidate in runs if candidate.start() >= opening.end()
                        and len(candidate.group()) == len(opening.group())), None)
        if closing:
            pieces.extend((original[cursor:opening.start()], blank_markup(original[opening.start():closing.end()])))
            cursor = closing.end()
    pieces.append(original[cursor:])
    body = ''.join(pieces)
    # A backslash-escaped tag opener is displayed text, not an HTML anchor.
    # Encode only that opener; decode destinations only AFTER a genuine link
    # has been identified. Whole-document unescape would invent hidden anchors.
    return ''.join('&lt;' if char == '<' and escaped(body, i) else char for i, char in enumerate(body))


def rendered_links(body):
    """Recognize supported actual link markup, then decode its destination.

    HTML extraction is separate from Markdown text extraction. Markdown syntax
    in raw HTML/attributes is never mistaken for an active Markdown link. Only
    closed, visible, standalone <a href=...> anchors with href/title attributes
    qualify; hidden/nested/script/style/pre/code contexts cannot provide proof.
    """
    hrefs = []
    visible = visible_link_source(body)

    class Anchors(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=False)
            self.markup = False
            self.stack = []
            self.anchor = None

        def handle_starttag(self, tag, attrs):
            self.markup = True
            tag = tag.lower()
            if tag == 'a' and not self.stack:
                destinations = [value for key, value in attrs if key == 'href' and value is not None]
                allowed = len(destinations) == 1 and all(key in ('href', 'title') for key, _ in attrs)
                self.anchor = {'href':destinations[0], 'visible':False, 'paragraph':self.paragraph} if allowed else None
            elif self.anchor:
                # Restrict labels to ordinary text or unstyled visible inline
                # tags. An unsupported descendant invalidates the whole anchor.
                if tag not in ('em', 'strong', 'code') or attrs:
                    self.anchor = None
            if tag not in ('area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'):
                self.stack.append(tag)

        def handle_startendtag(self, tag, attrs):
            self.markup = True
            if self.anchor:
                self.anchor = None

        def handle_endtag(self, tag):
            self.markup = True
            tag = tag.lower()
            if self.stack and self.stack[-1] == tag:
                if tag == 'a' and len(self.stack) == 1:
                    if self.anchor and self.anchor['visible'] and self.anchor['paragraph'] == self.paragraph:
                        hrefs.append((self.anchor['href'], self.paragraph))
                    self.anchor = None
                self.stack.pop()
            else:
                self.anchor = None

        def handle_data(self, data):
            if self.anchor and data.strip():
                self.anchor['visible'] = True

        def handle_entityref(self, name):
            if self.anchor and html.unescape('&'+name+';').strip():
                self.anchor['visible'] = True

        def handle_charref(self, name):
            if self.anchor and html.unescape('&#'+name+';').strip():
                self.anchor['visible'] = True

        def handle_decl(self, decl):
            self.markup = True

        def handle_pi(self, data):
            self.markup = True

        def unknown_decl(self, data):
            self.markup = True

        def handle_comment(self, data):
            self.markup = True

    pattern = r'''(?<!!)\[[^\]\n]*\]\(\s*(?:<([^>\n]+)>|([^\s()\n]+))(?:\s+(?:"[^"]*"|'[^']*'|\([^)]*\)))?\s*\)'''
    parser = Anchors()
    for index, paragraph in enumerate(visible.split('\n\n')):
        # Keep HTML context across blank lines, including unclosed pre/code/
        # script containers. A partial raw tag is ambiguous, never Markdown.
        parser.markup = bool(parser.stack) or bool(re.search(r'<(?:/?[A-Za-z]|!)', paragraph))
        parser.paragraph = index
        parser.feed(paragraph + '\n\n')
        if not parser.markup:
            for match in re.finditer(pattern, paragraph):
                if not escaped(paragraph, match.start()):
                    hrefs.append((html.unescape(match.group(1) or match.group(2)), index))
    parser.close()
    # HTMLParser already decoded attribute entities, even convert_charrefs=False.
    # Raw Markdown destinations are decoded once at their recognition site.
    return hrefs


def rendered_hrefs(body):
    return [href for href, _ in rendered_links(body)]


def has_target_href(root, document, body, target, paragraph_index=None, section_number=None):
    """Resolve rendered links from document parent, retaining the repo boundary."""
    root = root.resolve()
    expected = (root / target).resolve()
    if root not in expected.parents or not expected.is_file():
        return False
    for href, index in rendered_links(body):
        if paragraph_index is not None and paragraph_index != index:
            continue
        if section_number is not None:
            headings = list(re.finditer(r'(?m)^## (\d+)\. [^\n]+\n', body))
            matches = [(i, head) for i, head in enumerate(headings) if int(head.group(1)) == section_number]
            if len(matches) != 1:
                continue
            i, head = matches[0]
            section_end = headings[i+1].start() if i+1 < len(headings) else len(body)
            paragraphs = body.split('\n\n')
            start = sum(len(p)+2 for p in paragraphs[:index])
            if not (head.end() <= start and start+len(paragraphs[index]) <= section_end):
                continue
        parts = urlsplit(href)
        if parts.scheme or parts.netloc or parts.query or parts.fragment or not parts.path or parts.path.startswith('/'):
            continue
        resolved = (root / Path(document).parent / unquote(parts.path)).resolve()
        if root in resolved.parents and resolved == expected and resolved.is_file():
            return True
    return False


def header_delta(root, path, version, enforcement=None):
    new, _ = doc(root, path)
    old, _ = doc(BASE, path)
    require(new['version'] == version, 'VERSION:' + path)
    logs = new.get('change_log', [])
    require(len(logs) == len(old['change_log']) + 1 and logs[1:] == old['change_log']
            and logs[0]['version'] == version, 'CHANGE_LOG:' + path)
    normalized = copy.deepcopy(new)
    normalized['version'] = old['version']
    normalized['change_log'] = old['change_log']
    if enforcement:
        require(new.get('enforcement') == enforcement, 'ENFORCEMENT:' + path)
        normalized['enforcement'] = old['enforcement']
    require(normalized == old, 'FRONTMATTER_SCOPE:' + path)


def contract():
    return js(HERE, 'recovery-approved-contract.json')


def surface_content(root):
    s = section(doc(root, 'tools/interface.md')[1], 6, 'Optional Capability: Live Runtime Sessions')
    expected = contract()['implementation_requirements']
    # Operation declarations must be complete rows/bullets, not stray mentions.
    declarations = re.findall(r'(?m)^(?:\|\s*|[-*]\s+)(?:\*\*)?`([a-z]+-[a-z]+)`', s)
    require(sorted(declarations) == sorted(expected['operations']), 'OPERATIONS_EXACT')
    kind_tokens = set(re.findall(r'`(load_source|compile_source|evaluate|run_tests|observe)`', s))
    schema = js(root, 'schema/runtime_operation.schema.json')
    require(kind_tokens == set(schema['properties']['kind']['enum']), 'KINDS_EXACT')
    for token in ('operation_id', 'session_id', 'expected_generation', 'counter', 'nonce',
                  'expected_lease_epoch', 'requester', 'principal_kind', 'role', 'agent_id',
                  'contract_id', 'step_key', 'attempt', 'kind', 'payload', 'context',
                  'working_dir', 'namespace', 'limits', 'read-state', 'wait_outcome', 'stopped_waiting'):
        require(re.search(r'(?<![\w-])' + re.escape(token) + r'(?![\w-])', s), 'REQUEST_OR_STATUS:' + token)
    statuses = set(schema['properties']['status']['enum'])
    require(all('`' + status + '`' in s for status in statuses), 'STATUSES')
    require(re.search(r'debugger_paused[^\n]*(?:optional|reserved|not emitted)', s, re.I)
            or re.search(r'(?:optional|reserved|not emitted)[^\n]*debugger_paused', s, re.I), 'DEBUGGER_BOUNDARY')
    labels = re.findall(r'(?m)^(?:\|\s*|[-*]\s+(?:\*\*)?)S([1-9])(?:\*\*)?(?:\s*\||:)', s)
    require(sorted(labels) == [str(i) for i in range(1, 10)], 'S_RULES_EXACT')
    # The source reviewer checks the actual relationships independently. These
    # structural predicates catch misplaced/missing components, not prose truth.
    patterns = {
        1: (r'schema', r'record'),
        2: (r'generation', r'lease', r'(?:reject|before execution)'),
        3: (r'(?:one|1)', r'(?:flight|outstanding)'),
        4: (r'timeout', r'(?:wait|stop)'),
        5: (r'(?:unwind|unwinding)', r'(?:load|compile)', r'consisten'),
        6: (r'review', r'(?:reject|endpoint)'),
        7: (r'lifecycle', r'(?:evaluat|code)'),
        8: (r'session', r'acceptance', r'(?:fresh|never|not)'),
        9: (r'(?:attempt|counter)', r'(?:generation|process|reset)'),
    }
    for n, pats in patterns.items():
        row = re.search(r'(?m)^(?:\|\s*|[-*]\s+(?:\*\*)?)S' + str(n) + r'(?:\*\*)?(?:\s*\||:)([^\n]+)', s)
        require(row and all(re.search(p, row.group(1), re.I) for p in pats), 'S_RULE_CONTENT:' + str(n))
    require(re.search(r'only[^.\n]*submit-operation[^.\n]*(?:execut|project code)', s, re.I), 'SUBMIT_ONLY')
    require(re.search(r'(?:no|not)[^.\n]*(?:separate|status)[^.\n]*(?:call|endpoint)', s, re.I), 'NO_STATUS_CALL')
    require(re.search(r'(?:nonclaiming|without|do not claim|does not claim)[^.\n]*(?:conform|optional)', s, re.I), 'OPTIONAL_COMPATIBILITY')
    require(re.search(r'(?:only|claiming)[^.\n]*(?:claim|adapter)', s, re.I), 'CONDITIONAL_CLAIM')
    require(all(p in s for p in ('runtime.session.lifecycle', 'runtime.session.operate', 'runtime.session.accept')), 'PERMISSION_ROUTES')


def source_review(root):
    inputs = js(root, '.agent/evidence/113/current-source-inputs.json')
    review = js(root, '.agent/evidence/113/source-review.json')
    actors = js(root, '.agent/evidence/113/fixed-inputs.json')['actors']
    require(review.get('actor') not in (actors['generator'], actors['test_author'])
            and review.get('actor') in (actors['bundle_reviewer'], actors['final_qa']), 'SOURCE_REVIEW_INDEPENDENCE')
    require(review.get('candidate_commit') == inputs['candidate']['commit']
            and review.get('source_manifest_sha256') == sha(root / '.agent/evidence/113/current-source-inputs.json')
            and review.get('fixed_inputs_sha256') == sha(root / '.agent/evidence/113/fixed-inputs.json'), 'SOURCE_REVIEW_BINDING')
    require(review.get('final_verdict', {}).get('approved') is True
            and all(review.get(k) == [] for k in ('issues', 'missing_acceptance_coverage', 'unsupported_claims')), 'SOURCE_REVIEW_VERDICT')
    require(review.get('evidence') and all(read(root, p).strip() for p in review['evidence']), 'SOURCE_REVIEW_EVIDENCE')


def surface(root):
    surface_content(root)
    source_review(root)


def unique(entries, key, diagnostic):
    names = [e[key] for e in entries]
    require(len(names) == len(set(names)), diagnostic)


def routing(root):
    m = js(root, 'tools/skill.json')
    unique(m['capabilities'], 'name', 'DUPLICATE_MANIFEST_ROUTE')
    caps = {e['name']: e['module'] for e in m['capabilities']}
    require(caps.get('live_runtime_session') == 'tools/interface.md'
            and caps.get('sbcl_runtime_binding') == 'methodology/11_sbcl_runtime_binding.md'
            and caps.get('live_runtime_protocol') == 'methodology/10_live_runtime_sessions.md', 'MANIFEST_ROUTE')
    req = m['runtime_requirements'].get('live_runtime_session')
    require(isinstance(req, dict) and req.get('required') is False, 'OPTIONAL_REQUIRED_FALSE')
    index = js(root, 'NIZAM.json')
    unique(index['capabilities'], 'id', 'DUPLICATE_INDEX_ROUTE')
    require({e['id']: e['authoritative_source'] for e in index['capabilities']}.get('nizam-live-runtime-adapter') == 'tools/interface.md', 'INDEX_ROUTE')
    router = section(doc(root, 'tools/SKILL.md')[1], 10, 'Live Runtime Sessions')
    for path in ('tools/interface.md', 'methodology/10_live_runtime_sessions.md', 'methodology/11_sbcl_runtime_binding.md'):
        require(path in router and (root / path).is_file(), 'ROUTER_PATH:' + path)
    for file in ('tools/interface.md', 'tools/README.md'):
        body = doc(root, file)[1]
        for path in ('10_live_runtime_sessions.md', '11_sbcl_runtime_binding.md'):
            require(has_target_href(root, file, body, 'methodology/' + path), 'CROSSLINK:' + file + ':' + path)
    for file in PRODUCT[5:7]:
        body = doc(root, file)[1]
        location = 1 if file == PRODUCT[6] else None
        require(has_target_href(root, file, body, 'tools/interface.md', section_number=location), 'DOCUMENT_INTERFACE_LINK:' + file)
    refs = section(doc(root, 'tools/interface.md')[1], 7, 'References')
    for path in ('schema/runtime_session.schema.json', 'schema/runtime_operation.schema.json'):
        require(has_target_href(root, 'tools/interface.md', refs, path), 'SCHEMA_LINK:' + path)


def compatibility(root):
    old = doc(BASE, 'tools/interface.md')[1]
    new = doc(root, 'tools/interface.md')[1]
    require(new.split('## 6.')[0] == old.split('## 6.')[0], 'INTERFACE_BASE_BODY')
    require(len(re.findall(r'(?m)^\s*\d+\. ', section(new, 5))) == 10, 'TEN_ITEMS')
    oldm, newm = js(BASE, 'tools/skill.json'), js(root, 'tools/skill.json')
    normalized = copy.deepcopy(newm)
    require(normalized['version'] == '0.6.0', 'MANIFEST_VERSION')
    normalized['version'] = oldm['version']
    require(normalized['runtime_requirements'].pop('live_runtime_session', {}).get('required') is False, 'OPTIONAL_REQUIRED_FALSE')
    extra = {'live_runtime_session', 'sbcl_runtime_binding'}
    additions = [x for x in normalized['capabilities'] if x['name'] in extra]
    require(len(additions) == 2, 'MANIFEST_ADDITIONS')
    normalized['capabilities'] = [x for x in normalized['capabilities'] if x['name'] not in extra]
    require(normalized == oldm, 'MANIFEST_BASE_PRESERVED')
    oldi, newi = js(BASE, 'NIZAM.json'), js(root, 'NIZAM.json')
    additions = [x for x in newi['capabilities'] if x['id'] == 'nizam-live-runtime-adapter']
    require(len(additions) == 1, 'INDEX_ADDITIONS')
    newi['capabilities'] = [x for x in newi['capabilities'] if x['id'] != 'nizam-live-runtime-adapter']
    require(newi == oldi, 'INDEX_BASE_PRESERVED')


def bounded_delta(root):
    versions = {'tools/interface.md': '0.4.0', 'tools/SKILL.md': '0.6.0', 'tools/README.md': '0.20.0',
                'methodology/10_live_runtime_sessions.md': '0.2.0', 'methodology/11_sbcl_runtime_binding.md': '0.1.1'}
    for path, version in versions.items():
        enforcement = 'partially-enforced' if path == PRODUCT[5] else None
        header_delta(root, path, version, enforcement)
    old, new = doc(BASE, 'tools/SKILL.md')[1], doc(root, 'tools/SKILL.md')[1]
    require(new.split('## 10.')[0] == old.split('## 10.')[0], 'SKILL_BASE_BODY')
    for path, oldn, newn in (('tools/interface.md', 6, 7), ('tools/SKILL.md', 10, 11)):
        oldrefs, newrefs = section(doc(BASE, path)[1], oldn), section(doc(root, path)[1], newn)
        require(newrefs.startswith(oldrefs.rstrip()) and len(newrefs) - len(oldrefs) < 1800, 'REFERENCE_PRESERVATION:' + path)
    old, new = doc(BASE, PRODUCT[5])[1], doc(root, PRODUCT[5])[1]
    for n in range(1, 12):
        require(section(old, n) == section(new, n), 'RUNTIME_SECTION_PRESERVED:' + str(n))
    require(old[old.index('A runtime session'):old.index('## 1.')] == new[new.index('A runtime session'):new.index('## 1.')], 'RUNTIME_DEFINITION_PRESERVED')
    marker = 'The normative\nSBCL reference binding is delivered.'
    # Availability is the only mutable tail of the second Section12 paragraph.
    old12, new12 = section(old, 12), section(new, 12)
    require(old12.split(marker)[0] == new12.split(marker)[0]
            and old12[old12.index('| requirement-id'): ] == new12[new12.index('| requirement-id'):], 'RUNTIME_SECTION12_PRESERVED')
    old, new = doc(BASE, PRODUCT[6])[1], doc(root, PRODUCT[6])[1]
    paragraphs = new.split('\n\n')
    added = [p for i, p in enumerate(paragraphs) if has_target_href(root, PRODUCT[6], new, 'tools/interface.md', i, 1)]
    require(len(added) == 1 and len(added[0].split()) <= 100, 'SBCL_BOUNDED_LINK')
    require('\n\n'.join(p for p in paragraphs if p not in added) == old, 'SBCL_BODY_PRESERVED')
    old, new = doc(BASE, 'tools/README.md')[1], doc(root, 'tools/README.md')[1]
    def normalize_readme(text, revised):
        paras = text.split('\n\n')
        if revised:
            extra = [p for i, p in enumerate(paras) if not p.startswith('|') and has_target_href(root, 'tools/README.md', text, 'methodology/10_live_runtime_sessions.md', i)]
            require(len(extra) == 1 and len(extra[0].split()) <= 120, 'README_BOUNDED_PARAGRAPH')
            paras = [p for p in paras if p not in extra]
        return '\n\n'.join('\n'.join(line for line in p.split('\n') if not line.startswith(('| [`skill.json`]', '| [`interface.md`]'))) for p in paras)
    require(normalize_readme(old, False) == normalize_readme(new, True), 'README_BASE_PRESERVED')
    old, new = read(BASE, 'CHANGELOG.md'), read(root, 'CHANGELOG.md')
    changed = new.split('### Changed\n\n', 1)
    require(len(changed) == 2 and changed[0] == old.split('### Changed\n\n', 1)[0], 'CHANGELOG_LOCATION')
    bullet, rest = changed[1].split('\n\n', 1)
    require(bullet.startswith('- ') and '113' in bullet and len(bullet.split()) < 160
            and changed[0] + '### Changed\n\n' + rest == old, 'CHANGELOG_PRESERVED')


def history(root):
    pins = js(RECOVERY, 'pins.json')
    inventory = root / '.agent/evidence/113/private/history.json'
    require(inventory.is_file() and not inventory.is_symlink()
            and sha(inventory) == pins['original_history_sha256'], 'HISTORY_INVENTORY_IMMUTABLE')
    expected = js(root, '.agent/evidence/113/private/history.json')
    require(len(expected) == 4279, 'HISTORY_INVENTORY_COUNT')
    for path, meta in pins['base_files'].items():
        p = root / path
        require(p.is_file() and not p.is_symlink() and sha(p) == meta['sha256']
                and stat.S_IMODE(p.stat().st_mode) == meta['permissions'], 'HISTORICAL_BASE:' + path)
    mapping = contract()['recovery']['historical_contract_map']
    archive_inventory = root / mapping['archive_inventory_path']
    require(archive_inventory.is_file() and not archive_inventory.is_symlink()
            and sha(archive_inventory) == mapping['archive_inventory_sha256'], 'ORIGINAL_CONTRACT_ARCHIVE_INVENTORY')
    entry = js(root, mapping['archive_inventory_path'])[mapping['original_history_entry']]
    require(entry == {'sha256':mapping['original_sha256'], 'mode':oct(mapping['original_stat_permissions'])}, 'ORIGINAL_CONTRACT_ARCHIVE_ENTRY')
    for path, meta in expected.items():
        if path == 'docs/planning/DEBT.md':
            require(sha(RECOVERY / 'debt-original.md') == meta['sha256'], 'DEBT_ORIGINAL_HISTORY')
            debt(root)
            continue
        if path == mapping['original_history_entry']:
            p = root / mapping['archive_path']
            require(p.is_file() and not p.is_symlink() and sha(p) == meta['sha256'] == mapping['original_sha256']
                    and stat.S_IMODE(p.stat().st_mode) == meta['permissions'] == mapping['original_stat_permissions'], 'ORIGINAL_CONTRACT_ARCHIVE')
            continue
        p = root / path
        require(p.is_file() and not p.is_symlink() and sha(p) == meta['sha256']
                and stat.S_IMODE(p.stat().st_mode) == meta['permissions'], 'HISTORY_OR_INSTALLED:' + path)
    actual_installed = {str(p.relative_to(root)) for p in (root / '.nizam').rglob('*') if p.is_file() or p.is_symlink()}
    require(actual_installed == {p for p in expected if p.startswith('.nizam/')}, 'INSTALLED_INVENTORY')
    live = root / '.agent/contracts/113.json'
    require(live.is_file() and not live.is_symlink() and sha(live) == pins['approved_contract_sha256']
            and stat.S_IMODE(live.stat().st_mode) == pins['approved_contract_permissions'], 'LIVE_RECOVERY_CONTRACT_PIN')
    actual = js(root, '.agent/contracts/113.json')
    require(actual == contract() and actual['status'] == 'approved'
            and actual['approvals']['validator_mode_a'] is True and actual['approvals']['evaluator_contract_review'] is True, 'LIVE_RECOVERY_CONTRACT_APPROVAL')
    allowed = set(PRODUCT) | set(COORDINATION) | {'.agent/contracts/113.json', 'docs/planning/DEBT.md'}
    changed = git(root, 'diff', contract()['base_revision'], '--name-only').splitlines()
    additions = git(root, 'ls-files', '--others', '--exclude-standard').splitlines()
    for path in set(changed + additions):
        permitted = path in allowed or path.startswith('.agent/evidence/113/') or path in (
            '.agent/validator/113-mode-a.json', '.agent/validator/113-test-bundle-review.json',
            '.agent/validator/113-mode-b.json', '.agent/qa/113-contract-review.json', '.agent/qa/113.json')
        require(permitted, 'OUT_OF_SCOPE:' + path)


def debt_parts(text):
    require(text.startswith('---\n'), 'DEBT_FRONTMATTER')
    _, front, body = text.split('---', 2)
    lines = [line for line in body.splitlines() if line.startswith('| NDEBT-050 |')]
    require(len(lines) == 1, 'DEBT050_SINGLE_ROW')
    parts = lines[0].split('|')
    require(len(parts) == 7, 'DEBT050_SHAPE')
    position = body.index(lines[0])
    section_name = 'Open' if body.rfind('## Open', 0, position) > body.rfind('## Resolved', 0, position) else 'Resolved'
    return yaml.safe_load(front), front, body, lines[0], parts, section_name


def debt_front_transition(previous, current, version):
    old, oldraw, *_ = debt_parts(previous)
    new, newraw, *_ = debt_parts(current)
    require(new.get('version') == version, 'DEBT_VERSION')
    require(len(new['change_log']) == len(old['change_log'])+1
            and new['change_log'][1:] == old['change_log'] and new['change_log'][0]['version'] == version,
            'DEBT_OLD_LOGS')
    require(newraw.split('change_log:\n', 1)[1].endswith(oldraw.split('change_log:\n', 1)[1]), 'DEBT_OLD_LOG_BYTES')
    normalized = copy.deepcopy(new)
    normalized.update(version=old['version'], change_log=old['change_log'])
    require(normalized == old, 'DEBT_FRONTMATTER_SCOPE')


def debt_text(original, halt, recovered, current, allow_resolved=False):
    # The pre-halt register has no050 row. Check its literal body/logs against
    # the actual mandatory halt delta, not a replacement historical baseline.
    _, oldfront, oldbody = original.split('---', 2)
    oldmeta = yaml.safe_load(oldfront)
    haltmeta, haltraw, haltbody, haltrow, haltparts, haltsection = debt_parts(halt)
    require(haltmeta['version'] == '0.63.0' and oldmeta['version'] == '0.62.0'
            and haltmeta['change_log'][1:] == oldmeta['change_log']
            and len(haltmeta['change_log']) == len(oldmeta['change_log'])+1, 'DEBT_HALT_LOG')
    normalized = copy.deepcopy(haltmeta)
    normalized.update(version=oldmeta['version'], change_log=oldmeta['change_log'])
    require(normalized == oldmeta and haltraw.split('change_log:\n',1)[1].endswith(oldfront.split('change_log:\n',1)[1]), 'DEBT_HALT_FRONTMATTER')
    require(haltbody.replace(haltrow+'\n','',1) == oldbody and haltsection == 'Open', 'DEBT_HALT_ONLY050')
    debt_front_transition(halt, recovered, '0.64.0')
    _, _, recoveredbody, recoveredrow, recoveredparts, recoveredsection = debt_parts(recovered)
    require(recoveredbody.replace(recoveredrow+'\n','',1) == haltbody.replace(haltrow+'\n','',1), 'DEBT_OTHER_BODY')
    require(recoveredparts[:5] == haltparts[:5] and recoveredparts[5].strip().startswith(haltparts[5].strip()), 'DEBT050_HALT_PREFIX')
    append = recoveredparts[5].strip()[len(haltparts[5].strip()):]
    require(0 < len(append.split()) <= 160 and all(token in append for token in ('recovery-authorization.json', '113-recovery-1', 'Open', 'pending')), 'DEBT050_RECOVERY_APPEND')
    require(recoveredsection == 'Open', 'DEBT050_RECOVERY_OPEN')
    newmeta, _, newbody, newrow, newparts, newsection = debt_parts(current)
    if newmeta['version'] == '0.64.0':
        require(current == recovered, 'DEBT_RECOVERY_BYTES')
        return
    require(newmeta['version'] == '0.65.0', 'DEBT_VERSION')
    debt_front_transition(recovered, current, '0.65.0')
    require(newbody.replace(newrow+'\n','',1) == recoveredbody.replace(recoveredrow+'\n','',1), 'DEBT_OTHER_BODY')
    require(newparts[:5] == recoveredparts[:5] and newparts[5].strip().startswith(recoveredparts[5].strip()), 'DEBT050_HALT_PREFIX')
    append = newparts[5].strip()[len(recoveredparts[5].strip()):]
    require(0 < len(append.split()) <= 160 and 'RESOLVED' in append and 'evidence-gate.txt' in append, 'DEBT050_RESOLUTION_APPEND')
    resolved_rows = [line for line in newbody.split('## Resolved',1)[1].splitlines() if line.startswith('| NDEBT-')]
    require(newsection == 'Resolved' and resolved_rows and resolved_rows[0] == newrow, 'DEBT050_RESOLUTION_LOCATION')
    require(allow_resolved, 'DEBT_PREMATURE_RESOLUTION')


def real_completion(root):
    files = ('.agent/validator/113-test-bundle-review.json', '.agent/validator/113-mode-b.json', '.agent/qa/113.json',
             '.agent/evidence/113/current-source-inputs.json', '.agent/evidence/113/evidence-gate.txt')
    if not all((root/path).is_file() for path in files):
        return False
    bundle, mode_b, qa = [js(root,path) for path in files[:3]]
    source = js(root, files[3])
    for gate in (bundle, mode_b, qa):
        if gate.get('final_verdict',{}).get('approved') is not True or any(gate.get(k) != [] for k in ('issues','missing_acceptance_coverage','unsupported_claims')):
            return False
    actors = js(root,'.agent/evidence/113/fixed-inputs.json')['actors']
    if qa.get('actor') != actors['final_qa'] or qa.get('qa_pass') is not True or qa.get('checks_passed') != 16 or qa.get('checks_run') != 16 or qa.get('adversarial',{}).get('performed') is not True:
        return False
    for gate in (mode_b, qa):
        if gate.get('candidate_commit') != source['candidate']['commit'] or gate.get('source_manifest_sha256') != sha(root/'.agent/evidence/113/current-source-inputs.json') or gate.get('fixed_inputs_sha256') != sha(root/'.agent/evidence/113/fixed-inputs.json'):
            return False
    raw = read(root,files[4])
    return (raw.startswith('COMMAND: PYTHONDONTWRITEBYTECODE=1 python3 .agent/evidence/113/evidence_gate.py\n')
            and 'CANDIDATE_SHA: '+source['candidate']['commit']+'\n' in raw
            and 'EVIDENCE GATE PASS:' in raw and re.findall(r'(?m)^EXIT:\s*(-?\d+)\s*$',raw)==['0'])


def debt(root):
    pins = js(RECOVERY,'pins.json')
    require(sha(root/'.agent/evidence/113/recovery-authorization.json') == pins['authorization_sha256'], 'RECOVERY_AUTHORIZATION_PIN')
    require(stat.S_IMODE((root/'docs/planning/DEBT.md').stat().st_mode) == 436, 'DEBT_PERMISSIONS')
    debt_text(read(RECOVERY,'debt-original.md'), read(HERE,'recovery-debt-halt.md'),
              read(RECOVERY,'debt-recovery.md'), read(root,'docs/planning/DEBT.md'), allow_resolved=real_completion(root))


def scope_history(root):
    compatibility(root)
    bounded_delta(root)
    history(root)
    budget_actual(root)


def budget_actual(root):
    # Invoke the unchanged frozen classifier. Parsing its reported total adds
    # the approved ceiling predicate, never another measurement algorithm.
    command = [sys.executable, '.agent/evidence/scope-budget-014/measure.py',
               '--range', '113=' + contract()['base_revision'] + '..', '--files']
    result = subprocess.run(command, cwd=root, capture_output=True, text=True,
                            env={**os.environ, 'PYTHONDONTWRITEBYTECODE':'1'})
    require(result.returncode == 0, 'BUDGET_MEASURE_EXIT:' + str(result.returncode))
    totals = re.findall(r'(?m)^\s*BUDGET_COUNTED_LINES=(\d+)\s*$', result.stdout)
    require(len(totals) == 1, 'BUDGET_MEASURE_TOTAL')
    require(6088 + int(totals[0]) <= 9360, 'BUDGET_ACTUAL_CEILING')


def lifecycle_data(features, phase, state, completion=False):
    oldfeatures = js(BASE, '.agent/feature_list_015.json')
    oldphase = yaml.safe_load(read(BASE, 'docs/planning/phase_015.yaml'))
    oldstate = js(BASE, '.agent/run_state.json')
    recovery_state = js(RECOVERY,'state.json')
    recovery_features = js(RECOVERY,'features.json')
    blocked_row = next(x for x in recovery_features['features'] if x['id']=='113')
    require(phase.get('status') == 'in_progress', 'PHASE_CONTINUITY')
    require([x['id'] for x in features['features']] == [x['id'] for x in oldfeatures['features']], 'FEATURE_IDS')
    require([x['id'] for x in phase['steps']] == [x['id'] for x in oldphase['steps']], 'STEP_IDS')
    for key in features:
        if key != 'features':
            require(features[key] == oldfeatures[key], 'FEATURE_ENVELOPE')
    for key in phase:
        if key != 'steps':
            require(phase[key] == oldphase[key], 'PHASE_ENVELOPE')
    for row, old in zip(features['features'], oldfeatures['features']):
        if row['id'] != '113':
            require(row == old, 'PREDECESSOR_SUCCESSOR:' + row['id'])
            continue
        allowed = {'status', 'passes', 'contract_ref', 'completed_at', 'qa', 'evidence', 'blocked_reason'}
        require({k:v for k,v in row.items() if k not in allowed} == {k:v for k,v in old.items() if k not in allowed}, 'FEATURE113_IMMUTABLE')
        require(row['status'] in ('blocked', 'in_progress', 'complete'), 'FEATURE113_STATUS')
        if row['status']=='blocked':
            require(row.get('passes') is False and row.get('blocked_reason')==blocked_row['blocked_reason']
                    and row.get('evidence')=='.agent/evidence/113/circuit-breaker-halt.json', 'BLOCKED_REFERENCES')
        if row['status']=='in_progress':
            require(row.get('passes') is False and 'blocked_reason' not in row, 'RECOVERY_RESUME_MASK')
        if row['status'] == 'complete':
            require(row.get('passes') is True and row.get('qa') == '.agent/qa/113.json'
                    and row.get('evidence') == '.agent/evidence/113/evidence-gate.txt'
                    and row.get('contract_ref') == '.agent/contracts/113.json' and row.get('completed_at'), 'COMPLETION_REFERENCES')
    feature = next(x for x in features['features'] if x['id'] == '113')
    for row, old in zip(phase['steps'], oldphase['steps']):
        if row['id'] != '113':
            require(row == old, 'STEP_HISTORY:' + row['id'])
        else:
            require(row.get('description') == old['description'], 'STEP113_DESCRIPTION')
            require(set(row) <= {'id', 'description', 'status', 'evidence', 'docs_updated', 'changelog_entry'}, 'STEP113_FIELDS')
            require(row['status'] == {'blocked':'BLOCKED', 'in_progress':'IN_PROGRESS', 'complete':'COMPLETED'}[feature['status']], 'LIFECYCLE_AGREEMENT')
            if row['status']=='BLOCKED':
                require(row.get('evidence')=='.agent/evidence/113/circuit-breaker-halt.json', 'BLOCKED_STEP_EVIDENCE')
            if row['status'] == 'COMPLETED':
                require(row.get('evidence') == '.agent/evidence/113/evidence-gate.txt'
                        and row.get('docs_updated') and row.get('changelog_entry'), 'STEP113_COMPLETION')
    require(state['current_phase'] == oldstate['current_phase'] and state['current_feature'] in ('113', '114'), 'RUN_POSITION')
    require(state['status'] == ('blocked' if feature['status']=='blocked' else 'in_progress'), 'RUN_STATUS_AGREEMENT')
    budget = state['scope_budget']
    require(budget['original_estimate_lines'] == 7200 and budget['ceiling_130pct'] == 9360
            and budget['per_feature'][:3] == oldstate['scope_budget']['per_feature'][:3]
            and budget['total_lines_changed'] <= 9360, 'BUDGET_CONTINUITY')
    require(set(state['circuit_breaker']) == set(recovery_state['circuit_breaker']), 'UNAUTHORIZED_COUNTER_KEY')
    for key, old in recovery_state['circuit_breaker'].items():
        now = state['circuit_breaker'].get(key)
        if key in ('113-checker-development','113-checker-review','113-contract'):
            require(now==old and now['attempts']==3 and now['limit']==3, 'COUNTER_CONTINUITY:'+key)
        elif key in ('113-recovery-1-checker-development','113-recovery-1-checker-review'):
            require(set(now)=={'attempts','limit','authorization'} and now['authorization']=='.agent/evidence/113/recovery-authorization.json'
                    and now['limit']==3 and old['attempts']<=now['attempts']<=3, 'RECOVERY_COUNTER_AUTH:'+key)
        elif key in ('113-generator-development','113-implementation','113-qa','113-evidence-capture'):
            require(set(now)==set(old) and now['limit']==old['limit']==3 and old['attempts']<=now['attempts']<=3, 'COUNTER_CONTINUITY:'+key)
        else:
            require(now == old, 'HISTORICAL_COUNTER:' + key)
    require(state['history'][:len(oldstate['history'])] == oldstate['history'], 'HISTORY_APPEND_ONLY')
    require(state['history'][:len(recovery_state['history'])] == recovery_state['history'], 'RECOVERY_HISTORY_APPEND_ONLY')
    mutable={'current_feature','status','updated_at','circuit_breaker','history','scope_budget','last_action','active_contract_id','pending_operator_gate','blocked_features','completed_contract_ids'}
    require({k:v for k,v in state.items() if k not in mutable}=={k:v for k,v in recovery_state.items() if k not in mutable}, 'HISTORICAL_STATE_FIELDS')
    require(completion is False or feature['status'] == 'complete', 'COMPLETION_PROJECTION')


def lifecycle(root):
    features = js(root, COORDINATION[0])
    phase = yaml.safe_load(read(root, COORDINATION[1]))
    state = js(root, COORDINATION[2])
    lifecycle_data(features, phase, state)
    debt(root)
    c = js(root, '.agent/contracts/113.json')
    require(c == contract(), 'APPROVED_CONTRACT_IMMUTABLE')
    require(c['status'] == 'approved' and c['approvals']['validator_mode_a'] is True
            and c['approvals']['evaluator_contract_review'] is True, 'CONTRACT_APPROVALS')
    feature=next(x for x in features['features'] if x['id']=='113')
    if feature['status'] != 'blocked':
        reviewed=js(root,'.agent/validator/113-test-bundle-review.json')
        require(reviewed.get('final_verdict',{}).get('approved') is True
                and all(reviewed.get(k)==[] for k in ('issues','missing_acceptance_coverage','unsupported_claims'))
                and reviewed.get('fixed_inputs_sha256')==sha(root/'.agent/evidence/113/fixed-inputs.json'), 'RECOVERY_BUNDLE_RESUME_GATE')
    if feature['status']=='complete':
        require(real_completion(root), 'COMPLETION_ACTUAL_EVIDENCE')
    # Explicit projection remains memory/scratch proof, never a lifecycle write.
    projected, projected_phase = copy.deepcopy(features), copy.deepcopy(phase)
    row = next(x for x in projected['features'] if x['id'] == '113')
    row.pop('blocked_reason',None)
    row.update(status='complete', passes=True, contract_ref='.agent/contracts/113.json',
               completed_at='CONTROL_ONLY', qa='.agent/qa/113.json', evidence='.agent/evidence/113/evidence-gate.txt')
    next(x for x in projected_phase['steps'] if x['id'] == '113').update(
        status='COMPLETED', evidence='.agent/evidence/113/evidence-gate.txt',
        docs_updated='CONTROL_ONLY', changelog_entry='CONTROL_ONLY')
    projected_state=copy.deepcopy(state);projected_state['status']='in_progress'
    lifecycle_data(projected, projected_phase, projected_state, completion=True)
    resumed=copy.deepcopy(features);resumed_phase=copy.deepcopy(phase)
    resumed_row=next(x for x in resumed['features'] if x['id']=='113')
    resumed_row.pop('blocked_reason',None);resumed_row.update(status='in_progress',passes=False)
    next(x for x in resumed_phase['steps'] if x['id']=='113')['status']='IN_PROGRESS'
    lifecycle_data(resumed,resumed_phase,projected_state)


def claim_boundary(root):
    _, runtime = doc(root, PRODUCT[5])
    head = runtime[:runtime.index('A runtime session')]
    require('partially-enforced' in head and all(word in head for word in ('schema', 'C12', 'record'))
            and re.search(r'(?:cannot|never|not)[^.]*prove[^.]*live', head, re.I), 'RECORD_ONLY_ENFORCEMENT')
    require('113' not in head or not re.search(r'pending[^.]*113', head), 'ADAPTER_DELIVERED')
    require(re.search(r'pending[^.]*phase016|phase016[^.]*pending', head, re.I), 'PHASE016_PENDING')
    front, sbcl = doc(root, PRODUCT[6])
    require(front.get('enforcement') == 'consumer-aspirational' and 'illustrative' in sbcl, 'SBCL_BOUNDARY')
    _, interface = doc(root, PRODUCT[0])
    s = section(interface, 6)
    require(re.search(r'(?:fresh|hermetic)', s, re.I) and re.search(r'(?:not|never)[^.]*acceptance evidence', s, re.I), 'ACCEPTANCE_BOUNDARY')
    # Positive declarations only. Historical unchanged changelog warnings are
    # never scanned as though they described current implementation delivery.
    forbidden = (r'controller (?:is |has been )?(?:delivered|implemented|working)',
                 r'(?:all |the )?(?:13|thirteen) (?:live )?(?:cases|proofs|tests) (?:pass|passed|complete)',
                 r'(?:released|published|upgraded) (?:framework |installed )?v?1\.[6-9]',
                 r'(?:authorized|allocated) phase016', r'(?:member of|governed by) NizamIQ')
    for path in PRODUCT:
        new = read(root, path)
        oldlines = set(read(BASE, path).splitlines())
        additions = '\n'.join(line for line in new.splitlines() if line not in oldlines)
        require(not any(re.search(p, additions, re.I) for p in forbidden), 'FALSE_DELIVERY_CLAIM:' + path)


def validate_members(root, members, diagnostic):
    require(isinstance(members, dict) and members, diagnostic + ':EMPTY')
    for path, meta in members.items():
        require(not Path(path).is_absolute() and '..' not in Path(path).parts, diagnostic + ':PATH')
        p = root / path
        require(p.is_file() and not p.is_symlink() and sha(p) == meta['sha256']
                and mode(p) == meta['mode'], diagnostic + ':' + path)


def integrity_data(root, fixed, fixed_seal, current, current_seal):
    require(fixed_seal.get('manifest_sha256') == sha(root / '.agent/evidence/113/fixed-inputs.json'), 'FIXED_SEAL')
    require(fixed['contract_sha256'] == sha(root / '.agent/contracts/113.json') and fixed['base_revision'] == contract()['base_revision'], 'FIXED_CONTRACT')
    actors = fixed['actors']
    require(set(actors) == {'test_author', 'generator', 'bundle_reviewer', 'final_qa'}
            and len(set(actors.values())) == 4 and actors['test_author'] == '/root/adapter_test_author_113'
            and actors['final_qa']=='/root/adapter_acceptance_recovery_113', 'ACTOR_INDEPENDENCE')
    validate_members(root, fixed['files'], 'FIXED_MEMBER')
    require(current_seal.get('manifest_sha256') == sha(root / '.agent/evidence/113/current-source-inputs.json')
            and current_seal.get('candidate_commit') == current['candidate']['commit'], 'SOURCE_SEAL')
    require(current['fixed_inputs_sha256'] == sha(root / '.agent/evidence/113/fixed-inputs.json')
            and current['contract_sha256'] == fixed['contract_sha256'], 'SOURCE_FIXED_BINDING')
    require(set(current['source_paths']) == set(PRODUCT), 'SOURCE_INVENTORY')
    validate_members(root, current['source_paths'], 'SOURCE_MEMBER')
    candidate = current['candidate']['commit']
    require(re.fullmatch(r'[0-9a-f]{40}', candidate) and git(root, 'rev-parse', candidate + '^{tree}') == current['candidate']['tree'], 'CANDIDATE_TREE')
    require(git(root, 'merge-base', candidate, 'HEAD') == candidate, 'CANDIDATE_ANCESTRY')
    for path, meta in current['source_paths'].items():
        obj = subprocess.run(['git', '-C', str(root), 'show', candidate + ':' + path], capture_output=True)
        require(obj.returncode == 0 and hashlib.sha256(obj.stdout).hexdigest() == meta['sha256'], 'CANDIDATE_SOURCE:' + path)
        require(git(root, 'ls-tree', candidate, '--', path).split()[0] == meta['mode'], 'CANDIDATE_MODE:' + path)
    # A later Parent closure may add receipts/canonical fields, never source.
    require(not git(root, 'diff', candidate, '--name-only', '--', *PRODUCT), 'SOURCE_CHANGED_AFTER_CANDIDATE')


def input_integrity(root):
    fixed = js(root, '.agent/evidence/113/fixed-inputs.json')
    current = js(root, '.agent/evidence/113/current-source-inputs.json')
    integrity_data(root, fixed, js(root, '.agent/evidence/113/fixed-inputs-seal.json'),
                   current, js(root, '.agent/evidence/113/current-source-seal.json'))
    review = js(root, '.agent/validator/113-test-bundle-review.json')
    require(review.get('actor') == fixed['actors']['bundle_reviewer']
            and review.get('fixed_inputs_sha256') == sha(root / '.agent/evidence/113/fixed-inputs.json')
            and review.get('final_verdict', {}).get('approved') is True
            and all(review.get(k) == [] for k in ('issues', 'missing_acceptance_coverage', 'unsupported_claims')), 'BUNDLE_REVIEW')


def negative_controls(root):
    command = [sys.executable, str(PRIVATE / 'controls.py'), '--root', str(root)]
    p = subprocess.run(command, text=True, capture_output=True, env={**os.environ, 'PYTHONDONTWRITEBYTECODE':'1'})
    print(p.stdout, end='')
    print(p.stderr, end='', file=sys.stderr)
    require(p.returncode == 0 and 'CONTROL_SUITE:PASS' in p.stdout, 'PRIVATE_CONTROLS')


FUNCTIONS = {'surface':surface, 'routing':routing, 'compatibility':compatibility,
             'scope-history':scope_history, 'lifecycle':lifecycle, 'negative-controls':negative_controls,
             'claim-boundary':claim_boundary, 'input-integrity':input_integrity}


def main():
    require(len(sys.argv) == 2 and sys.argv[1] in MODES, 'USAGE:' + ','.join(MODES))
    FUNCTIONS[sys.argv[1]](ROOT)
    print('113:' + sys.argv[1] + ':PASS')


if __name__ == '__main__':
    try:
        main()
    except (Failure, ValueError, KeyError, OSError, yaml.YAMLError) as e:
        print('113:FAIL:' + str(e), file=sys.stderr)
        sys.exit(1)
