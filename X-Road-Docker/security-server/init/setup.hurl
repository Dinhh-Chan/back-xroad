# Initialize Security Server

# Check that the Security Server UI is up and running
GET https://{{ss_host}}:{{ss_port}}
HTTP 200

# Create management Security Server API-Key
POST https://{{ss_host}}:{{ss_port}}/api/v1/api-keys
[BasicAuth]
{{ss_admin_user}}: {{ss_admin_user_password}}
[
    "XROAD_SECURITY_OFFICER",
    "XROAD_REGISTRATION_OFFICER",
    "XROAD_SERVICE_ADMINISTRATOR",
    "XROAD_SYSTEM_ADMINISTRATOR",
    "XROAD_SECURITYSERVER_OBSERVER"
]

HTTP 200

[Captures]
ss_api_key: jsonpath "$['key']"

# Add configuration anchor
POST https://{{ss_host}}:{{ss_port}}/api/v1/system/anchor
Authorization: X-Road-ApiKey token={{ss_api_key}}
Content-Type: application/octet-stream
file,anchors/internal-anchor.xml;

HTTP 201

# Initialize management Security Server
POST https://{{ss_host}}:{{ss_port}}/api/v1/initialization
Authorization: X-Road-ApiKey token={{ss_api_key}}
Content-Type: application/json
{
    "owner_member_class": "{{ss_member_class}}",
    "owner_member_code": "{{ss_member_code}}",
    "security_server_code": "{{ss_security_server_code}}",
    "software_token_pin": "{{ss_token_pin}}",
    "ignore_warnings": true
}

HTTP 201

# Log in to the Security Servers token
PUT https://{{ss_host}}:{{ss_port}}/api/v1/tokens/0/login
Authorization: X-Road-ApiKey token={{ss_api_key}}
Content-Type: application/json
{
    "password": "{{ss_token_pin}}"
}

HTTP *

# Get the CA name
GET https://{{ss_host}}:{{ss_port}}/api/v1/certificate-authorities
Authorization: X-Road-ApiKey token={{ss_api_key}}

HTTP 200

[Captures]
ca_name: jsonpath "$[0].name"

# Add auth key to the Security Server token
POST https://{{ss_host}}:{{ss_port}}/api/v1/tokens/0/keys-with-csrs
Authorization: X-Road-ApiKey token={{ss_api_key}}
Content-Type: application/json
{
    "key_label": "Auth key",
    "csr_generate_request": {
        "key_usage_type": "AUTHENTICATION",
        "ca_name": "{{ca_name}}",
        "csr_format": "DER",
        "subject_field_values": {
            "CN": "{{ss_member_code}}",
            "C": "FI",
            "O": "{{ss_member_name}}",
            "serialNumber": "{{cs_instance_identifier}}/{{ss_security_server_code}}/{{ss_member_class}}",
            "subjectAltName": "{{ss_member_name}}"
        },
        "acme_order": false
    }
}
# TODO: This should return 201 according to the definition:
# https://github.com/nordic-institute/X-Road/blob/e14d198f704b34b4d1789c2972e816152b6a35f8/src/security-server/openapi-model/src/main/resources/META-INF/openapi-definition.yaml#L4846
HTTP 200

[Captures]
ss_auth_key_id: jsonpath "$.key.id"
ss_auth_key_csr_id: jsonpath "$.csr_id"

# Get the auth key CSR
GET https://{{ss_host}}:{{ss_port}}/api/v1/keys/{{ss_auth_key_id}}/csrs/{{ss_auth_key_csr_id}}?csr_format=PEM
Authorization: X-Road-ApiKey token={{ss_api_key}}

HTTP 200

[Captures]
ss_auth_key_csr: body

# Sign the auth key CSR (note that the CA needs filename so we can't just send it under
# [FormMultiPart] as we do with the other requests)
POST http://{{ca_host}}:8888/ca/sign
Content-Type: multipart/form-data; boundary=certboundary
```
--certboundary
Content-Disposition: form-data; name="type"

auth
--certboundary
Content-Disposition: form-data; name="certreq"; filename="auth.csr.pem"

{{ss_auth_key_csr}}
--certboundary--
```

HTTP 200
[Captures]
ss_auth_key_cert: body

# Import auth certificate
POST https://{{ss_host}}:{{ss_port}}/api/v1/token-certificates
Authorization: X-Road-ApiKey token={{ss_api_key}}
Content-Type: application/octet-stream
```
{{ss_auth_key_cert}}
```

HTTP 201

[Captures]
ss_auth_key_cert_hash: jsonpath "$.certificate_details.hash"

# Add sign key to the Security Server token
POST https://{{ss_host}}:{{ss_port}}/api/v1/tokens/0/keys-with-csrs
Authorization: X-Road-ApiKey token={{ss_api_key}}
{
    "key_label": "Sign key",
    "csr_generate_request": {
        "key_usage_type": "SIGNING",
        "ca_name": "{{ca_name}}",
        "csr_format": "DER",
        "member_id": "{{cs_instance_identifier}}:{{ss_member_class}}:{{ss_member_code}}",
        "subject_field_values": {
            "CN": "{{ss_member_code}}",
            "C": "FI",
            "O": "{{ss_member_name}}",
            "subjectAltName": "{{ss_member_name}}",
            "serialNumber": "{{cs_instance_identifier}}/{{ss_security_server_code}}/{{ss_member_class}}"
        },
        "acme_order": false
    }
}

# TODO: This should return 201 according to the definition (same as for auth key above)
HTTP 200

[Captures]
ss_sign_key_id: jsonpath "$.key.id"
ss_sign_key_csr_id: jsonpath "$.csr_id"

# Get the sign key CSR
GET https://{{ss_host}}:{{ss_port}}/api/v1/keys/{{ss_sign_key_id}}/csrs/{{ss_sign_key_csr_id}}?csr_format=PEM
Authorization: X-Road-ApiKey token={{ss_api_key}}

HTTP 200

[Captures]
ss_sign_key_csr: body

# Sign the sign key CSR (note that the CA needs filename so we can't just send it under
# [FormMultiPart] as we do with the other requests)
POST http://{{ca_host}}:8888/ca/sign
Content-Type: multipart/form-data; boundary=certboundary
```
--certboundary
Content-Disposition: form-data; name="type"

sign
--certboundary
Content-Disposition: form-data; name="certreq"; filename="sign.csr.pem"

{{ss_sign_key_csr}}
--certboundary--
```

HTTP 200
[Captures]
ss_sign_key_cert: body

# Import sign certificate
POST https://{{ss_host}}:{{ss_port}}/api/v1/token-certificates
Authorization: X-Road-ApiKey token={{ss_api_key}}
Content-Type: application/octet-stream
```
{{ss_sign_key_cert}}
```

HTTP 201

[Captures]
ss_sign_key_cert_hash: jsonpath "$.certificate_details.hash"


# Register auth certificate
PUT https://{{ss_host}}:{{ss_port}}/api/v1/token-certificates/{{ss_auth_key_cert_hash}}/register
Authorization: X-Road-ApiKey token={{ss_api_key}}
{
    "address": "{{ss_host}}"
}

# TODO: This should be 200 according to the OpenAPI description but is 204:
# https://github.com/nordic-institute/X-Road/blob/e14d198f704b34b4d1789c2972e816152b6a35f8/src/security-server/openapi-model/src/main/resources/META-INF/openapi-definition.yaml#L640
HTTP 204

# Add MANAGEMENT to management Security Server
POST https://{{ss_host}}:{{ss_port}}/api/v1/clients
Authorization: X-Road-ApiKey token={{ss_api_key}}
{
    "ignore_warnings": true,
    "client": {
        "member_class": "{{ss_member_class}}",
        "member_code": "{{ss_member_code}}",
        "subsystem_code": "MANAGEMENT",
        "connection_type": "HTTP"
    }
}

HTTP 201

[Captures]
ss_management_client_id: jsonpath "$.id"

# Activate auth certificate on Security Server
PUT https://{{ss_host}}:{{ss_port}}/api/v1/token-certificates/{{ss_auth_key_cert_hash}}/activate
Authorization: X-Road-ApiKey token={{ss_api_key}}

HTTP 204

# Set timestamping service on Security Server
GET https://{{ss_host}}:{{ss_port}}/api/v1/timestamping-services
Authorization: X-Road-ApiKey token={{ss_api_key}}


HTTP 200

[Captures]
tsa_name: jsonpath "$[0].name"
tsa_url: jsonpath "$[0].url"

POST https://{{ss_host}}:{{ss_port}}/api/v1/system/timestamping-services
Authorization: X-Road-ApiKey token={{ss_api_key}}
{
    "name": "{{tsa_name}}",
    "url": "{{tsa_url}}"
}

HTTP 201
