"""Import local PDF text into page-bound evidence blocks; no OCR or semantic certification."""
import argparse
import hashlib
from importlib.metadata import version
import io
import json
import logging
from pathlib import Path
import re

VERSION = 'paperscope-pdf-ingest/0.1'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def text_blocks(text, limit=1400):
    """Keep exact extracted substrings; positions count Python Unicode characters."""
    start = 0
    while start < len(text):
        end = min(start + limit, len(text))
        if end < len(text):
            boundary = max(text.rfind('\n', start + limit // 2, end),
                           text.rfind(' ', start + limit // 2, end))
            if boundary >= 0:
                end = boundary + 1
        if text[start:end].strip():
            yield start, end, text[start:end]
        start = end


def ingest(pdf, source_id, out, expected_sha=None, title=None, doi=None, license_name=None):
    pdf, out = Path(pdf), Path(out)
    if out.exists():
        raise ValueError('Output directory must be new; existing sources are never overwritten')
    if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_.-]{0,79}', source_id):
        raise ValueError('source-id must be 1..80 ASCII letters/digits/dots/underscores/hyphens')
    raw = pdf.read_bytes()
    source_sha = digest(raw)
    if expected_sha is not None and source_sha != expected_sha.lower():
        raise ValueError('Source PDF SHA256 differs from registered source')
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError('PDF text import requires pypdf. Use an installed PDF-capable Python; no dependency is installed automatically.') from exc
    captured = io.StringIO()
    handler = logging.StreamHandler(captured)
    logger = logging.getLogger('pypdf')
    logger.addHandler(handler)
    try:
        try:
            reader = PdfReader(io.BytesIO(raw), strict=False)
            if reader.is_encrypted:
                raise ValueError('Encrypted PDFs are not imported. Provide an authorised unencrypted local copy; do not put passwords in the draft.')
            count = len(reader.pages)
            if not count:
                raise ValueError('PDF contains no pages')
            metadata = reader.metadata
            pdf_title = metadata.title if metadata and isinstance(metadata.title, str) else None
            pages, blocks = [], []
            for index, page in enumerate(reader.pages, 1):
                issue = None
                try:
                    text = (page.extract_text(extraction_mode='plain') or '').replace('\r\n', '\n').replace('\r', '\n')
                except Exception as exc:
                    text, issue = '', f'{type(exc).__name__}: {exc}'
                chars = sum(ch.isalnum() for ch in text)
                status = 'extraction_failed' if issue else 'empty_text' if chars == 0 else 'low_text' if chars < 40 else 'text_extracted'
                rotation = page.get('/Rotate', 0)
                pages.append({'physical_page': index, 'status': status, 'alphanumeric_chars': chars,
                              'rotation_from_pdf': str(rotation), 'error': issue, 'text': text})
                for number, (start, end, body) in enumerate(text_blocks(text), 1):
                    blocks.append({'block_id': f'p{index:03d}-b{number:03d}', 'pdf_page': index,
                                   'text': body, 'extracted_page_span': [start, end]})
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError(f'PDF could not be parsed: {type(exc).__name__}: {exc}') from exc
    finally:
        logger.removeHandler(handler)
    unresolved = [p['physical_page'] for p in pages if p['status'] != 'text_extracted']
    status = 'no_extractable_text' if not blocks else 'partial_text' if unresolved else 'text_extracted'
    corpus = {'schema_version': 'paperscope-corpus/1.0', 'source_id': source_id,
              'source_sha256': source_sha, 'title': title or pdf_title,
              'doi': doi, 'license': license_name,
              'metadata_note': 'Title may be unverified PDF metadata; DOI/license only supplied explicitly, never inferred.',
              'extraction': {'library': 'pypdf', 'version': version('pypdf'),
                             'mode': 'plain', 'normalization': 'CRLF/CR converted to LF only',
                             'status': status, 'limitations': 'Text order, columns, equations and tables may differ from the visual page. No OCR or verification of scientific contents.'},
              'blocks': blocks}
    files = {'source.pdf': raw, 'corpus.json': encode(corpus),
             'pages.json': encode({'source_id': source_id, 'source_pdf_sha256': source_sha, 'pages': pages}),
             'sources.json': encode({'sources': [{'source_id': source_id, 'kind': 'pdf',
                                                 'path': 'source.pdf', 'sha256': source_sha}]})}
    provenance = {'importer': VERSION, 'script_sha256': digest(Path(__file__).read_bytes()),
                  'source_pdf_sha256': source_sha, 'expected_hash_checked': expected_sha is not None,
                  'physical_pages': count, 'blocks': len(blocks), 'status': status,
                  'pages_requiring_visual_review': unresolved,
                  'parser_warnings': captured.getvalue().splitlines(),
                  'source_pdf_authenticity_verified': False, 'semantic_support_verified': False,
                  'note': 'A hash identifies the supplied file; it does not establish publisher authenticity. Empty/low-text pages may be scanned or legitimately sparse. Do not claim full coverage from successful extraction.',
                  'files': {name: {'sha256': digest(data), 'bytes': len(data)} for name, data in files.items()}}
    files['ingest-provenance.json'] = encode(provenance)
    out.mkdir(parents=True, exist_ok=False)
    for name, data in files.items():
        with (out / name).open('xb') as stream:
            stream.write(data)
    return provenance


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pdf', required=True)
    parser.add_argument('--source-id', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--expected-sha256')
    parser.add_argument('--title')
    parser.add_argument('--doi')
    parser.add_argument('--license')
    args = parser.parse_args()
    try:
        result = ingest(args.pdf, args.source_id, args.out, args.expected_sha256, args.title, args.doi, args.license)
    except (OSError, ValueError, RuntimeError) as exc:
        parser.exit(2, f'Import failed: {exc}\n')
    print(json.dumps({k: result[k] for k in ['status', 'physical_pages', 'blocks', 'pages_requiring_visual_review']}, ensure_ascii=False))
    return 0 if result['status'] == 'text_extracted' else 3


if __name__ == '__main__':
    raise SystemExit(main())
