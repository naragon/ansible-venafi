from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import unittest
import json
from unittest.mock import MagicMock, patch
from ansible_collections.venafi.cloud.plugins.module_utils.venafi_cloud import VenafiCloudAPI

class TestVenafiCloudAPI(unittest.TestCase):

    def setUp(self):
        self.mock_module = MagicMock()
        self.api = VenafiCloudAPI(self.mock_module, "test-api-key")

    @patch('ansible_collections.venafi.cloud.plugins.module_utils.venafi_cloud.fetch_url')
    def test_request_success(self, mock_fetch_url):
        # Mock response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"status": "success"}).encode('utf-8')
        mock_fetch_url.return_value = (mock_response, {"status": 200})

        result = self.api.request("GET", "/test")

        self.assertEqual(result, {"status": "success"})
        mock_fetch_url.assert_called_once()
        args, kwargs = mock_fetch_url.call_args
        self.assertEqual(kwargs['headers']['tppl-api-key'], "test-api-key")

    @patch('ansible_collections.venafi.cloud.plugins.module_utils.venafi_cloud.fetch_url')
    def test_request_fail(self, mock_fetch_url):
        # Mock error response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"message": "Invalid API Key"}).encode('utf-8')
        mock_fetch_url.return_value = (mock_response, {"status": 401, "msg": "Unauthorized"})

        self.api.request("GET", "/test")

        self.mock_module.fail_json.assert_called_once_with(
            msg="API request failed: 401 - Invalid API Key",
            status=401,
            url="https://api.venafi.cloud/test"
        )

if __name__ == '__main__':
    unittest.main()
