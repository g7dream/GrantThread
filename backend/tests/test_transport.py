"""Cloud transport checks use injected repositories and bytes; no AWS calls."""
import base64
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from grantthread.api import Binary, dispatch
from grantthread.errors import DomainError
from grantthread.finance_service import FinancialService
from grantthread.lambda_handler import MAX_INLINE_BINARY_BYTES, handler
from grantthread.repository import SQLiteRepository
from grantthread.seed import IDENTITIES, seed_all
from grantthread.storage import LocalStorage


class TransportContracts(unittest.TestCase):
    def test_single_confirmation_rejects_body_id_substitution(self):
        with tempfile.TemporaryDirectory() as temp, patch.dict(os.environ, {'GRANTTHREAD_MODE': 'local', 'GRANTTHREAD_DATA_DIR': temp}):
            repo, storage = SQLiteRepository(), LocalStorage()
            seed_all(repo, storage)
            finance = FinancialService(IDENTITIES['brightpath'], repo, storage)
            def draft(reference):
                return finance.create_entry({'grantId': 'digital-belonging', 'kind': 'expense', 'date': '2026-04-15',
                    'description': 'Fictional supplies', 'reference': reference, 'currency': 'EUR', 'amount': '10',
                    'category': '1.4 Goods and Supplies', 'conversionMode': 'same_currency'})
            first, second = draft('A'), draft('B')
            before = repo.read('brightpath')
            with self.assertRaises(DomainError):
                dispatch('POST', '/financials/entries/' + first['id'] + '/confirm',
                         {'id': second['id'], 'expectedVersion': second['version']}, IDENTITIES['brightpath'], repo, storage)
            self.assertEqual(repo.read('brightpath'), before)
            result = dispatch('POST', '/financials/entries/' + first['id'] + '/confirm',
                              {'expectedVersion': first['version']}, IDENTITIES['brightpath'], repo, storage)
            self.assertEqual(result['id'], first['id'])
            self.assertEqual(result['status'], 'confirmed')
            self.assertEqual(repo.read('brightpath')['financeEntries'][second['id']]['status'], 'draft')

    def cloud(self, body='', binary=None):
        event = {'rawPath': '/api/reports/test/pdf', 'requestContext': {'http': {'method': 'GET'}}, 'body': body, 'isBase64Encoded': True}
        with patch.dict(os.environ, {'GRANTTHREAD_MODE': 'aws'}), \
             patch('grantthread.lambda_handler.get_repository'), \
             patch('grantthread.lambda_handler.gateway_identity', return_value=IDENTITIES['brightpath']), \
             patch('grantthread.lambda_handler.dispatch', return_value=binary):
            return handler(event, None)

    def test_binary_response_limit_is_a_clear_error_before_gateway_failure(self):
        response = self.cloud(binary=Binary(b'x' * (MAX_INLINE_BINARY_BYTES + 1), 'application/pdf', 'report.pdf'))
        self.assertEqual(response['statusCode'], 413)
        self.assertEqual(json.loads(response['body'])['code'], 'export_too_large')
        self.assertNotIn('isBase64Encoded', response)

    def test_supported_binary_bytes_and_filename_are_preserved_safely(self):
        raw = b'%PDF-1.4\nfictional'
        response = self.cloud(binary=Binary(raw, 'application/pdf', 'test"\r\n.pdf'))
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(base64.b64decode(response['body']), raw)
        self.assertEqual(response['headers']['Content-Disposition'], 'attachment; filename="test.pdf"')

    def test_largest_supported_binary_fits_within_lambda_response_envelope(self):
        response = self.cloud(binary=Binary(b'x' * MAX_INLINE_BINARY_BYTES, 'application/pdf', 'report.pdf'))
        self.assertEqual(response['statusCode'], 200)
        self.assertLess(len(json.dumps(response).encode()), 6 * 1024 * 1024)

    def test_malformed_base64_is_not_silently_treated_as_an_empty_request(self):
        response = self.cloud(body='!!!!')
        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(json.loads(response['body'])['code'], 'invalid_request')


if __name__ == '__main__':
    unittest.main()
