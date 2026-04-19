from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: certificate_retire
short_description: Retire certificates in Venafi TLS Protect Cloud
description:
    - This module allows users to retire one or more certificates in Venafi TLS Protect Cloud.
    - Retired certificates are moved to a virtual recycle bin and no longer monitored.
options:
    api_key:
        description:
            - Venafi Cloud API Key.
            - Can be set via the VENAFI_API_KEY environment variable.
        type: str
        required: true
    base_url:
        description:
            - The base URL for the Venafi Cloud API.
        type: str
        default: https://api.venafi.cloud
    certificate_ids:
        description:
            - List of certificate IDs to retire.
        type: list
        elements: str
        required: true
author:
    - Venafi
'''

EXAMPLES = r'''
- name: Retire a certificate
  venafi.cloud.certificate_retire:
    api_key: "{{ venafi_api_key }}"
    certificate_ids:
      - "df7a8100-64c3-11eb-bcda-99e9056552b5"
'''

RETURN = r'''
retirement_result:
    description: The response from the Venafi Cloud API.
    returned: always
    type: dict
    sample: {
        "certificateIds": ["df7a8100-64c3-11eb-bcda-99e9056552b5"]
    }
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.venafi.cloud.plugins.module_utils.venafi_cloud import VenafiCloudAPI, venafi_cloud_argument_spec

def main():
    argument_spec = venafi_cloud_argument_spec()
    argument_spec.update(dict(
        certificate_ids=dict(type='list', elements='str', required=True)
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=False
    )

    api = VenafiCloudAPI(module, module.params['api_key'], module.params['base_url'])
    
    payload = {
        "certificateIds": module.params['certificate_ids']
    }

    result = api.request("POST", "/v1/certificates/retire", data=payload)

    module.exit_json(changed=True, retirement_result=result)

if __name__ == '__main__':
    main()
