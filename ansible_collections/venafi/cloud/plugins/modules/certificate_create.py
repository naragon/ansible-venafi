from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: certificate_create
short_description: Create a certificate in Venafi TLS Protect Cloud using ASK
description:
    - This module allows users to create a TLS certificate using Automated Secure Keypair (ASK).
    - Venafi generates the key pair and certificate.
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
        type: str
        required: true
    organization:
        description:
            - The Organization for the certificate.
        type: str
    organizational_units:
        description:
            - List of Organizational Units.
        type: list
        elements: str
    locality:
        description:
            - The Locality (City) for the certificate.
        type: str
    state:
        description:
            - The State/Province for the certificate.
        type: str
    country:
        description:
            - The Country (2-letter code) for the certificate.
        type: str
    sans:
        description:
            - Subject Alternative Names.
        type: dict
        suboptions:
            dns_names:
                description: List of DNS names.
                type: list
                elements: str
            ip_addresses:
                description: List of IP addresses.
                type: list
                elements: str
    key_type:
        description:
            - The algorithm for the key pair.
        type: str
        default: RSA
        choices: [RSA, ECC]
    key_length:
        description:
            - Key size (for RSA).
        type: int
        default: 2048
    key_curve:
        description:
            - Elliptic curve name (for ECC).
        type: str
        choices: [P256, P384, P521]
    validity_period:
        description:
            - ISO 8601 duration (e.g., P365D).
        type: str
author:
    - Venafi
'''

EXAMPLES = r'''
- name: Create a certificate with ASK
  venafi.cloud.certificate_create:
    api_key: "{{ venafi_api_key }}"
    application_id: "a1b2c3d4-..."
    template_id: "z9y8x7w6-..."
    common_name: "www.example.com"
    organization: "Example Corp"
    country: "US"
    sans:
      dns_names:
        - www.example.com
        - api.example.com
    key_type: RSA
    key_length: 4096
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
        organization=dict(type='str'),
        organizational_units=dict(type='list', elements='str'),
        locality=dict(type='str'),
        state=dict(type='str'),
        country=dict(type='str'),
        sans=dict(type='dict', options=dict(
            dns_names=dict(type='list', elements='str'),
            ip_addresses=dict(type='list', elements='str')
        )),
        key_type=dict(type='str', default='RSA', choices=['RSA', 'ECC']),
        key_length=dict(type='int', default=2048),
        key_curve=dict(type='str', choices=['P256', 'P384', 'P521']),
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
        # Find the latest certificate that is still valid
        valid_certs = []
        for cert in search_result['certificates']:
            # Venafi returns validityEnd in ISO format, e.g. "2023-10-01T00:00:00.000Z"
            end_date_str = cert.get('validityEnd', '').replace('Z', '+00:00')
            if end_date_str:
                try:
                    # handle possible variations in fractional seconds
                    if '.' in end_date_str:
                        end_date = datetime.fromisoformat(end_date_str.split('.')[0] + '+00:00')
                    else:
                        end_date = datetime.fromisoformat(end_date_str)
                    
                    if end_date > now.replace(tzinfo=end_date.tzinfo):
                        valid_certs.append(cert)
                except ValueError:
                    continue
        
        if valid_certs:
            # Sort by end date descending to get the one that lasts the longest
            valid_certs.sort(key=lambda x: x['validityEnd'], reverse=True)
            module.exit_json(changed=False, certificate_request={"id": "existing", "certificateIds": [valid_certs[0]['id']], "status": "ISSUED"})

    csr_attributes = {
        "commonName": module.params['common_name']
    }
    if module.params['organization']:
        csr_attributes['organization'] = module.params['organization']
    if module.params['organizational_units']:
        csr_attributes['organizationalUnits'] = module.params['organizational_units']
    if module.params['locality']:
        csr_attributes['locality'] = module.params['locality']
    if module.params['state']:
        csr_attributes['state'] = module.params['state']
    if module.params['country']:
        csr_attributes['country'] = module.params['country']

    payload = {
        "applicationId": module.params['application_id'],
        "certificateIssuingTemplateId": module.params['template_id'],
        "csrAttributes": csr_attributes,
        "isVaaSGenerated": True,
        "keyType": module.params['key_type'],
        "keyLength": module.params['key_length']
    }
    
    if module.params['sans']:
        sans_payload = {}
        if module.params['sans'].get('dns_names'):
            sans_payload['dnsNames'] = module.params['sans']['dns_names']
        if module.params['sans'].get('ip_addresses'):
            sans_payload['ipAddresses'] = module.params['sans']['ip_addresses']
        if sans_payload:
            payload['subjectAlternativeNamesByType'] = sans_payload

    if module.params['key_type'] == 'ECC' and module.params['key_curve']:
        payload['keyCurve'] = module.params['key_curve']
    
    if module.params['validity_period']:
        payload['validityPeriod'] = module.params['validity_period']

    result = api.request("POST", "/outagedetection/v1/certificaterequests", data=payload)

    module.exit_json(changed=True, certificate_request=result)

if __name__ == '__main__':
    main()
