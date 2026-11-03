"""Compile literal evidence from source/block IDs; never judge scientific truth.

Drafts use the existing claims schema, but replace each evidence quote with an
optional ``span: [start, end]`` in Unicode character offsets. Without a span,
copy the entire block. No model-written quote or fuzzy matching is accepted.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
from integrity import claims_errors, comparison_errors, corpus_errors

VERSION = 'paperscope-citation-compiler/0.3'


def compile_document(corpora: list[dict], draft: dict) -> tuple[dict, dict]:
    index = {}
    for corpus in corpora:
        errors = corpus_errors(corpus)
        if errors:
            raise ValueError('; '.join(errors))
        sid = corpus['source_id']
        if sid in index:
            raise ValueError('Duplicate source: ' + sid)
        index[sid] = {b['block_id']: b for b in corpus['blocks']}
    if not isinstance(draft, dict) or not isinstance(draft.get('claims'), list):
        raise ValueError('Draft must contain a claims array')
    document = deepcopy(draft)
    selections = []
    for claim in document['claims']:
        if not isinstance(claim, dict) or not isinstance(claim.get('evidence'), list):
            raise ValueError('Every claim needs an evidence array')
        for number, ev in enumerate(claim['evidence']):
            if not isinstance(ev, dict) or set(ev) - {'source_id', 'block_id', 'span'}:
                raise ValueError('Evidence accepts only source_id, block_id and optional span; do not supply a quote')
            sid, bid = ev.get('source_id'), ev.get('block_id')
            if not isinstance(sid, str) or not isinstance(bid, str):
                raise ValueError('Missing source/block identifiers')
            canonical = bid[len(sid) + 1:] if bid.startswith(sid + ':') else bid
            if sid not in index or canonical not in index[sid]:
                raise ValueError('Unknown source/block: ' + sid + ':' + bid)
            block = index[sid][canonical]
            body = block['text']
            span = ev.pop('span', [0, len(body)])
            if (not isinstance(span, list) or len(span) != 2
                    or any(type(x) is not int for x in span)
                    or not 0 <= span[0] < span[1] <= len(body)):
                raise ValueError('Invalid Unicode character span')
            quote = body[span[0]:span[1]]
            if len(quote) > 2000:
                raise ValueError('Quote exceeds 2000 characters; specify an explicit smaller span')
            ev['quote'] = quote
            selections.append({'claim_id': claim.get('id'), 'evidence_index': number,
                               'source_id': sid, 'block_id': canonical, 'pdf_page': block['pdf_page'],
                               'span': span, 'block_sha256': hashlib.sha256(body.encode('utf-8')).hexdigest()})
    errors = claims_errors(corpora, document)
    if errors:
        raise ValueError('; '.join(errors))
    return document, {'compiler': VERSION, 'integrity_checks_passed': True,
                      'semantic_support_verified': False, 'primary_pdf_authenticity_verified': False,
                      'selections': selections,
                      'boundary': 'Literal corpus selection only. Claim truth, omitted context and corpus/PDF agreement require separate review.'}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--corpus', type=Path, action='append', required=True)
    p.add_argument('--expected-corpus-sha256', action='append', default=[])
    p.add_argument('--draft', type=Path, required=True)
    p.add_argument('--answer', type=Path, help='Also validate claim IDs cited in an existing answer')
    p.add_argument('--comparison', type=Path, help='Also validate the existing comparison CSV')
    output = p.add_mutually_exclusive_group(required=True)
    output.add_argument('--out', type=Path, help='Create a fresh output directory')
    output.add_argument('--claims-out', type=Path, help='Create a new claims file alongside existing run artifacts')
    args = p.parse_args()
    try:
        if args.out:
            if args.out.exists():
                raise ValueError('Refusing to overwrite existing output directory')
            claims_path = args.out / 'claims.json'
            provenance_path = args.out / 'compile-provenance.json'
        else:
            claims_path = args.claims_out
            provenance_path = claims_path.with_name(claims_path.stem + '-compile-provenance.json')
            if claims_path.exists() or provenance_path.exists():
                raise ValueError('Refusing to overwrite existing claims or provenance file')
        if args.expected_corpus_sha256 and len(args.expected_corpus_sha256) != len(args.corpus):
            raise ValueError('Supply one expected SHA256 per corpus, in the same order')
        corpora, sources = [], []
        for i, path in enumerate(args.corpus):
            raw = path.read_bytes()
            digest = hashlib.sha256(raw).hexdigest()
            expected = args.expected_corpus_sha256[i] if args.expected_corpus_sha256 else None
            if expected is not None and digest != expected:
                raise ValueError('Registered corpus hash mismatch')
            corpora.append(json.loads(raw.decode('utf-8-sig')))
            sources.append({'file_name': path.name, 'sha256': digest,
                            'expected_sha256_verified': expected is not None})
        raw_draft = args.draft.read_bytes()
        document, provenance = compile_document(corpora, json.loads(raw_draft.decode('utf-8-sig')))
        cross_errors = []
        if args.comparison:
            cross_errors.extend(comparison_errors(args.comparison, document))
        if args.answer:
            references = set(re.findall(r'\[([A-Z]\d+)\]', args.answer.read_text(encoding='utf-8-sig')))
            ids = {c['id'] for c in document['claims']}
            if references - ids:
                cross_errors.append('Answer references undefined claim IDs: ' + ','.join(sorted(references - ids)))
        if cross_errors:
            raise ValueError('; '.join(cross_errors))
        provenance.update(answer_reference_check_performed=bool(args.answer), comparison_check_performed=bool(args.comparison))
        provenance.update(corpora=sources, draft_sha256=hashlib.sha256(raw_draft).hexdigest())
        if args.out:
            args.out.mkdir(parents=True, exist_ok=False)
        else:
            claims_path.parent.mkdir(parents=True, exist_ok=True)
        for path, data in [(claims_path, document), (provenance_path, provenance)]:
            with path.open('x', encoding='utf-8') as stream:
                stream.write(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
        print(json.dumps({'claims': len(document['claims']), 'evidence': len(provenance['selections']),
                          'integrity_checks_passed': True, 'semantic_support_verified': False}))
        return 0
    except (OSError, ValueError, TypeError) as error:
        print(json.dumps({'ok': False, 'error': str(error)}, ensure_ascii=False))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
