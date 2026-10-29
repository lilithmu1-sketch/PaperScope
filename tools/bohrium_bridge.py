"""Offline bridge from recorded Bohrium responses to registered primary sources.

No network, billing, model calls, fuzzy semantic verification, or answer bank.
Literal title matches locate reading context; they do not validate claims.
"""
from __future__ import annotations
import argparse
from collections import Counter
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import unicodedata


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def bounded(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('Input path escapes project')
    return path


def normal_title(text):
    return ''.join(c for c in unicodedata.normalize('NFKC', text).casefold() if c.isalnum())


def locate_title(title, corpus):
    key = normal_title(title)
    if len(key) < 25:
        return []
    return [{'source_id': corpus['source_id'], 'block_id': b['block_id'],
             'pdf_page': b['pdf_page'], 'block_sha256': hashlib.sha256(b['text'].encode('utf-8')).hexdigest()}
            for b in corpus['blocks'] if key in normal_title(b['text'])]


def load_sources(project):
    sources = {}
    for item in read(project / 'materials/sources.json')['sources']:
        if item['kind'] != 'pdf':
            continue
        source_id = item['source_id']
        if not re.fullmatch(r'[A-Za-z0-9_-]+', source_id):
            raise ValueError('Invalid source identifier')
        pdf = bounded(project, item['path'])
        if digest(pdf) != item['sha256']:
            raise ValueError('Registered primary PDF hash mismatch')
        path = bounded(project, f'materials/corpus/{source_id}.json')
        corpus = read(path)
        if corpus['source_id'] != source_id or corpus['source_sha256'] != item['sha256']:
            raise ValueError('Corpus source metadata mismatch')
        if corpus['doi'].casefold() != item['doi'].casefold():
            raise ValueError('Corpus DOI mismatch')
        doi = item['doi'].casefold()
        if doi in sources:
            raise ValueError('Ambiguous registered DOI')
        sources[doi] = {'corpus': corpus, 'corpus_sha256': digest(path),
                        'primary_pdf_sha256_verified': item['sha256']}
    return sources


def expected_doi(operation):
    for flag in ['--doi']:
        if flag in operation:
            return operation[operation.index(flag) + 1].casefold()
    raise ValueError('Recorded operation must be DOI scoped')


def summarise_response(response, operation, source):
    doi = expected_doi(operation)
    corpus = source['corpus']
    if doi != corpus['doi'].casefold():
        raise ValueError('Operation and registered source DOI differ')
    data = response.get('data', {})
    kind = operation[1]
    report = {'operation': kind, 'doi': doi, 'api_ok': response.get('ok'),
              'request_id': response.get('meta', {}).get('request_id'),
              'cli_version': response.get('meta', {}).get('cli_version'),
              'billing': response.get('notice', {}).get('billing'),
              'semantic_support_verified': False}
    if kind == 'search':
        variables = data.get('variables', [])
        report.update(status='no_matches' if not variables else 'retrieved_candidates_require_review',
                      query=operation[2], returned_variables=len(variables), has_more=data.get('has_more'))
        return report
    items = data.get('items', [])
    if len(items) != 1:
        raise ValueError('Expected exactly one DOI-resolved paper')
    seed = items[0].get('paper', {}) if kind == 'graph' else items[0]
    if (seed.get('doi') or '').casefold() != doi:
        raise ValueError('Returned seed paper DOI mismatch')
    report['paper_id'] = seed.get('id')
    if kind == 'graph':
        graph = items[0].get('graph', {})
        nodes, edges = graph.get('nodes', []), graph.get('edges', [])
        report.update(status='graph_available' if nodes else 'empty_graph',
                      nodes=len(nodes), edges=len(edges), error=response.get('error'))
    elif kind == 'reference':
        if response.get('ok') is not True:
            raise ValueError('Do not import failed reference retrieval as evidence')
        refs = items[0].get('references')
        if not isinstance(refs, list):
            raise ValueError('References were not queried; null is not an empty list')
        rows = []
        for index, ref in enumerate(refs):
            title = ref.get('en_title') or ''
            matches = locate_title(title, corpus)
            rows.append({'response_index': index, 'title': title, 'doi': ref.get('doi') or '',
                         'paper_id': ref.get('id') or '', 'primary_title_matches': matches,
                         'title_match_status': 'literal_normalised_title_found' if matches else 'not_verified_by_literal_match',
                         'reference_doi_verified_against_primary_source': False,
                         'scientific_claim_verified': False})
        report.update(status='bibliography_returned', references=len(rows),
                      title_located=sum(bool(r['primary_title_matches']) for r in rows), entries=rows)
    else:
        raise ValueError('Unsupported recorded operation')
    return report


def build_report(project, responses):
    sources = load_sources(project)
    ledger = read(responses / 'budget-ledger.json')
    requests = ledger['requests']
    if len(requests) > 10 or sum((Decimal(r['reserved_nominal_cny']) for r in requests), Decimal('0')) > Decimal('0.50'):
        raise ValueError('Recorded request budget exceeds authorised ceiling')
    reports = []
    for request in requests:
        number, operation = request['number'], request['operation']
        if type(number) is not int or not 1 <= number <= 10 or operation[1] not in ['graph', 'reference', 'search']:
            raise ValueError('Invalid recorded request')
        path = bounded(responses, f'{number:02d}-{operation[1]}/response.json')
        if digest(path) != request['response_sha256']:
            raise ValueError('Captured response hash mismatch')
        doi = expected_doi(operation)
        if doi not in sources:
            raise ValueError('DOI is not registered to a local primary PDF')
        report = summarise_response(read(path), operation, sources[doi])
        report.update(number=number, captured_response_sha256=digest(path),
                      capture_kind=ledger.get('response_kind', 'original_cli_response'))
        reports.append(report)
    channels = Counter((r.get('billing') or {}).get('channel', 'not_reported') for r in reports)
    refs = [r for r in reports if r['operation'] == 'reference']
    return {'schema': 'paperscope-bohrium-bridge/0.1', 'calls': reports,
            'billing_channels': dict(channels), 'nominal_reserved_cny': ledger['reserved_nominal_cny'],
            'actual_charge_amount_aggregated': False, 'actual_charge_amount_cny': None,
            'all_recorded_requests_used_free_pool': bool(reports) and channels.get('quota', 0) == len(reports),
            'references_returned': sum(r['references'] for r in refs),
            'references_with_literal_title_location': sum(r['title_located'] for r in refs),
            'sources': {doi: {k: v for k, v in item.items() if k != 'corpus'} for doi, item in sources.items()},
            'semantic_support_verified': False, 'corpus_primary_pdf_text_equivalence_verified': False,
            'limitations': ['Literal title location is not a correctness rate, DOI verification, bibliography completeness, or scientific support.',
                           'Unmatched titles require further review; they are not automatically wrong references.',
                           'The two scoped queries returning no matches do not prove absence under every possible query.',
                           'This uses Bohrium CLI, not the scientific-space web chat. No graph reasoning was obtained.',
                           'The Matbench primary PDF is the registered historical snapshot; current performance must account for its separate correction.']}


def markdown(report):
    def escape(value):
        return re.sub(r'([\\`*_{}\[\]()<>#+!|])', r'\\\1', str(value)).replace('\n', ' ')
    lines = ['# 玻尔实际接入核验', '',
             f"记录{len(report['calls'])}次请求，按标价预留{report['nominal_reserved_cny']}元；计费渠道：{report['billing_channels']}。",
             ('全部回执均为quota免费池。' if report['all_recorded_requests_used_free_pool'] else '并非全部回执使用免费池，请核查逐次计费渠道。') + ' 本工具不汇总人民币实扣额，不用标价冒充实扣金额。', '',
             f"参考文献返回{report['references_returned']}条，其中{report['references_with_literal_title_location']}条标题可在本地原文块按确定性规则定位。这不是引用准确率。", '',
             '## 逐次结果', '', '| 序号 | 操作 | DOI | 结果 | 免费池剩余 |', '|---|---|---|---|---:|']
    for call in report['calls']:
        lines.append('| ' + ' | '.join(escape(x) for x in [call['number'], call['operation'], call['doi'], call['status'], (call.get('billing') or {}).get('remaining', '未返回')]) + ' |')
    lines += ['', '## 参考文献定位', '', '标题经NFKC、大小写和非字母数字字符规范化后，长度不少于25个字符才作逐字连续匹配。以下块号指向完整本地原文；没有用标题匹配来判定论文结论。', '']
    for call in report['calls']:
        if call['operation'] != 'reference':
            continue
        lines += [f"### {escape(call['doi'])}", '', '| 返回标题 | 平台DOI（未单独验证） | 本地原文位置 |', '|---|---|---|']
        for row in call['entries']:
            positions = '; '.join(f"{m['source_id']}:{m['block_id']} / PDF p{m['pdf_page']}" for m in row['primary_title_matches']) or '尚未由逐字匹配验证'
            lines.append('| ' + ' | '.join(escape(x) for x in [row['title'], row['doi'], positions]) + ' |')
    lines += ['', '## 解释边界', ''] + ['- ' + text for text in report['limitations']]
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--responses', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise ValueError('Refusing to overwrite existing output directory')
    report = build_report(args.project, args.responses)
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    (args.out / '核验报告.md').write_text(markdown(report), encoding='utf-8')
    print(json.dumps({k: report[k] for k in ['billing_channels', 'references_returned', 'references_with_literal_title_location', 'semantic_support_verified']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
