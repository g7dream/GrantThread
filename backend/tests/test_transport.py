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
from grantthread.api import Binary, dispatch, source_download
from grantthread.errors import DomainError
from grantthread.finance_service import FinancialService
from grantthread.lambda_handler import MAX_INLINE_BINARY_BYTES, handler
from grantthread.repository import SQLiteRepository
from grantthread.seed import IDENTITIES, seed_all
from grantthread.storage import LocalStorage


class TransportContracts(unittest.TestCase):
    def test_cloud_preflight_returns_no_content_without_authentication_or_data_access(self):
        with patch.dict(os.environ, {'GRANTTHREAD_MODE': 'aws'}), \
             patch('grantthread.lambda_handler.get_repository') as repository, \
             patch('grantthread.lambda_handler.gateway_identity') as authenticate, \
             patch('grantthread.lambda_handler.dispatch') as dispatch_request:
            for path in ('/api/health', '/api/session', '/api/jobs'):
                with self.subTest(path=path):
                    event = {'rawPath': path, 'requestContext': {'http': {'method': 'OPTIONS'}},
                             'body': 'invalid base64 must not be parsed', 'isBase64Encoded': True}
                    self.assertEqual(handler(event, None),
                                     {'statusCode': 204, 'headers': {'Cache-Control': 'no-store'}, 'body': ''})
            repository.assert_not_called()
            authenticate.assert_not_called()
            dispatch_request.assert_not_called()

    def test_preflight_does_not_bypass_cloud_configuration_guard(self):
        with patch.dict(os.environ, {'GRANTTHREAD_MODE': 'local'}), \
             patch('grantthread.lambda_handler.get_repository') as repository:
            result = handler({'rawPath': '/api/session', 'requestContext': {'http': {'method': 'OPTIONS'}}}, None)
            self.assertEqual(result['statusCode'], 503)
            repository.assert_not_called()

    def test_only_api_options_bypasses_authentication(self):
        with patch.dict(os.environ, {'GRANTTHREAD_MODE': 'aws'}), \
             patch('grantthread.lambda_handler.get_repository') as repository, \
             patch('grantthread.lambda_handler.dispatch') as dispatch_request:
            for method, path in (('GET', '/api/session'), ('POST', '/api/jobs'),
                                 ('OPTIONS', '/outside'), ('OPTIONS', '/apiculture/session')):
                with self.subTest(method=method, path=path):
                    result = handler({'rawPath': path, 'requestContext': {'http': {'method': method}}}, None)
                    self.assertEqual(result['statusCode'], 401)
                    self.assertEqual(json.loads(result['body'])['code'], 'unauthorised')
            repository.return_value.read_key.assert_not_called()
            dispatch_request.assert_not_called()

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

    def test_private_source_url_is_noncacheable_json_instead_of_cross_origin_redirect(self):
        descriptor = source_download(('https://synthetic-bucket.example.test/file?signature=fictional', 'text/plain', 'Invoice.txt'))
        response = self.cloud(binary=descriptor)
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(response['headers']['Content-Type'], 'application/json')
        self.assertEqual(response['headers']['Cache-Control'], 'no-store')
        self.assertNotIn('Location', response['headers'])
        self.assertEqual(json.loads(response['body']), {'downloadUrl': 'https://synthetic-bucket.example.test/file?signature=fictional',
                                                      'contentType': 'text/plain', 'filename': 'Invoice.txt'})

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
