# Check that the Central Server UI is up and running
GET https://{{cs_host}}:{{cs_port}}

HTTP 200

# Create Central Server API-Key
POST https://{{cs_host}}:{{cs_port}}/api/v1/api-keys
[BasicAuth]
{{cs_admin_user}}: {{cs_admin_user_password}}
[
    "XROAD_REGISTRATION_OFFICER",
    "XROAD_SECURITY_OFFICER",
    "XROAD_SYSTEM_ADMINISTRATOR",
    "XROAD_MANAGEMENT_SERVICE"
]

HTTP 200

[Captures]
cs_api_key: jsonpath "$['key']"

# Initialize Central Server
POST https://{{cs_host}}:{{cs_port}}/api/v1/initialization
Authorization: X-Road-ApiKey token={{cs_api_key}}
Content-Type: application/json
{
    "software_token_pin": "{{cs_token_pin}}",
    "instance_identifier": "{{cs_instance_identifier}}",
    "central_server_address": "{{cs_host}}"
}

# TODO: The Central Server currently returns the incorrect HTTP code, the documentation notes that it should be "201":
# https://github.com/nordic-institute/X-Road/blob/6ef2d9e83287ccb281b0cc27ba663a5ae8c4aa16/src/central-server/openapi-model/src/main/resources/openapi-definition.yaml#L1344
HTTP 200


# Add member classes to Central Server
POST https://{{cs_host}}:{{cs_port}}/api/v1/member-classes
Authorization: X-Road-ApiKey token={{cs_api_key}}
Content-Type: application/json
{
    "code": "GOV",
    "description": "Governmental organizations"
}

POST https://{{cs_host}}:{{cs_port}}/api/v1/member-classes
Authorization: X-Road-ApiKey token={{cs_api_key}}
Content-Type: application/json
{
    "code": "EDU",
    "description": "Educational organizations"
}

POST https://{{cs_host}}:{{cs_port}}/api/v1/member-classes
Authorization: X-Road-ApiKey token={{cs_api_key}}
Content-Type: application/json
{
    "code": "ORG",
    "description": "Non-profit organizations"
}

POST https://{{cs_host}}:{{cs_port}}/api/v1/member-classes
Authorization: X-Road-ApiKey token={{cs_api_key}}
Content-Type: application/json
{
    "code": "COM",
    "description": "Commercial organizations"
}

HTTP 201

# Log in Central Server token
PUT https://{{cs_host}}:{{cs_port}}/api/v1/tokens/0/login
Authorization: X-Road-ApiKey token={{cs_api_key}}
Content-Type: application/json
{
    "password": "{{cs_token_pin}}"
}

HTTP *

# Add internal signing key to Central Server
POST https://{{cs_host}}:{{cs_port}}/api/v1/configuration-sources/INTERNAL/signing-keys
Authorization: X-Road-ApiKey token={{cs_api_key}}
Content-Type: application/json
{
    "key_label": "Internal signing key",
    "token_id": 0
}

# TODO: The Central Server currently returns the incorrect HTTP code, the documentation notes that it should be "201":
# https://github.com/nordic-institute/X-Road/blob/6ef2d9e83287ccb281b0cc27ba663a5ae8c4aa16/src/central-server/openapi-model/src/main/resources/openapi-definition.yaml#L1051
HTTP 200

# Add external signing key to Central Server
POST https://{{cs_host}}:{{cs_port}}/api/v1/configuration-sources/EXTERNAL/signing-keys
Authorization: X-Road-ApiKey token={{cs_api_key}}
Content-Type: application/json
{
    "key_label": "External signing key",
    "token_id": 0
}

# TODO: The Central Server currently returns the incorrect HTTP code, the documentation notes that it should be "201":
# https://github.com/nordic-institute/X-Road/blob/6ef2d9e83287ccb281b0cc27ba663a5ae8c4aa16/src/central-server/openapi-model/src/main/resources/openapi-definition.yaml#L1051
HTTP 200

# Add member to Central Server
POST https://{{cs_host}}:{{cs_port}}/api/v1/members
Authorization: X-Road-ApiKey token={{cs_api_key}}
Content-Type: application/json
{
    "member_id": {
        "member_class": "{{ssm_member_class}}",
        "member_code": "{{ssm_member_code}}"
    },
    "member_name": "{{ssm_member_name}}"
}

HTTP 201

# Add management subsystem for member to Central Server
POST https://{{cs_host}}:{{cs_port}}/api/v1/subsystems
Authorization: X-Road-ApiKey token={{cs_api_key}}
Content-Type: application/json
{
    "subsystem_id": {
        "member_class": "{{ssm_member_class}}",
        "member_code": "{{ssm_member_code}}",
        "subsystem_code": "MANAGEMENT"
    }
}

HTTP 201


# Set management subsystem for member as the management service for the Central Server
PATCH https://{{cs_host}}:{{cs_port}}/api/v1/management-services-configuration
Authorization: X-Road-ApiKey token={{cs_api_key}}
Content-Type: application/json
{
    "service_provider_id": "{{cs_instance_identifier}}:{{ssm_member_class}}:{{ssm_member_code}}:MANAGEMENT"
}

HTTP 200

# Download CA certificate from Central Server
GET http://{{ca_host}}:8888/ca/certs/ca.cert.pem
[Options]
output: /hurl-files/ca.pem

HTTP 200

# Add CA to Central Server configuration
POST https://{{cs_host}}:{{cs_port}}/api/v1/certification-services
Authorization: X-Road-ApiKey token={{cs_api_key}}
[MultipartFormData]
certificate_profile_info: ee.ria.xroad.common.certificateprofile.impl.FiVRKCertificateProfileInfoProvider
tls_auth: false
acme_server_directory_url: http://{{ca_host}}:8887
certificate: file,ca.pem;

HTTP 201

[Captures]
ca_id: jsonpath "$.id"

# Download OCSP certificate from Central Server
GET http://{{ca_host}}:8888/ca/certs/ocsp.cert.pem
[Options]
output: /hurl-files/ocsp.pem

HTTP 200

# Add OCSP to CA in the Central Server configuration
POST https://{{cs_host}}:{{cs_port}}/api/v1/certification-services/{{ca_id}}/ocsp-responders
Authorization: X-Road-ApiKey token={{cs_api_key}}
[MultipartFormData]
url: http://{{ca_host}}:8888
certificate: file,ocsp.pem;

HTTP 201

# Download TSA certificate from Central Server
GET http://{{ca_host}}:8888/ca/certs/tsa.cert.pem
[Options]
output: /hurl-files/tsa.pem

HTTP 200

# Add TSA to the Central Server
POST https://{{cs_host}}:{{cs_port}}/api/v1/timestamping-services
Authorization: X-Road-ApiKey token={{cs_api_key}}
[MultipartFormData]
url: http://{{ca_host}}:8899
certificate: file,tsa.pem;


# Download global configuration anchor from Central Server
GET https://{{cs_host}}:{{cs_port}}/api/v1/configuration-sources/INTERNAL/anchor/download
Authorization: X-Road-ApiKey token={{cs_api_key}}

HTTP 200

[Captures]
g_conf_anchor: body

# Initialize management Security Server

# Check that the Security Server UI is up and running
GET https://{{ssm_host}}:{{ssm_port}}
HTTP 200

# Create management Security Server API-Key
POST https://{{ssm_host}}:{{ssm_port}}/api/v1/api-keys
[BasicAuth]
{{ssm_admin_user}}: {{ssm_admin_user_password}}
[
    "XROAD_SECURITY_OFFICER",
    "XROAD_REGISTRATION_OFFICER",
    "XROAD_SERVICE_ADMINISTRATOR",
    "XROAD_SYSTEM_ADMINISTRATOR",
    "XROAD_SECURITYSERVER_OBSERVER"
]

HTTP 200

[Captures]
ssm_api_key: jsonpath "$['key']"

# Add configuration anchor
POST https://{{ssm_host}}:{{ssm_port}}/api/v1/system/anchor
Authorization: X-Road-ApiKey token={{ssm_api_key}}
Content-Type: application/octet-stream
```
{{g_conf_anchor}}
```

HTTP 201

# Initialize management Security Server
POST https://{{ssm_host}}:{{ssm_port}}/api/v1/initialization
Authorization: X-Road-ApiKey token={{ssm_api_key}}
Content-Type: application/json
{
    "owner_member_class": "{{ssm_member_class}}",
    "owner_member_code": "{{ssm_member_code}}",
    "security_server_code": "{{ssm_security_server_code}}",
    "software_token_pin": "{{ssm_token_pin}}",
    "ignore_warnings": true
}

HTTP 201

# Log in to the Security Servers token
PUT https://{{ssm_host}}:{{ssm_port}}/api/v1/tokens/0/login
Authorization: X-Road-ApiKey token={{ssm_api_key}}
Content-Type: application/json
{
    "password": "{{ssm_token_pin}}"
}

HTTP *

# Get the CA name
GET https://{{ssm_host}}:{{ssm_port}}/api/v1/certificate-authorities
Authorization: X-Road-ApiKey token={{ssm_api_key}}

HTTP 200

[Captures]
ca_name: jsonpath "$[0].name"

# Add auth key to the Security Server token
POST https://{{ssm_host}}:{{ssm_port}}/api/v1/tokens/0/keys-with-csrs
Authorization: X-Road-ApiKey token={{ssm_api_key}}
Content-Type: application/json
{
    "key_label": "Auth key",
    "csr_generate_request": {
        "key_usage_type": "AUTHENTICATION",
        "ca_name": "{{ca_name}}",
        "csr_format": "DER",
        "subject_field_values": {
            "CN": "{{ssm_member_code}}",
            "C": "FI",
            "O": "{{ssm_member_name}}",
            "serialNumber": "{{cs_instance_identifier}}/{{ssm_security_server_code}}/{{ssm_member_class}}",
            "subjectAltName": "{{ssm_member_name}}"
        },
        "acme_order": false
    }
}
# TODO: This should return 201 according to the definition:
# https://github.com/nordic-institute/X-Road/blob/e14d198f704b34b4d1789c2972e816152b6a35f8/src/security-server/openapi-model/src/main/resources/META-INF/openapi-definition.yaml#L4846
HTTP 200

[Captures]
ssm_auth_key_id: jsonpath "$.key.id"
ssm_auth_key_csr_id: jsonpath "$.csr_id"

# Get the auth key CSR
GET https://{{ssm_host}}:{{ssm_port}}/api/v1/keys/{{ssm_auth_key_id}}/csrs/{{ssm_auth_key_csr_id}}?csr_format=PEM
Authorization: X-Road-ApiKey token={{ssm_api_key}}

HTTP 200

[Captures]
ssm_auth_key_csr: body

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

{{ssm_auth_key_csr}}
--certboundary--
```

HTTP 200
[Captures]
ssm_auth_key_cert: body

# Import auth certificate
POST https://{{ssm_host}}:{{ssm_port}}/api/v1/token-certificates
Authorization: X-Road-ApiKey token={{ssm_api_key}}
Content-Type: application/octet-stream
```
{{ssm_auth_key_cert}}
```

HTTP 201

[Captures]
ssm_auth_key_cert_hash: jsonpath "$.certificate_details.hash"

# Add sign key to the Security Server token
POST https://{{ssm_host}}:{{ssm_port}}/api/v1/tokens/0/keys-with-csrs
Authorization: X-Road-ApiKey token={{ssm_api_key}}
Content-Type: application/json
{
    "key_label": "Sign key",
    "csr_generate_request": {
        "key_usage_type": "SIGNING",
        "ca_name": "{{ca_name}}",
        "csr_format": "DER",
        "member_id": "{{cs_instance_identifier}}:{{ssm_member_class}}:{{ssm_member_code}}",
        "subject_field_values": {
            "CN": "{{ssm_member_code}}",
            "C": "FI",
            "O": "{{ssm_member_name}}",
            "subjectAltName": "{{ssm_member_name}}",
            "serialNumber": "{{cs_instance_identifier}}/{{ssm_security_server_code}}/{{ssm_member_class}}"
        },
        "acme_order": false
    }
}

# TODO: This should return 201 according to the definition (same as for auth key above)
HTTP 200

[Captures]
ssm_sign_key_id: jsonpath "$.key.id"
ssm_sign_key_csr_id: jsonpath "$.csr_id"

# Get the sign key CSR
GET https://{{ssm_host}}:{{ssm_port}}/api/v1/keys/{{ssm_sign_key_id}}/csrs/{{ssm_sign_key_csr_id}}?csr_format=PEM
Authorization: X-Road-ApiKey token={{ssm_api_key}}

HTTP 200

[Captures]
ssm_sign_key_csr: body

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

{{ssm_sign_key_csr}}
--certboundary--
```

HTTP 200
[Captures]
ssm_sign_key_cert: body

# Import sign certificate
POST https://{{ssm_host}}:{{ssm_port}}/api/v1/token-certificates
Authorization: X-Road-ApiKey token={{ssm_api_key}}
Content-Type: application/octet-stream
```
{{ssm_sign_key_cert}}
```

HTTP 201

[Captures]
ssm_sign_key_cert_hash: jsonpath "$.certificate_details.hash"


# Register auth certificate
PUT https://{{ssm_host}}:{{ssm_port}}/api/v1/token-certificates/{{ssm_auth_key_cert_hash}}/register
Authorization: X-Road-ApiKey token={{ssm_api_key}}
{
    "address": "{{ssm_host}}"
}

# TODO: This should be 200 according to the OpenAPI description but is 204:
# https://github.com/nordic-institute/X-Road/blob/e14d198f704b34b4d1789c2972e816152b6a35f8/src/security-server/openapi-model/src/main/resources/META-INF/openapi-definition.yaml#L640
HTTP 204

# Accept Security Server auth certificate registration
GET https://{{cs_host}}:{{cs_port}}/api/v1/management-requests?sort=id&desc=true&status=WAITING
Authorization: X-Road-ApiKey token={{cs_api_key}}

HTTP 200

[Captures]
ssm_auth_cert_reg_req_id: jsonpath "$.items[0].id"

POST https://{{cs_host}}:{{cs_port}}/api/v1/management-requests/{{ssm_auth_cert_reg_req_id}}/approval
Authorization: X-Road-ApiKey token={{cs_api_key}}

HTTP 200

# Register management subsystem to Security Server
POST https://{{cs_host}}:{{cs_port}}/api/v1/management-services-configuration/register-provider
Authorization: X-Road-ApiKey token={{cs_api_key}}
{
    "security_server_id": "{{cs_instance_identifier}}:{{ssm_member_class}}:{{ssm_member_code}}:{{ssm_security_server_code}}"
}

HTTP 200

# Add MANAGEMENT to management Security Server
POST https://{{ssm_host}}:{{ssm_port}}/api/v1/clients
Authorization: X-Road-ApiKey token={{ssm_api_key}}
{
    "ignore_warnings": true,
    "client": {
        "member_class": "{{ssm_member_class}}",
        "member_code": "{{ssm_member_code}}",
        "subsystem_code": "MANAGEMENT",
        "connection_type": "HTTP"
    }
}

HTTP 201

[Captures]
ssm_management_client_id: jsonpath "$.id"

# Get Central Server management services settings
GET https://{{cs_host}}:{{cs_port}}/api/v1/management-services-configuration
Authorization: X-Road-ApiKey token={{cs_api_key}}

HTTP 200

[Captures]
cs_management_service_address: jsonpath "$.services_address"
cs_management_service_wsdl: jsonpath "$.wsdl_address"

# Add Central Server management service to Security Server
POST https://{{ssm_host}}:{{ssm_port}}/api/v1/clients/{{ssm_management_client_id}}/service-descriptions
Authorization: X-Road-ApiKey token={{ssm_api_key}}
{
    "url": "{{cs_management_service_wsdl}}",
    "type": "WSDL",
    "ignore_warnings": true
}

HTTP 201

[Captures]
ssm_management_service_id: jsonpath "$.id"
ssm_auth_cert_deletion_service_id: jsonpath "$.services[0].id"

# Add security server owners group access to management services
PATCH https://{{ssm_host}}:{{ssm_port}}/api/v1/services/{{ssm_auth_cert_deletion_service_id}}
Authorization: X-Road-ApiKey token={{ssm_api_key}}
{
    "ignore_warnings": true,
    "ssl_auth": false,
    "ssl_auth_all": true,
    "timeout": 60,
    "timeout_all": true,
    "url": "{{cs_management_service_address}}",
    "url_all": true
}

# Add security server owners group access to management services
POST https://{{ssm_host}}:{{ssm_port}}/api/v1/clients/{{ssm_management_client_id}}/service-clients/{{cs_instance_identifier}}:security-server-owners/access-rights
Authorization: X-Road-ApiKey token={{ssm_api_key}}
{
    "items": [
        {
            "service_code": "authCertDeletion"
        },
        {
            "service_code": "clientDeletion"
        },
        {
            "service_code": "clientReg"
        },
        {
            "service_code": "ownerChange"
        },
        {
            "service_code": "clientEnable"
        },
        {
            "service_code": "clientDisable"
        },
        {
            "service_code": "addressChange"
        }
    ]
}

# Enable management subsystem on management Security Server
PUT https://{{ssm_host}}:{{ssm_port}}/api/v1/service-descriptions/{{ssm_management_service_id}}/enable
Authorization: X-Road-ApiKey token={{ssm_api_key}}

# TODO: This should be 204 according to the OpenAPI description but is 200:
# https://github.com/nordic-institute/X-Road/blob/e14d198f704b34b4d1789c2972e816152b6a35f8/src/security-server/openapi-model/src/main/resources/META-INF/openapi-definition.yaml#L3908
HTTP 200

# Activate auth certificate on Security Server
PUT https://{{ssm_host}}:{{ssm_port}}/api/v1/token-certificates/{{ssm_auth_key_cert_hash}}/activate
Authorization: X-Road-ApiKey token={{ssm_api_key}}

HTTP 204

# Set timestamping service on Security Server
GET https://{{ssm_host}}:{{ssm_port}}/api/v1/timestamping-services
Authorization: X-Road-ApiKey token={{ssm_api_key}}

HTTP 200

[Captures]
tsa_name: jsonpath "$[0].name"
tsa_url: jsonpath "$[0].url"

POST https://{{ssm_host}}:{{ssm_port}}/api/v1/system/timestamping-services
Authorization: X-Road-ApiKey token={{ssm_api_key}}
{
    "name": "{{tsa_name}}",
    "url": "{{tsa_url}}"
}

HTTP 201
