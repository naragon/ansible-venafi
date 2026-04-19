from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
from ansible.module_utils.urls import fetch_url
from ansible.module_utils.basic import AnsibleModule

class VenafiCloudAPI:
    def __init__(self, module, api_key, base_url="https://api.venafi.cloud"):
        self.module = module
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')

    def request(self, method, path, data=None):
        url = f"{self.base_url}{path}"
        headers = {
            "tppl-api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        payload = None
        if data:
            payload = json.dumps(data)

        response, info = fetch_url(self.module, url, method=method, headers=headers, data=payload)
        
        if info['status'] >= 400:
            error_msg = info.get('msg', 'Unknown error')
            try:
                error_body = json.loads(response.read())
                error_msg = error_body.get('message', error_msg)
            except Exception:
                pass
            self.module.fail_json(msg=f"API request failed: {info['status']} - {error_msg}", status=info['status'], url=url)

        if response:
            content = response.read()
            if content:
                try:
                    return json.loads(content)
                except ValueError:
                    return content
        return None

    def search_certificates(self, cn, application_id=None):
        payload = {
            "expression": {
                "operator": "AND",
                "operands": [
                    {
                        "field": "subjectCN",
                        "operator": "EQ",
                        "value": cn
                    }
                ]
            }
        }
        
        if application_id:
            payload['expression']['operands'].append({
                "field": "applicationId",
                "operator": "EQ",
                "value": application_id
            })

        return self.request("POST", "/outagedetection/v1/certificatesearch", data=payload)

def venafi_cloud_argument_spec():
    return dict(
        api_key=dict(type='str', required=True, no_log=True, fallback=(AnsibleModule.env_fallback, ['VENAFI_API_KEY'])),
        base_url=dict(type='str', default='https://api.venafi.cloud')
    )
