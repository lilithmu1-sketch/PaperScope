from copy import deepcopy
import json
from pathlib import Path
import unittest
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import bohrium_bridge as bridge

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / 'experiments/bohrium/recorded'


class BridgeTests(unittest.TestCase):
    def test_actual_six_calls_and_all_primary_pdf_hashes(self):
        report = bridge.build_report(ROOT, PACK)
        self.assertEqual(len(report['calls']), 6)
        self.assertEqual(report['billing_channels'], {'quota': 6})
        self.assertEqual(report['references_returned'], 118)
        self.assertEqual(report['references_with_literal_title_location'], 101)
        self.assertEqual([c['status'] for c in report['calls'][:2]], ['empty_graph', 'empty_graph'])
        self.assertEqual([c['status'] for c in report['calls'][-2:]], ['no_matches', 'no_matches'])
        self.assertFalse(report['semantic_support_verified'])

    def test_wrong_seed_doi_is_rejected(self):
        response = bridge.read(PACK / '04-reference/response.json')
        response['data']['items'][0]['doi'] = '10.0000/wrong'
        source = bridge.load_sources(ROOT)['10.1038/s42256-025-01055-1']
        with self.assertRaisesRegex(ValueError, 'seed paper DOI mismatch'):
            bridge.summarise_response(response, ['lkm', 'reference', '--doi', '10.1038/s42256-025-01055-1'], source)

    def test_unqueried_references_are_not_an_empty_success(self):
        response = bridge.read(PACK / '04-reference/response.json')
        response['data']['items'][0]['references'] = None
        source = bridge.load_sources(ROOT)['10.1038/s42256-025-01055-1']
        with self.assertRaisesRegex(ValueError, 'not queried'):
            bridge.summarise_response(response, ['lkm', 'reference', '--doi', '10.1038/s42256-025-01055-1'], source)

    def test_short_titles_are_not_weakly_matched(self):
        corpus = {'source_id': 's', 'blocks': [{'block_id': 'b', 'pdf_page': 1, 'text': 'A short IRNet mention.'}]}
        self.assertEqual(bridge.locate_title('IRNet', corpus), [])

    def test_paid_channel_is_not_rendered_as_all_free(self):
        report = bridge.build_report(ROOT, PACK)
        report['all_recorded_requests_used_free_pool'] = False
        report['billing_channels'] = {'balance': 6}
        self.assertNotIn('全部回执均为quota免费池', bridge.markdown(report))


if __name__ == '__main__':
    unittest.main()
