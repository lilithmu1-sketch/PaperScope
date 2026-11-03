"""Render one reader-authored record into consistent views and a portable audit bundle."""
import argparse
from copy import deepcopy
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
from compile_quotes import compile_document
from integrity import comparison_errors, result
from calculate import replay as replay_calculations
import derived_assets

VERSION = 'paperscope-review-assembler/0.3'
TOKEN = re.compile(r'\{\{([CN]\d+)(?:\.(statement|reasoning|ref|value|units))?\}\}')
FINAL = ['answer.md', 'claims.json', 'comparison.csv', 'numeric-review.json']


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def read(path):
    def unique(pairs):
        obj = {}
        for key, value in pairs:
            if key in obj:
                raise ValueError('Duplicate JSON key: ' + key)
            obj[key] = value
        return obj
    return json.loads(Path(path).read_text(encoding='utf-8-sig'), object_pairs_hook=unique)


def text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(label + ' must be nonempty text')
    return value


def local_file(base, relative):
    relative = Path(text(relative, 'attachment path'))
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('Attachment paths must be relative and remain inside the draft folder')
    source = (base / relative).resolve()
    if not source.is_relative_to(base.resolve()) or not source.is_file():
        raise ValueError('Attachment absent or escapes draft folder: ' + str(relative))
    return source


def attachment_errors(draft, base):
    """Return actionable attachment-only errors without modifying data or writing files."""
    if not isinstance(draft, dict):
        return ['Draft must be a JSON object']
    items = draft.get('attachments', [])
    if not isinstance(items, list):
        return ['attachments must be an array']
    errors, seen = [], set()
    for index, item in enumerate(items):
        location = f'attachments[{index}]'
        if not isinstance(item, dict):
            errors.append(location + ' must be an object with id, path and purpose')
            continue
        aid = item.get('id')
        if not isinstance(aid, str) or not re.fullmatch(r'A\d+', aid):
            errors.append(f'{location}.id={str(aid)[:100]!r}: use A followed by digits, e.g. A01; put descriptive names in purpose. Update matching numbers[].attachment_ids explicitly; no automatic rename.')
        elif aid in seen:
            errors.append(f'{location}.id={aid!r}: duplicate attachment ID; choose an unused A-number and update references explicitly')
        else:
            seen.add(aid)
        try:
            text(item.get('purpose'), location + '.purpose')
            source = local_file(base, item.get('path'))
            if not re.fullmatch(r'\.[a-z0-9]{1,8}', source.suffix.lower()):
                raise ValueError('Attachment needs a simple file extension')
        except (ValueError, OSError) as exc:
            errors.append(location + ': ' + str(exc))
    numbers = draft.get('numbers', [])
    if not isinstance(numbers, list):
        errors.append('numbers must be an array')
    else:
        for index, item in enumerate(numbers):
            if not isinstance(item, dict):
                errors.append(f'numbers[{index}] must be an object')
                continue
            refs = item.get('attachment_ids', [])
            if not isinstance(refs, list):
                errors.append(f'numbers[{index}].attachment_ids must be an array')
            else:
                for identity in refs:
                    if not isinstance(identity, str) or identity not in seen:
                        errors.append(f'numbers[{index}].attachment_ids: absent or invalid attachment id {str(identity)[:100]!r}; declare an existing A-number with a real file')
    return errors


def render_views(corpora, draft):
    if not isinstance(draft, dict) or draft.get('schema_version') != 'paperscope-review/1.0':
        raise ValueError('Expected schema_version paperscope-review/1.0')
    numbers, locations = {}, {}
    for item in draft.get('numbers', []):
        nid = item.get('id')
        if not isinstance(nid, str) or not re.fullmatch(r'N\d+', nid) or nid in numbers:
            raise ValueError('Missing, duplicate or invalid number id')
        for key in ['value', 'units', 'conditions', 'source_locator', 'verification']:
            text(item.get(key), nid + '.' + key)
            if '{{' in item[key] or '}}' in item[key]:
                raise ValueError('Number records must contain literal values, not templates')
        if item.get('basis') not in ['source', 'calculation', 'unverified']:
            raise ValueError(nid + ': invalid basis')
        if item['basis'] == 'calculation':
            text(item.get('formula'), nid + '.formula')
        numbers[nid] = item
        locations[nid] = []
    claims = {}

    def expand(value, location, allow_claims=True):
        text(value, location)
        def replace(match):
            identity, field = match.groups()
            if identity in numbers:
                if field not in [None, 'value', 'units']:
                    raise ValueError('Invalid number field: ' + match.group())
                locations[identity].append(location)
                return numbers[identity]['units' if field == 'units' else 'value']
            if not allow_claims or identity not in claims or field not in [None, 'statement', 'reasoning', 'ref']:
                raise ValueError('Unknown claim/number or invalid template: ' + match.group())
            claim = claims[identity]
            if field == 'ref':
                return '[' + identity + ']'
            if field in ['statement', 'reasoning']:
                return claim[field]
            return claim['statement'] + ' [' + identity + ']'
        rendered = TOKEN.sub(replace, value)
        if '{{' in rendered or '}}' in rendered:
            raise ValueError('Unresolved or unsupported template in ' + location)
        return rendered

    for item in draft.get('claims', []):
        item = deepcopy(item)
        cid = item.get('id')
        if not isinstance(cid, str) or not re.fullmatch(r'C\d+', cid) or cid in claims:
            raise ValueError('Missing, duplicate or invalid claim id')
        for key in ['statement', 'reasoning']:
            item[key] = expand(item.get(key), cid + '.' + key, allow_claims=False)
        claims[cid] = item
    for nid, item in numbers.items():
        refs = item.get('evidence_ids', [])
        if not isinstance(refs, list) or any(not isinstance(cid, str) or cid not in claims for cid in refs):
            raise ValueError(nid + ': unknown evidence id')
        if item['basis'] == 'source' and not refs:
            raise ValueError(nid + ': source number must link a claim with evidence')
        if item['basis'] == 'source' and not any(claims[cid].get('evidence') for cid in refs):
            raise ValueError(nid + ': source number links only claims without evidence')
    document, compiler = compile_document(corpora, {'schema_version': '1.0',
                'source_ids': draft.get('source_ids'), 'claims': list(claims.values())})
    answer = draft.get('answer')
    if not isinstance(answer, dict) or not isinstance(answer.get('sections'), list) or not answer['sections']:
        raise ValueError('answer.sections must be a nonempty array')
    lines = []
    if answer.get('title'):
        lines += ['# ' + expand(answer['title'], 'answer.title'), '']
    for index, section in enumerate(answer['sections'], 1):
        location = f'answer.section{index}'
        if section.get('heading'):
            lines += ['## ' + expand(section['heading'], location + '.heading'), '']
        paragraphs = section.get('paragraphs')
        if not isinstance(paragraphs, list) or not paragraphs:
            raise ValueError(location + '.paragraphs must be nonempty')
        for j, paragraph in enumerate(paragraphs, 1):
            lines += [expand(paragraph, location + f'.paragraph{j}'), '']
    answer_text = '\n'.join(lines).rstrip() + '\n'
    if set(re.findall(r'\[(C\d+)\]', answer_text)) - set(claims):
        raise ValueError('Answer references undefined claims')
    comparisons = draft.get('comparisons')
    if not isinstance(comparisons, list) or not comparisons:
        raise ValueError('comparisons must contain relevant rows; use legacy format if no comparison is needed')
    buffer = io.StringIO(newline='')
    writer = csv.writer(buffer, lineterminator='\n')
    writer.writerow(['item', 'paper_setting', 'target_setting', 'comparability', 'evidence_ids'])
    for index, row in enumerate(comparisons, 1):
        if row.get('comparability') not in ['comparable', 'mismatch', 'unknown', 'not_applicable']:
            raise ValueError('Invalid comparison status')
        refs = row.get('evidence_ids', [])
        if not isinstance(refs, list) or any(not isinstance(cid, str) or cid not in claims for cid in refs):
            raise ValueError('Unknown comparison claim')
        writer.writerow([expand(row.get(k), f'comparison{index}.{k}') for k in ['item', 'paper_setting', 'target_setting']] +
                        [row['comparability'], ';'.join(refs)])
    numeric = []
    compiled_claims = {claim['id']: claim for claim in document['claims']}
    for nid, item in numbers.items():
        quotes = [ev['quote'] for cid in item.get('evidence_ids', []) for ev in compiled_claims[cid]['evidence']]
        # An absent literal is a review cue, not a verdict: figures and unit conversions may differ.
        literal_found = any(item['value'] in quote for quote in quotes) if item['basis'] == 'source' else None
        numeric.append({'id': nid, 'answer_location': '; '.join(dict.fromkeys(locations[nid])) or 'registry only; not used in generated text',
            'value': item['value'], 'basis': item['basis'], 'source_locator': item['source_locator'],
            'units_and_conditions': item['units'] + '; ' + item['conditions'],
            'formula': item.get('formula'), 'evidence_ids': item.get('evidence_ids', []),
            'calculation_id': item.get('calculation_id'),
            'verification': 'Reader-reported, not certified by assembler: ' + item['verification'],
            'attachment_ids': item.get('attachment_ids', []), 'automated_numeric_truth_verified': False,
            'literal_value_text_found_in_linked_quotes': literal_found,
            'source_alignment_review_needed': literal_found is False})
    files = {'answer.md': answer_text.encode('utf-8'), 'claims.json': encoded(document),
             'comparison.csv': buffer.getvalue().encode('utf-8'), 'numeric-review.json': encoded({'items': numeric})}
    return files, compiler


def build(draft_path, corpus_paths, out):
    draft_path, out = Path(draft_path), Path(out)
    if out.exists():
        raise ValueError('Output directory must be new; never overwrite earlier results')
    draft, corpora = read(draft_path), [read(p) for p in corpus_paths]
    errors = attachment_errors(draft, draft_path.parent)
    if errors:
        raise ValueError('\n'.join(errors))
    calculations = replay_calculations(draft)
    files, compiler = render_views(corpora, draft)
    portable = deepcopy(draft)
    attachments, original_attachments = {}, {}
    for item in portable.get('attachments', []):
        aid = item.get('id')
        if not isinstance(aid, str) or not re.fullmatch(r'A\d+', aid) or aid in attachments:
            raise ValueError('Missing, duplicate or invalid attachment id')
        text(item.get('purpose'), aid + '.purpose')
        source = local_file(draft_path.parent, item.get('path'))
        suffix = source.suffix.lower()
        if not re.fullmatch(r'\.[a-z0-9]{1,8}', suffix):
            raise ValueError('Attachment needs a simple file extension')
        relative = 'attachments/' + aid + suffix
        content = source.read_bytes()
        files[relative] = content
        original_attachments[aid] = {'original_path': item['path'], 'bundle_path': relative,
                                    'sha256': sha(content), 'purpose': item['purpose']}
        item['path'] = relative
        attachments[aid] = relative
    for item in draft.get('numbers', []):
        ids = item.get('attachment_ids', [])
        if not isinstance(ids, list) or any(not isinstance(a, str) or a not in attachments for a in ids):
            raise ValueError('Number references an absent attachment id')
    files['original-draft.json'] = draft_path.read_bytes()
    files['replay-draft.json'] = encoded(portable)
    corpus_names = []
    for i, path in enumerate(corpus_paths, 1):
        name = f'corpora/source-{i:03d}.json'
        files[name] = Path(path).read_bytes()
        corpus_names.append(name)
    for name in ['assemble_review.py', 'compile_quotes.py', 'integrity.py', 'calculate.py', 'derived_assets.py', 'render_region.py']:
        files['tools/' + name] = Path(__file__).with_name(name).read_bytes()
    dependencies = derived_assets.close(files, original_attachments, draft_path.parent.resolve(), local_file)
    derived_assets.verify(files, dependencies)
    # Preserve automatically collected images as explicit inputs for portable rebuilds.
    next_id = 1
    for path in sorted(p for p in files if p.startswith('dependencies/')):
        while 'A' + str(next_id) in attachments:
            next_id += 1
        aid = 'A' + str(next_id)
        attachments[aid] = path
        portable.setdefault('attachments', []).append({'id': aid, 'path': path,
            'purpose': 'Automatically included renderer dependency; see dependency-map.json'})
    files['replay-draft.json'] = encoded(portable)
    files['dependency-map.json'] = encoded(dependencies)
    files['calculations.json'] = encoded(calculations)
    files['claims-compile-provenance.json'] = encoded(compiler)
    provenance = {'assembler': VERSION, 'original_draft_sha256': sha(files['original-draft.json']),
        'portable_draft_sha256': sha(files['replay-draft.json']), 'attachments': original_attachments,
        'corpora': [{'bundle_path': name, 'sha256': sha(files[name])} for name in corpus_names],
        'source_statuses': [{'source_id': c['source_id'], 'source_pdf_sha256': c['source_sha256'],
            'extraction_status': c.get('extraction', {}).get('status', 'not recorded'),
            'matching_source_pdf_in_attachments': any(sha(files[p]) == c['source_sha256'] for p in attachments.values())} for c in corpora],
        'semantic_support_verified': False, 'numeric_truth_verified': False,
        'scope': 'Template consistency and literal citations only. Reader annotations are not certified history. Attachments are copied as data and never executed.'}
    files['assembly-provenance.json'] = encoded(provenance)
    out.mkdir(parents=True, exist_ok=False)
    for name, content in files.items():
        target = out / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as stream:
            stream.write(content)
    # Validate actual generated CSV before sealing the bundle. On failure leave an unsealed directory.
    errors = comparison_errors(out / 'comparison.csv', read(out / 'claims.json'))
    if errors:
        raise ValueError('; '.join(errors))
    check_data = result([])
    check_data['numeric_truth_verified'] = False
    check_data['numeric_source_alignment_review_needed'] = [item['id'] for item in read(out / 'numeric-review.json')['items'] if item['source_alignment_review_needed']]
    checks = encoded(check_data)
    (out / 'checks.json').write_bytes(checks)
    files['checks.json'] = checks
    manifest = {'schema_version': 'paperscope-bundle/1.0', 'assembler': VERSION,
                'files': {name: {'sha256': sha(content), 'bytes': len(content)} for name, content in sorted(files.items())},
                'final_views': FINAL, 'replay_draft': 'replay-draft.json', 'replay_corpora': corpus_names,
                'limitations': 'Unsigned local inventory, not external authenticity or semantic proof. File hashes detect accidental changes against this manifest; a party can replace both payload and manifest.'}
    with (out / 'manifest.json').open('xb') as stream:
        stream.write(encoded(manifest))
    return {'files': len(files), 'claims': len(draft['claims']), 'numbers': len(draft.get('numbers', [])),
            'numeric_source_alignment_review_needed': check_data['numeric_source_alignment_review_needed'],
            'integrity_checks_passed': True, 'semantic_support_verified': False}


def verify(bundle):
    bundle = Path(bundle)
    manifest = read(bundle / 'manifest.json')
    if manifest.get('schema_version') != 'paperscope-bundle/1.0':
        raise ValueError('Unsupported bundle manifest')
    for relative, item in manifest['files'].items():
        path = local_file(bundle, relative)
        if sha(path.read_bytes()) != item['sha256'] or path.stat().st_size != item['bytes']:
            raise ValueError('Bundle hash mismatch: ' + relative)
    actual = {p.relative_to(bundle).as_posix() for p in bundle.rglob('*') if p.is_file()}
    if actual != set(manifest['files']) | {'manifest.json'}:
        raise ValueError('Unregistered files in bundle')
    files, _ = render_views([read(local_file(bundle, p)) for p in manifest['replay_corpora']],
                            read(local_file(bundle, manifest['replay_draft'])))
    for name in FINAL:
        if files[name] != (bundle / name).read_bytes():
            raise ValueError('Replayed view differs: ' + name)
    draft = read(local_file(bundle, manifest['replay_draft']))
    if encoded(replay_calculations(draft)) != (bundle / 'calculations.json').read_bytes():
        raise ValueError('Replayed calculations differ')
    dependency_count = derived_assets.verify(
        {p: local_file(bundle, p).read_bytes() for p in manifest['files']}, read(bundle / 'dependency-map.json'))
    errors = comparison_errors(bundle / 'comparison.csv', read(bundle / 'claims.json'))
    if errors:
        raise ValueError('; '.join(errors))
    return {'registered_files': len(manifest['files']), 'four_views_replayed_identically': True,
            'arithmetic_replayed_identically': True, 'declared_render_dependency_edges_checked': dependency_count,
            'render_images_regenerated': False,
            'semantic_support_verified': False, 'numeric_truth_verified': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    command = sub.add_parser('build')
    command.add_argument('--draft', required=True)
    command.add_argument('--corpus', action='append', required=True)
    command.add_argument('--out', required=True)
    command = sub.add_parser('verify')
    command.add_argument('bundle')
    command = sub.add_parser('check-attachments', help='Read-only attachment ID/path/reference check; not full assembly or science validation')
    command.add_argument('--draft', required=True)
    command = sub.add_parser('replay-renders')
    command.add_argument('bundle')
    command.add_argument('--out', required=True)
    args = parser.parse_args()
    try:
        if args.command == 'check-attachments':
            errors = attachment_errors(read(Path(args.draft)), Path(args.draft).parent)
            report = {'attachment_checks_passed': not errors, 'errors': errors,
                      'semantic_support_verified': False, 'derived_dependencies_verified': False,
                      'scope': 'Attachment IDs, paths and number references only; no files changed, no scientific validation or derived-asset closure check.'}
        elif args.command == 'build':
            report = build(args.draft, args.corpus, args.out)
        elif args.command == 'verify':
            report = verify(args.bundle)
        else:
            verify(args.bundle)
            report = derived_assets.regenerate(Path(args.bundle), Path(args.out))
    except (OSError, ValueError, TypeError, KeyError, AttributeError, RuntimeError) as exc:
        parser.exit(2, f'Assembly failed: {exc}\n')
    print(json.dumps(report, ensure_ascii=False))
    if report.get('attachment_checks_passed') is False:
        return 2
    if report.get('all_render_images_byte_identical') is False:
        return 3


if __name__ == '__main__':
    sys.exit(main())
