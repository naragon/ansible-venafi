from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import unittest
from unittest.mock import MagicMock, patch
from ansible_collections.venafi.cloud.plugins.modules import certificate_retire

class TestCertificateRetire(unittest.TestCase):

    def setUp(self):
        self.mock_module = MagicMock()
        self.mock_module.params = {
            'api_key': 'test-api-key',
            'base_url': 'https://api.venafi.cloud',
            'certificate_ids': ['cert-id-1']
        }

    @patch('ansible_collections.venafi.cloud.plugins.modules.certificate_retire.VenafiCloudAPI')
    @patch('ansible_collections.venafi.cloud.plugins.modules.certificate_retire.AnsibleModule')
    def test_main_success(self, mock_ansible_module, mock_api_class):
        # Setup mocks
        mock_ansible_module.return_value = self.mock_module
        mock_api_instance = mock_api_class.return_value
        mock_api_instance.request.return_value = {"certificateIds": ["cert-id-1"]}

        # Run main
        certificate_retire.main()

        # Assertions
        mock_api_instance.request.assert_called_with("POST", "/v1/certificates/retire", data={"certificateIds": ["cert-id-1"]})
        self.mock_module.exit_json.assert_called_once()
        args, kwargs = self.mock_module.exit_json.call_args
        self.assertTrue(kwargs['changed'])
        self.assertEqual(kwargs['retirement_result'], {"certificateIds": ["cert-id-1"]})

if __name__ == '__main__':
    unittest.main()
