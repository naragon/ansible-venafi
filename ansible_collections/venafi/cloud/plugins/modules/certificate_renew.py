from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: certificate_renew
short_description: Renew a certificate in Venafi TLS Protect Cloud
description:
    - This module allows users to renew a TLS certificate in Venafi TLS Protect Cloud.
    - You can renew using either a new CSR or Automated Secure Keypair (ASK).
    - The renewal links the new certificate to an existing certificate record.
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
    existing_certificate_id:
        description:
            - The ID of the existing certificate to be renewed.
        type: str
        required: true
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
    csr:
        description:
            - The PEM-encoded CSR for CSR-based renewal.
            - If omitted, ASK (Automated Secure Keypair) will be used.
        type: str
    common_name:
        description:
            - The Common Name for the certificate (required for ASK renewal if not providing CSR).
        type: str
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
            - Subject Alternative Names (for ASK renewal).
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
            - The algorithm for the key pair (for ASK renewal).
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
- name: Renew a certificate using a new CSR
  venafi.cloud.certificate_renew:
    api_key: "{{ venafi_api_key }}"
    existing_certificate_id: "4f2a1b3c-..."
    application_id: "a1b2c3d4-..."
    template_id: "z9y8x7w6-..."
    csr: "{{ lookup('file', 'renewal.csr') }}"

- name: Renew a certificate using ASK
  venafi.cloud.certificate_renew:
    api_key: "{{ venafi_api_key }}"
    existing_certificate_id: "4f2a1b3c-..."
    application_id: "a1b2c3d4-..."
    template_id: "z9y8x7w6-..."
    common_name: "www.example.com"
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
        existing_certificate_id=dict(type='str', required=True),
        application_id=dict(type='str', required=True),
        template_id=dict(type='str', required=True),
        csr=dict(type='str'),
        common_name=dict(type='str'),
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
        required_if=[
            ('csr', None, ['common_name'])
        ],
        supports_check_mode=False
    )

    api = VenafiCloudAPI(module, module.params['api_key'], module.params['base_url'])
    
    payload = {
        "existingCertificateId": module.params['existing_certificate_id'],
        "applicationId": module.params['application_id'],
        "certificateIssuingTemplateId": module.params['template_id']
    }

    if module.params['csr']:
        payload['csr'] = module.params['csr']
        payload['isVaaSGenerated'] = False
    else:
        # ASK Renewal
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

        payload['csrAttributes'] = csr_attributes
        payload['isVaaSGenerated'] = True
        payload['keyType'] = module.params['key_type']
        payload['keyLength'] = module.params['key_length']
        
        if module.params['key_type'] == 'ECC' and module.params['key_curve']:
            payload['keyCurve'] = module.params['key_curve']

        if module.params['sans']:
            sans_payload = {}
            if module.params['sans'].get('dns_names'):
                sans_payload['dnsNames'] = module.params['sans']['dns_names']
            if module.params['sans'].get('ip_addresses'):
                sans_payload['ipAddresses'] = module.params['sans']['ip_addresses']
            if sans_payload:
                payload['subjectAlternativeNamesByType'] = sans_payload

    if module.params['validity_period']:
        payload['validityPeriod'] = module.params['validity_period']

    result = api.request("POST", "/outagedetection/v1/certificaterequests", data=payload)

    module.exit_json(changed=True, certificate_request=result)

if __name__ == '__main__':
    main()
