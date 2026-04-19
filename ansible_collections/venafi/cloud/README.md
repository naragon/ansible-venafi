# Venafi TLS Protect Cloud Ansible Collection

This collection provides a set of Ansible modules to automate the lifecycle management of TLS certificates using the **Venafi TLS Protect Cloud** (formerly Venafi as a Service) API.

## Features

- **Request Certificates**: Submit a Certificate Signing Request (CSR) for signing.
- **Create Certificates (ASK)**: Use Automated Secure Keypair (ASK) to have Venafi generate the key pair and certificate.
- **Renew Certificates**: Easily renew existing certificates using either CSR or ASK workflows.
- **Retire Certificates**: Move certificates to the virtual recycle bin to stop monitoring and billing.
- **Download Certificates**: Fetch public certificates and their chains for installation on servers and devices.
- **Idempotency**: Enrollment modules check for existing valid certificates before submitting new requests.

## Requirements

- **Ansible**: version 2.13 or higher.
- **Python**: version 3.6 or higher.
- **Venafi TLS Protect Cloud Account**: An active API key and at least one Application and Issuing Template (CIT).

## Installation

### From Source
To install the collection locally from this repository:

```bash
# Build the collection
ansible-galaxy collection build ansible_collections/venafi/cloud/

# Install the collection
ansible-galaxy collection install venafi-cloud-1.4.0.tar.gz
```

## Configuration

All modules support the following common parameters:

- `api_key`: Your Venafi Cloud API Key. Can also be set via the `VENAFI_API_KEY` environment variable.
- `base_url`: The API endpoint. Defaults to `https://api.venafi.cloud`. Use `https://api.eu.venafi.cloud` for the EU region.

## Usage Examples

### 1. Request a Certificate (CSR-based)
```yaml
- name: Request a certificate using a local CSR
  venafi.cloud.certificate_request:
    api_key: "{{ my_api_key }}"
    application_id: "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    template_id: "z9y8x7w6-v5u4-3210-fedc-ba0987654321"
    common_name: "www.example.com"
    csr: "{{ lookup('file', 'request.csr') }}"
```

### 2. Create a Certificate (ASK-based)
```yaml
- name: Create a certificate using Venafi-generated keys
  venafi.cloud.certificate_create:
    api_key: "{{ my_api_key }}"
    application_id: "..."
    template_id: "..."
    common_name: "api.example.com"
    organization: "My Corp"
    country: "US"
    key_type: RSA
    key_length: 4096
```

### 3. Renew a Certificate
```yaml
- name: Renew an expiring certificate
  venafi.cloud.certificate_renew:
    api_key: "{{ my_api_key }}"
    existing_certificate_id: "uuid-of-old-cert"
    application_id: "..."
    template_id: "..."
    common_name: "www.example.com"
```

### 4. Download a Certificate
```yaml
- name: Download certificate for Nginx
  venafi.cloud.certificate_download:
    api_key: "{{ my_api_key }}"
    certificate_id: "..."
    dest: "/etc/nginx/certs/mysite.pem"
    chain_order: EE_FIRST
```

## Idempotency

The `certificate_request` and `certificate_create` modules are idempotent. They search for an existing certificate with the same **Common Name** and **Application ID**. If a matching certificate is found and it is still valid (not expired), the module will return `changed: false` and the existing certificate details.

---

## Developer Guide

### Directory Structure
- `plugins/modules/`: Python module implementations.
- `plugins/module_utils/`: Shared API wrapper and utilities.
- `tests/unit/`: Unit tests using Python's `unittest` framework.

### Running Unit Tests
Tests are designed to run with `ansible-test unit`, but can also be executed manually:

```bash
# Set PYTHONPATH to include the collection root
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Run a specific test
python3 ansible_collections/venafi/cloud/tests/unit/plugins/modules/test_certificate_create.py
```

### Contributing
When adding new modules:
1.  Inherit from `VenafiCloudAPI` in `module_utils` for API requests.
2.  Include full `DOCUMENTATION`, `EXAMPLES`, and `RETURN` blocks.
3.  Implement idempotency where appropriate.
4.  Add unit tests in the `tests/unit/` directory.

## License
Apache-2.0
