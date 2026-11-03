"""Close declared PDF-render dependencies while preserving original provenance bytes."""
import hashlib
import json
from pathlib import Path


def sha(data):
    return hashlib.sha256(data).hexdigest()


def render_record(data):
    try:
        obj = json.loads(data)
    except (ValueError, UnicodeError):
        return None
    if isinstance(obj, dict) and 'source_pdf_sha256' in obj and 'retained_rectangle' in obj and 'files' in obj:
        if not isinstance(obj['files'], dict) or not obj['files']:
            raise ValueError('Malformed render provenance')
        return obj
    return None


def close(files, originals, draft_base, local_file):
    edges = []
    # Only registered attachments, never arbitrary filesystem scans.
    for aid, item in originals.items():
        provenance = render_record(files[item['bundle_path']])
        if provenance is None:
            continue
        refs = [('source_pdf', provenance['source_pdf_sha256']),
                ('renderer_script', provenance['script_sha256'])]
        for name, details in provenance['files'].items():
            digest = details['sha256']
            matches = [p for p, content in files.items() if sha(content) == digest]
            if not matches:
                original = local_file(draft_base, item['original_path'])
                candidate = local_file(draft_base, (original.parent / name).relative_to(draft_base.resolve()).as_posix())
                data = candidate.read_bytes()
                if sha(data) != digest:
                    raise ValueError('Render dependency hash mismatch: ' + name)
                suffix = candidate.suffix.lower()
                if suffix != '.png':
                    raise ValueError('Expected PNG render dependency')
                relative = 'dependencies/' + digest + suffix
                files[relative] = data
            refs.append((name, digest))
        for role, digest in refs:
            matches = sorted(p for p, content in files.items() if sha(content) == digest)
            if not matches:
                raise ValueError('Missing render dependency: ' + role + ' for ' + aid)
            edges.append({'provenance': item['bundle_path'], 'role': role,
                          'path': matches[0], 'sha256': digest})
    return {'schema_version': 'paperscope-dependencies/1.0', 'edges': edges,
            'scope': 'Declared renderer source/script/image hash closure; not regeneration or scientific validation.'}


def verify(files, graph):
    expected = []
    for path, data in files.items():
        if not path.startswith('attachments/'):
            continue
        obj = render_record(data)
        if obj is not None:
            expected.extend((path, role, digest) for role, digest in
                            [('source_pdf', obj['source_pdf_sha256']), ('renderer_script', obj['script_sha256'])] +
                            [(name, item['sha256']) for name, item in obj['files'].items()])
    observed = []
    for edge in graph['edges']:
        if edge['path'] not in files or sha(files[edge['path']]) != edge['sha256']:
            raise ValueError('Dependency missing or altered')
        observed.append((edge['provenance'], edge['role'], edge['sha256']))
    if sorted(expected) != sorted(observed):
        raise ValueError('Dependency graph does not match render provenance')
    return len(observed)


def regenerate(bundle, out):
    from render_region import render
    if out.exists():
        raise ValueError('Render replay output must be new')
    graph = json.loads((bundle / 'dependency-map.json').read_text(encoding='utf-8'))
    grouped = {}
    for edge in graph['edges']:
        grouped.setdefault(edge['provenance'], {})[edge['role']] = edge
    out.mkdir(parents=True, exist_ok=False)
    results = []
    for index, (path, edges) in enumerate(sorted(grouped.items()), 1):
        original = json.loads((bundle / path).read_text(encoding='utf-8'))
        fresh = render(bundle / edges['source_pdf']['path'], original['physical_page_one_based'],
                       original['retained_rectangle'], original['region_scale_pixels_per_canvas_unit'],
                       out / f'render-{index:03d}', original['source_pdf_sha256'])
        matches = {name: fresh['files'][name]['sha256'] == item['sha256']
                   for name, item in original['files'].items()}
        results.append({'original_provenance': path, 'image_hash_matches': matches,
                        'original_renderer': original['renderer'], 'replay_renderer': fresh['renderer']})
    report = {'render_records': results,
              'all_render_images_byte_identical': all(all(r['image_hash_matches'].values()) for r in results),
              'render_record_count': len(results),
              'scope': 'Current trusted renderer re-execution; versions recorded. No OCR, source authenticity or scientific validation.'}
    (out / 'render-replay.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return report
