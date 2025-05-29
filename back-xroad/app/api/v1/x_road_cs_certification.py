# app/api/v1/certification_services.py
from fastapi import APIRouter, HTTPException, UploadFile, File, Query, Form, Depends
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.core.config import settings
from app.utils.xroad_client import xroad_client, create_xroad_client
from app.schemas.x_road_config import XRoadConfigParams, XRoadEnvironment

router = APIRouter(prefix="/certification-services", tags=["X-Road Central Server - Certification Services"])

# Helper function to get XRoad client
def get_xroad_client(
    custom_base_url: Optional[str] = Query(None, description="Custom X-Road base URL"),
    custom_api_key: Optional[str] = Query(None, description="Custom X-Road API key"),
    env_prefix: Optional[XRoadEnvironment] = Query(None, description="Environment prefix")
):
    """Get XRoad client with configuration"""
    config = XRoadConfigParams(
        custom_base_url=custom_base_url,
        custom_api_key=custom_api_key,
        env_prefix=env_prefix
    )
    
    if config.env_prefix:
        env_config = settings.get_xroad_config(config.env_prefix.value)
        return create_xroad_client(
            base_url=config.custom_base_url or env_config["base_url"],
            api_key=config.custom_api_key or env_config["api_key"],
            timeout=env_config["timeout"]
        )
    
    if config.custom_base_url or config.custom_api_key:
        return create_xroad_client(
            base_url=config.custom_base_url,
            api_key=config.custom_api_key
        )
    
    return xroad_client

# ============== CERTIFICATION SERVICES APIs ==============

@router.get("/",
           summary="Get certification services",
           description="Hiển thị danh sách các dịch vụ chứng nhận đã được phê duyệt cho X-Road instance hiện tại")
async def get_certification_services(client=Depends(get_xroad_client)):
    """
    Get list of approved certification services for current X-Road instance
    
    Returns:
        List of certification services with basic information
        
    Example response:
        [
            {
                "id": 123,
                "name": "Name",
                "not_after": "2022-01-17T00:00:00.001Z",
                "not_before": "2022-01-17T00:00:00.001Z"
            }
        ]
    """
    result = await client.get("/certification-services")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to get certification services")
        )
    return result["data"]

@router.post("/",
            summary="Add certification service",
            description="Thêm mới một dịch vụ chứng nhận vào danh sách các dịch vụ được phê duyệt")
async def add_certification_service(
    certificate: UploadFile = File(..., description="Certificate file"),
    certificate_profile_info: str = Form(..., description="Certificate profile info class"),
    tls_auth: bool = Form(False, description="Enable TLS authentication"),
    acme_server_directory_url: Optional[str] = Form(None, description="ACME server directory URL"),
    acme_server_ip_address: Optional[str] = Form(None, description="ACME server IP address"),
    authentication_certificate_profile_id: Optional[str] = Form(None, description="Authentication certificate profile ID"),
    signing_certificate_profile_id: Optional[str] = Form(None, description="Signing certificate profile ID"),
    client=Depends(get_xroad_client)
):
    """
    Add new certification service to approved services list
    
    Parameters:
        - certificate: Certificate file (multipart/form-data)
        - certificate_profile_info: Certificate profile info provider class
        - tls_auth: Enable TLS authentication
        - acme_server_directory_url: ACME server directory URL (optional)
        - acme_server_ip_address: ACME server IP address (optional)
        - authentication_certificate_profile_id: Auth cert profile ID (optional)
        - signing_certificate_profile_id: Signing cert profile ID (optional)
    
    Returns:
        Detailed information about the added certification service
        
    Success response:
        {
            "id": 123,
            "name": "Name",
            "issuer_distinguished_name": "issuer123",
            "subject_distinguished_name": "subject123",
            "not_after": "2022-01-17T00:00:00.001Z",
            "not_before": "2022-01-17T00:00:00.001Z",
            "certificate_profile_info": "ee.ria.xroad.common.certificateprofile.impl.FiVRKCertificateProfileInfoProvider",
            "tls_auth": true,
            "acme_server_directory_url": "string",
            "acme_server_ip_address": "string",
            "authentication_certificate_profile_id": "string",
            "signing_certificate_profile_id": "string"
        }
        
    Warning response:
        {
            "error": {
                "code": "warnings_detected"
            },
            "status": 400,
            "warnings": [
                {
                    "code": "auth_key_with_registered_cert_warning",
                    "metadata": ["0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF"]
                }
            ]
        }
    """
    # Read certificate file
    cert_content = await certificate.read()
    
    # Prepare multipart form data
    files = {"certificate": (certificate.filename, cert_content, certificate.content_type or "application/x-x509-ca-cert")}
    
    # Prepare form data
    data = {
        "certificate_profile_info": certificate_profile_info,
        "tls_auth": str(tls_auth).lower()
    }
    
    # Add optional fields
    if acme_server_directory_url:
        data["acme_server_directory_url"] = acme_server_directory_url
    if acme_server_ip_address:
        data["acme_server_ip_address"] = acme_server_ip_address
    if authentication_certificate_profile_id:
        data["authentication_certificate_profile_id"] = authentication_certificate_profile_id
    if signing_certificate_profile_id:
        data["signing_certificate_profile_id"] = signing_certificate_profile_id
    
    result = await client.post("/certification-services", files=files, data=data)
    
    # Handle warnings (status 400 with warnings_detected)
    if result.get("status_code") == 400 and "warnings" in result.get("data", {}):
        raise HTTPException(
            status_code=400,
            detail=result["data"]
        )
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to add certification service")
        )
    
    return result["data"]

@router.get("/{certification_service_id}",
           summary="Get certification service details",
           description="Hiển thị chi tiết của một dịch vụ chứng nhận đã được phê duyệt")
async def get_certification_service(
    certification_service_id: int,
    client=Depends(get_xroad_client)
):
    """
    Get details of an approved certification service
    
    Parameters:
        - certification_service_id: ID of the certification service
    
    Returns:
        Detailed information about the certification service
        
    Example response:
        {
            "id": 123,
            "name": "Name",
            "issuer_distinguished_name": "issuer123",
            "subject_distinguished_name": "subject123",
            "not_after": "2022-01-17T00:00:00.001Z",
            "not_before": "2022-01-17T00:00:00.001Z",
            "certificate_profile_info": "ee.ria.xroad.common.certificateprofile.impl.FiVRKCertificateProfileInfoProvider",
            "tls_auth": true,
            "acme_server_directory_url": "string",
            "acme_server_ip_address": "string",
            "authentication_certificate_profile_id": "string",
            "signing_certificate_profile_id": "string"
        }
    """
    result = await client.get(f"/certification-services/{certification_service_id}")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to get certification service {certification_service_id}")
        )
    return result["data"]

@router.delete("/{certification_service_id}",
              summary="Delete certification service",
              description="Xóa một dịch vụ chứng nhận khỏi danh sách các dịch vụ đã được phê duyệt")
async def delete_certification_service(
    certification_service_id: int,
    client=Depends(get_xroad_client)
):
    """
    Delete a certification service from approved services list
    
    Parameters:
        - certification_service_id: ID of the certification service to delete
    
    Returns:
        Confirmation message
    """
    result = await client.delete(f"/certification-services/{certification_service_id}")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to delete certification service {certification_service_id}")
        )
    
    return {"message": f"Certification service {certification_service_id} deleted successfully"}

@router.patch("/{certification_service_id}",
             summary="Update certification service",
             description="Cập nhật cấu hình của một dịch vụ chứng nhận đã được phê duyệt")
async def update_certification_service(
    certification_service_id: int,
    update_data: Dict[str, Any],
    client=Depends(get_xroad_client)
):
    """
    Update configuration of an approved certification service
    
    Parameters:
        - certification_service_id: ID of the certification service
        - update_data: JSON object with fields to update
    
    Request body example:
        {
            "certificate_profile_info": "ee.ria.xroad.common.certificateprofile.impl.FiVRKCertificateProfileInfoProvider",
            "tls_auth": "string",
            "acme_server_directory_url": "string",
            "acme_server_ip_address": "string",
            "authentication_certificate_profile_id": "string",
            "signing_certificate_profile_id": "string"
        }
    
    Returns:
        Updated certification service information
    """
    result = await client.patch(f"/certification-services/{certification_service_id}", data=update_data)
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to update certification service {certification_service_id}")
        )
    return result["data"]

# ============== CERTIFICATION SERVICE CERTIFICATE APIs ==============

@router.get("/{certification_service_id}/certificate",
           summary="Get certification service certificate",
           description="Hiển thị chi tiết của chứng chỉ dịch vụ chứng nhận đã được phê duyệt")
async def get_certification_service_certificate(
    certification_service_id: int,
    client=Depends(get_xroad_client)
):
    """
    Get certificate details of an approved certification service
    
    Parameters:
        - certification_service_id: ID of the certification service
    
    Returns:
        Certificate details
        
    Example response:
        {
            "hash": "1234567890ABCDEF",
            "issuer_common_name": "domain.com",
            "issuer_distinguished_name": "issuer123",
            "key_usages": ["NON_REPUDIATION"],
            "not_after": "2022-01-17T00:00:00.001Z",
            "not_before": "2022-01-17T00:00:00.001Z",
            "public_key_algorithm": "sha256WithRSAEncryption",
            "rsa_public_key_exponent": 65537,
            "rsa_public_key_modulus": "c44421d601...",
            "serial": "123456789",
            "signature": "30af2fdc1780...",
            "signature_algorithm": "sha256WithRSAEncryption",
            "subject_alternative_names": "DNS:*.example.org",
            "subject_common_name": "domain.com",
            "subject_distinguished_name": "subject123",
            "version": 3
        }
    """
    result = await client.get(f"/certification-services/{certification_service_id}/certificate")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to get certificate for certification service {certification_service_id}")
        )
    return result["data"]

# ============== INTERMEDIATE CAs APIs ==============

@router.get("/{certification_service_id}/intermediate-cas",
           summary="Get intermediate CAs",
           description="Hiển thị danh sách các tổ chức chứng nhận trung gian được cấu hình cho một dịch vụ chứng nhận")
async def get_intermediate_cas(
    certification_service_id: int,
    client=Depends(get_xroad_client)
):
    """
    Get list of intermediate CAs configured for a certification service
    
    Parameters:
        - certification_service_id: ID of the certification service
    
    Returns:
        List of intermediate CAs with certificate details
    """
    result = await client.get(f"/certification-services/{certification_service_id}/intermediate-cas")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to get intermediate CAs for certification service {certification_service_id}")
        )
    return result["data"]

@router.post("/{certification_service_id}/intermediate-cas",
            summary="Add intermediate CA",
            description="Cấu hình tổ chức chứng nhận trung gian mới cho một dịch vụ chứng nhận")
async def add_intermediate_ca(
    certification_service_id: int,
    certificate: UploadFile = File(..., description="Intermediate CA certificate file"),
    client=Depends(get_xroad_client)
):
    """
    Configure new intermediate CA for a certification service
    
    Parameters:
        - certification_service_id: ID of the certification service
        - certificate: Intermediate CA certificate file (multipart/form-data)
    
    Returns:
        Added intermediate CA information with certificate details
    """
    # Read certificate file
    cert_content = await certificate.read()
    
    # Prepare multipart form data
    files = {"certificate": (certificate.filename, cert_content, certificate.content_type or "application/x-x509-ca-cert")}
    
    result = await client.post(f"/certification-services/{certification_service_id}/intermediate-cas", files=files)
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to add intermediate CA for certification service {certification_service_id}")
        )
    return result["data"]

# ============== OCSP RESPONDERS APIs ==============

@router.get("/{certification_service_id}/ocsp-responders",
           summary="Get OCSP responders",
           description="Hiển thị danh sách các OCSP responders được cấu hình cho dịch vụ chứng nhận")
async def get_ocsp_responders(
    certification_service_id: int,
    client=Depends(get_xroad_client)
):
    """
    Get list of OCSP responders configured for certification service
    
    Parameters:
        - certification_service_id: ID of the certification service
    
    Returns:
        List of OCSP responders
        
    Example response:
        [
            {
                "url": "http://dev.xroad.rocks:123",
                "id": 123,
                "has_certificate": false
            }
        ]
    """
    result = await client.get(f"/certification-services/{certification_service_id}/ocsp-responders")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to get OCSP responders for certification service {certification_service_id}")
        )
    return result["data"]

@router.post("/{certification_service_id}/ocsp-responders",
            summary="Add OCSP responder",
            description="Thêm một OCSP responder mới vào dịch vụ chứng nhận")
async def add_ocsp_responder(
    certification_service_id: int,
    url: str = Form(..., description="OCSP responder URL"),
    certificate: Optional[UploadFile] = File(None, description="OCSP responder certificate (optional)"),
    client=Depends(get_xroad_client)
):
    """
    Add new OCSP responder to certification service
    
    Parameters:
        - certification_service_id: ID of the certification service
        - url: OCSP responder URL
        - certificate: OCSP responder certificate file (optional, multipart/form-data)
    
    Returns:
        Added OCSP responder information
        
    Example response:
        {
            "url": "http://dev.xroad.rocks:123",
            "id": 123,
            "has_certificate": false
        }
    """
    # Prepare form data
    data = {"url": url}
    files = {}
    
    # Add certificate if provided
    if certificate:
        cert_content = await certificate.read()
        files["certificate"] = (certificate.filename, cert_content, certificate.content_type or "application/x-x509-ca-cert")
    
    result = await client.post(f"/certification-services/{certification_service_id}/ocsp-responders", files=files, data=data)
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to add OCSP responder for certification service {certification_service_id}")
        )
    return result["data"]

# ============== HEALTH CHECK ==============

@router.get("/health",
           summary="Health check for certification services")
async def certification_services_health_check(client=Depends(get_xroad_client)):
    """Check if certification services APIs are accessible"""
    try:
        # Test get certification services endpoint
        result = await client.get("/certification-services")
        
        return {
            "status": "healthy" if result.get("status_code", 200) < 400 else "unhealthy",
            "certification_api_accessible": result.get("status_code", 200) < 400,
            "response_time": "OK"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "certification_api_accessible": False,
            "error": str(e)
        }