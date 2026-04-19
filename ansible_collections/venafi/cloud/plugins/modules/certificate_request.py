from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: certificate_request
short_description: Request a certificate from Venafi TLS Protect Cloud using a CSR
description:
    - This module allows users to request a TLS certificate by providing a Certificate Signing Request (CSR).
    - The request is submitted to Venafi TLS Protect Cloud.
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
    application_id:
        description:
            - The ID of the Application in Venafi Cloud.
        type: str
        required: true
    template_id:
        description:
            - The ID of the Certificate Issuing Template.
        type: str
        required: true
    common_name:
        description:
            - The Common Name for the certificate.
            - Used for idempotency check.
        type: str
        required: true
    csr:
        description:
            - The PEM-encoded CSR.
        type: str
        required: true
    validity_period:
        description:
            - ISO 8601 duration (e.g., P365D).
        type: str
author:
    - Venafi
'''

EXAMPLES = r'''
- name: Request a certificate with CSR
  venafi.cloud.certificate_request:
    api_key: "{{ venafi_api_key }}"
    application_id: "a1b2c3d4-..."
    template_id: "z9y8x7w6-..."
    common_name: "www.example.com"
    csr: "{{ lookup('file', 'request.csr') }}"
'''

RETURN = r'''
certificate_request:
    description: The response from the Venafi Cloud API.
    returned: always
    type: dict
    sample: {
        "id": "b30736b0-bce1-11eb-9af9-c947417e28d0",
        "certificateIds": ["c41847c1-cde2-22fc-0bg0-d058528f39e1"],
        "status": "ISSUED"
    }
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.venafi.cloud.plugins.module_utils.venafi_cloud import VenafiCloudAPI, venafi_cloud_argument_spec

def main():
    argument_spec = venafi_cloud_argument_spec()
    argument_spec.update(dict(
        application_id=dict(type='str', required=True),
        template_id=dict(type='str', required=True),
        common_name=dict(type='str', required=True),
        csr=dict(type='str', required=True),
        validity_period=dict(type='str', required=False)
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=False
    )

    api = VenafiCloudAPI(module, module.params['api_key'], module.params['base_url'])
    
    # Idempotency check
    search_result = api.search_certificates(module.params['common_name'], module.params['application_id'])
    if search_result and search_result.get('certificates'):
        from datetime import datetime
        now = datetime.utcnow()
        valid_certs = []
        for cert in search_result['certificates']:
            end_date_str = cert.get('validityEnd', '').replace('Z', '+00:00')
            if end_date_str:
                try:
                    if '.' in end_date_str:
                        end_date = datetime.fromisoformat(end_date_str.split('.')[0] + '+00:00')
                    else:
                        end_date = datetime.fromisoformat(end_date_str)
                    
                    if end_date > now.replace(tzinfo=end_date.tzinfo):
                        valid_certs.append(cert)
                except ValueError:
                    continue
        
        if valid_certs:
            valid_certs.sort(key=lambda x: x['validityEnd'], reverse=True)
            module.exit_json(changed=False, certificate_request={"id": "existing", "certificateIds": [valid_certs[0]['id']], "status": "ISSUED"})

    payload = {
        "applicationId": module.params['application_id'],
        "certificateIssuingTemplateId": module.params['template_id'],
        "csr": module.params['csr'],
        "isVaaSGenerated": False
    }
    
    if module.params['validity_period']:
        payload['validityPeriod'] = module.params['validity_period']

    result = api.request("POST", "/outagedetection/v1/certificaterequests", data=payload)

    module.exit_json(changed=True, certificate_request=result)

if __name__ == '__main__':
    main()
