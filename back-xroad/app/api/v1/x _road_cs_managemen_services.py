from fastapi import APIRouter, HTTPException, Query, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import Optional, List, Dict, Any
import io
from app.core.config import settings
from app.utils.xroad_client_cs import xroad_client, create_xroad_client
from app.schemas.x_road_config import XRoadConfigParams, XRoadEnvironment

router = APIRouter(prefix="/management-services", tags=["X-Road Central Server - Management Services"])

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

# ============== MANAGEMENT SERVICES CONFIGURATION APIs ==============

@router.get("/configuration",
           summary="Get management services configuration",
           description="Xem cấu hình dịch vụ quản lý của máy chủ trung tâm")
async def get_management_services_configuration(client=Depends(get_xroad_client)):
    """
    View management services configuration of central server
    
    Returns:
        Management services configuration with provider details
        
    Example response:
        {
            "service_provider_id": "FI:GOV:123:ABC",
            "security_server_id": "CS:ORG:111:SS1",
            "security_server_owners_global_group_code": "security-server-owners",
            "service_provider_name": "NIIS",
            "services_address": "https://dev.xroad.rocks/managementservice/manage/",
            "wsdl_address": "https://dev.xroad.rocks/managementservices.wsdl"
        }
    """
    result = await client.get("/management-services-configuration")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to get management services configuration")
        )
    return result["data"]

@router.patch("/configuration",
             summary="Update management services configuration",
             description="Cập nhật cấu hình dịch vụ quản lý của máy chủ trung tâm")
async def update_management_services_configuration(
    config_data: Dict[str, str],
    client=Depends(get_xroad_client)
):
    """
    Update management services configuration of central server
    
    Parameters:
        - config_data: JSON object with configuration to update
    
    Request body example:
        {
            "service_provider_id": "FI:GOV:123:ABC"
        }
    
    Returns:
        Updated management services configuration
        
    Example response:
        {
            "service_provider_id": "FI:GOV:123:ABC",
            "security_server_id": "CS:ORG:111:SS1",
            "security_server_owners_global_group_code": "security-server-owners",
            "service_provider_name": "NIIS",
            "services_address": "https://dev.xroad.rocks/managementservice/manage/",
            "wsdl_address": "https://dev.xroad.rocks/managementservices.wsdl"
        }
    """
    result = await client.patch("/management-services-configuration", data=config_data)
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to update management services configuration")
        )
    return result["data"]

@router.post("/configuration/register-provider",
            summary="Register management service provider",
            description="Đăng ký nhà cung cấp dịch vụ quản lý làm client của server bảo mật")
async def register_management_service_provider(
    provider_data: Dict[str, str],
    client=Depends(get_xroad_client)
):
    """
    Register management service provider as security server client
    
    Parameters:
        - provider_data: JSON object with service provider information
    
    Request body example:
        {
            "service_provider_id": "FI:GOV:123:ABC"
        }
    
    Returns:
        Registration result with updated configuration
        
    Example response:
        {
            "service_provider_id": "FI:GOV:123:ABC",
            "security_server_id": "CS:ORG:111:SS1",
            "security_server_owners_global_group_code": "security-server-owners",
            "service_provider_name": "NIIS",
            "services_address": "https://dev.xroad.rocks/managementservice/manage/",
            "wsdl_address": "https://dev.xroad.rocks/managementservices.wsdl"
        }
    """
    result = await client.post("/management-services-configuration/register-provider", data=provider_data)
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to register management service provider")
        )
    return result["data"]

# ============== MANAGEMENT SERVICES CERTIFICATE APIs ==============

@router.get("/configuration/certificate",
           summary="Get management services TLS certificate",
           description="Xem thông tin chứng chỉ TLS của dịch vụ quản lý")
async def get_management_services_certificate(client=Depends(get_xroad_client)):
    """
    View TLS certificate information of management service
    
    Returns:
        Detailed TLS certificate information
        
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
    result = await client.get("/management-services-configuration/certificate")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to get management services TLS certificate")
        )
    return result["data"]

@router.get("/configuration/download-certificate",
           summary="Download management services TLS certificate",
           description="Tải xuống chứng chỉ TLS của dịch vụ quản lý")
async def download_management_services_certificate(client=Depends(get_xroad_client)):
    """
    Download TLS certificate of management service
    
    Returns:
        Binary certificate file for download
    """
    result = await client.get("/management-services-configuration/download-certificate")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to download management services TLS certificate")
        )
    
    # Extract file content and content type
    content = result["data"]
    content_type = result.get("content_type", "application/x-x509-ca-cert")
    
    # Return as streaming response for file download
    return StreamingResponse(
        io.BytesIO(content),
        media_type=content_type,
        headers={
            "Content-Disposition": "attachment; filename=management_services_tls.crt",
            "Content-Length": str(len(content))
        }
    )

@router.post("/configuration/certificate",
            summary="Generate new TLS key and self-signed certificate",
            description="Tạo mới khóa TLS và chứng chỉ tự ký cho dịch vụ quản lý")
async def generate_management_services_certificate(client=Depends(get_xroad_client)):
    """
    Generate new TLS key and self-signed certificate for management service
    
    Returns:
        Generated certificate information
    """
    result = await client.post("/management-services-configuration/certificate")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to generate new TLS certificate for management services")
        )
    return result["data"]

@router.post("/configuration/generate-csr",
            summary="Generate certificate signing request",
            description="Tạo yêu cầu chứng chỉ mới")
async def generate_management_services_csr(
    csr_data: Dict[str, str],
    client=Depends(get_xroad_client)
):
    """
    Generate new certificate signing request
    
    Parameters:
        - csr_data: JSON object with distinguished name information
    
    Request body example:
        {
            "name": "C=FI, O=X-Road Test, OU=X-Road Test CA OU, CN=X-Road Test CA CN"
        }
    
    Returns:
        Generated CSR information
    """
    result = await client.post("/management-services-configuration/generate-csr", data=csr_data)
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to generate CSR for management services")
        )
    return result["data"]

@router.post("/configuration/upload-certificate",
            summary="Upload new TLS certificate",
            description="Tải lên chứng chỉ TLS mới cho dịch vụ quản lý")
async def upload_management_services_certificate(
    certificate: UploadFile = File(..., description="TLS certificate file"),
    client=Depends(get_xroad_client)
):
    """
    Upload new TLS certificate for management service
    
    Parameters:
        - certificate: TLS certificate file (multipart/form-data)
    
    Returns:
        Uploaded certificate information
        
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
    # Read certificate file content
    cert_content = await certificate.read()
    
    # Prepare multipart form data
    files = {"certificate": (certificate.filename, cert_content, certificate.content_type or "application/x-x509-ca-cert")}
    
    result = await client.post("/management-services-configuration/upload-certificate", files=files)
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to upload TLS certificate for management services")
        )
    return result["data"]

# ============== HEALTH CHECK ==============

@router.get("/health",
           summary="Health check for management services APIs")
async def management_services_health_check(client=Depends(get_xroad_client)):
    """Check if management services APIs are accessible"""
    try:
        # Test get management services configuration endpoint
        result = await client.get("/management-services-configuration")
        
        return {
            "status": "healthy" if result.get("status_code", 200) < 400 else "unhealthy",
            "management_services_api_accessible": result.get("status_code", 200) < 400,
            "response_time": "OK"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "management_services_api_accessible": False,
            "error": str(e)
        }