from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import unittest
from unittest.mock import MagicMock, patch
from ansible_collections.venafi.cloud.plugins.modules import certificate_create

class TestCertificateCreate(unittest.TestCase):

    def setUp(self):
        self.mock_module = MagicMock()
        self.mock_module.params = {
            'api_key': 'test-api-key',
            'base_url': 'https://api.venafi.cloud',
            'application_id': 'app-id',
            'template_id': 'tpl-id',
            'common_name': 'www.example.com',
            'organization': 'Org',
            'organizational_units': ['IT'],
            'locality': 'SLC',
            'state': 'UT',
            'country': 'US',
            'sans': {'dns_names': ['www.example.com']},
            'key_type': 'RSA',
            'key_length': 2048,
            'key_curve': None,
            'validity_period': 'P365D'
        }

    @patch('ansible_collections.venafi.cloud.plugins.modules.certificate_create.VenafiCloudAPI')
    @patch('ansible_collections.venafi.cloud.plugins.modules.certificate_create.AnsibleModule')
    def test_main_idempotent(self, mock_ansible_module, mock_api_class):
        # Setup mocks
        mock_ansible_module.return_value = self.mock_module
        mock_api_instance = mock_api_class.return_value
        
        # Mock existing valid certificate
        mock_api_instance.search_certificates.return_value = {
            "certificates": [
                {
                    "id": "existing-id",
                    "validityEnd": "2099-01-01T00:00:00.000Z"
                }
            ]
        }

        # Run main
        certificate_create.main()

        # Assertions
        self.mock_module.exit_json.assert_called_once()
        args, kwargs = self.mock_module.exit_json.call_args
        self.assertFalse(kwargs['changed'])
        self.assertEqual(kwargs['certificate_request']['certificateIds'], ["existing-id"])

    @patch('ansible_collections.venafi.cloud.plugins.modules.certificate_create.VenafiCloudAPI')
    @patch('ansible_collections.venafi.cloud.plugins.modules.certificate_create.AnsibleModule')
    def test_main_create_new(self, mock_ansible_module, mock_api_class):
        # Setup mocks
        mock_ansible_module.return_value = self.mock_module
        mock_api_instance = mock_api_class.return_value
        
        # No existing certificates
        mock_api_instance.search_certificates.return_value = {"certificates": []}
        mock_api_instance.request.return_value = {"id": "new-req-id", "status": "ISSUED"}

        # Run main
        certificate_create.main()

        # Assertions
        self.mock_module.exit_json.assert_called_once()
        args, kwargs = self.mock_module.exit_json.call_args
        self.assertTrue(kwargs['changed'])
        self.assertEqual(kwargs['certificate_request']['id'], "new-req-id")

if __name__ == '__main__':
    unittest.main()
