from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: certificate_download
short_description: Download a certificate from Venafi TLS Protect Cloud
description:
    - This module allows users to download a TLS certificate from Venafi TLS Protect Cloud.
    - It can return the certificate content or save it to a file.
    - To download a private key (ASK requests), use M(venafi.cloud.certificate_export).
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
    certificate_id:
        description:
            - The ID of the certificate to download.
        type: str
        required: true
    dest:
        description:
            - Path where the certificate should be saved.
        type: path
    format:
        description:
            - The download format.
        type: str
        default: PEM
        choices: [PEM, DER]
    chain_order:
        description:
            - The order of the certificate chain.
        type: str
        default: ROOT_FIRST
        choices: [ROOT_FIRST, EE_FIRST, EE_ONLY]
    include_chain:
        description:
            - Whether to include the full chain.
        type: bool
        default: true
author:
    - Venafi
'''

EXAMPLES = r'''
- name: Download certificate to a file
  venafi.cloud.certificate_download:
    api_key: "{{ venafi_api_key }}"
    certificate_id: "df7a8100-..."
    dest: "/tmp/cert.pem"
    format: PEM

- name: Get certificate content into a variable
  venafi.cloud.certificate_download:
    api_key: "{{ venafi_api_key }}"
    certificate_id: "df7a8100-..."
  register: cert_data
'''

RETURN = r'''
certificate:
    description: The PEM-encoded certificate content (if format is PEM).
    returned: success
    type: str
dest:
    description: The path to the saved file.
    returned: if dest is provided
    type: str
'''

import os
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.venafi.cloud.plugins.module_utils.venafi_cloud import VenafiCloudAPI, venafi_cloud_argument_spec

def main():
    argument_spec = venafi_cloud_argument_spec()
    argument_spec.update(dict(
        certificate_id=dict(type='str', required=True),
        dest=dict(type='path'),
        format=dict(type='str', default='PEM', choices=['PEM', 'DER']),
        chain_order=dict(type='str', default='ROOT_FIRST', choices=['ROOT_FIRST', 'EE_FIRST', 'EE_ONLY']),
        include_chain=dict(type='bool', default=True)
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    api = VenafiCloudAPI(module, module.params['api_key'], module.params['base_url'])
    
    path = f"/outagedetection/v1/certificates/{module.params['certificate_id']}/contents"
    params = []
    params.append(f"format={module.params['format']}")
    params.append(f"chainOrder={module.params['chain_order']}")
    params.append(f"includeChain={'true' if module.params['include_chain'] else 'false'}")
    
    full_path = f"{path}?{'&'.join(params)}"
    
    content = api.request("GET", full_path)

    changed = False
    if module.params['dest']:
        dest = module.params['dest']
        # Check if file exists and has same content
        if os.path.exists(dest):
            with open(dest, 'rb') as f:
                old_content = f.read()
            if old_content != (content if isinstance(content, bytes) else content.encode('utf-8')):
                changed = True
        else:
            changed = True
        
        if changed and not module.check_mode:
            mode = 'wb' if isinstance(content, bytes) else 'w'
            with open(dest, mode) as f:
                f.write(content)

    module.exit_json(changed=changed, certificate=content if isinstance(content, str) else None, dest=module.params['dest'])

if __name__ == '__main__':
    main()
