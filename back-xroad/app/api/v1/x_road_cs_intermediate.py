# app/api/v1/additional_apis.py
from fastapi import APIRouter, HTTPException, Query, Depends, UploadFile, File, Form
from typing import Optional, List, Dict, Any
from app.core.config import settings
from app.utils.xroad_client_cs import xroad_client, create_xroad_client
from app.schemas.x_road_config import XRoadConfigParams, XRoadEnvironment

router = APIRouter(tags=["X-Road Central Server - Intermediate"])

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

# ============== CONFIGURATION SOURCES APIs ==============

@router.get("/configuration-sources/{configuration_type}/download-url",
           summary="Get configuration source download URL",
           description="Xem URL tải xuống của một nguồn cấu hình cụ thể")
async def get_configuration_source_download_url(
    configuration_type: str,
    client=Depends(get_xroad_client)
):
    """
    View download URL of a specific configuration source
    
    Parameters:
        - configuration_type: Type of configuration source (INTERNAL, EXTERNAL)
    
    Returns:
        Download URL for the configuration source
        
    Example response:
        {
            "url": "https://dev.xroad.rocks/globalconf"
        }
    """
    result = await client.get(f"/configuration-sources/{configuration_type}/download-url")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to get download URL for configuration source {configuration_type}")
        )
    return result["data"]

# ============== CENTRAL SERVER INITIALIZATION APIs ==============

@router.post("/initialization",
            summary="Initialize Central Server",
            description="Khởi tạo một máy chủ trung tâm mới với cấu hình ban đầu được cung cấp")
async def initialize_central_server(
    init_data: Dict[str, str],
    client=Depends(get_xroad_client)
):
    """
    Initialize new central server with provided initial configuration
    May return metadata information in error response
    
    Parameters:
        - init_data: JSON object with initialization parameters
    
    Request body example:
        {
            "instance_identifier": "FI-TEST",
            "central_server_address": "string",
            "software_token_pin": "sup3rs3cr3t_p!n"
        }
    
    Returns:
        Initialization result
    """
    result = await client.post("/initialization", data=init_data)
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to initialize central server")
        )
    return result["data"]

@router.get("/initialization/status",
           summary="Get initialization status",
           description="Kiểm tra trạng thái khởi tạo của máy chủ trung tâm")
async def get_initialization_status(client=Depends(get_xroad_client)):
    """
    Check initialization status of central server
    
    Returns:
        Central server initialization status
        
    Example response:
        {
            "instance_identifier": "FI-TEST",
            "central_server_address": "string",
            "software_token_init_status": "INITIALIZED"
        }
    """
    result = await client.get("/initialization/status")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to get initialization status")
        )
    return result["data"]

# ============== INTERMEDIATE CERTIFICATE AUTHORITIES APIs ==============

@router.get("/intermediate-cas/{intermediate_ca_id}",
           summary="Get intermediate CA details",
           description="Xem chi tiết của một CA trung gian")
async def get_intermediate_ca(
    intermediate_ca_id: int,
    client=Depends(get_xroad_client)
):
    """
    View details of an intermediate CA
    
    Parameters:
        - intermediate_ca_id: ID of the intermediate CA
    
    Returns:
        Detailed information about the intermediate CA including certificate details
        
    Example response:
        {
            "id": 123,
            "ca_certificate": {
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
        }
    """
    result = await client.get(f"/intermediate-cas/{intermediate_ca_id}")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to get intermediate CA {intermediate_ca_id}")
        )
    return result["data"]

@router.delete("/intermediate-cas/{intermediate_ca_id}",
              summary="Delete intermediate CA",
              description="Xóa một CA trung gian")
async def delete_intermediate_ca(
    intermediate_ca_id: int,
    client=Depends(get_xroad_client)
):
    """
    Delete an intermediate CA
    
    Parameters:
        - intermediate_ca_id: ID of the intermediate CA to delete
    
    Returns:
        Confirmation message
    """
    result = await client.delete(f"/intermediate-cas/{intermediate_ca_id}")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to delete intermediate CA {intermediate_ca_id}")
        )
    
    return {"message": f"Intermediate CA {intermediate_ca_id} deleted successfully"}

# ============== INTERMEDIATE CA OCSP RESPONDERS APIs ==============

@router.get("/intermediate-cas/{intermediate_ca_id}/ocsp-responders",
           summary="Get intermediate CA OCSP responders",
           description="Xem danh sách các OCSP responders được cấu hình cho một CA trung gian")
async def get_intermediate_ca_ocsp_responders(
    intermediate_ca_id: int,
    client=Depends(get_xroad_client)
):
    """
    View list of OCSP responders configured for an intermediate CA
    
    Parameters:
        - intermediate_ca_id: ID of the intermediate CA
    
    Returns:
        List of OCSP responders for the intermediate CA
        
    Example response:
        [
            {
                "url": "http://dev.xroad.rocks:123",
                "id": 123,
                "has_certificate": false
            }
        ]
    """
    result = await client.get(f"/intermediate-cas/{intermediate_ca_id}/ocsp-responders")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to get OCSP responders for intermediate CA {intermediate_ca_id}")
        )
    return result["data"]

@router.post("/intermediate-cas/{intermediate_ca_id}/ocsp-responders",
            summary="Add OCSP responder to intermediate CA",
            description="Thêm thông tin dịch vụ OCSP responder cho một CA trung gian")
async def add_intermediate_ca_ocsp_responder(
    intermediate_ca_id: int,
    url: str = Form(..., description="OCSP responder URL"),
    certificate: Optional[UploadFile] = File(None, description="OCSP responder certificate (optional)"),
    client=Depends(get_xroad_client)
):
    """
    Add OCSP responder service information for an intermediate CA
    
    Parameters:
        - intermediate_ca_id: ID of the intermediate CA
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
    
    result = await client.post(f"/intermediate-cas/{intermediate_ca_id}/ocsp-responders", files=files, data=data)
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to add OCSP responder for intermediate CA {intermediate_ca_id}")
        )
    return result["data"]

@router.delete("/intermediate-cas/{intermediate_ca_id}/ocsp-responders/{ocsp_responder_id}",
              summary="Delete OCSP responder from intermediate CA",
              description="Xóa thông tin dịch vụ OCSP responder cho một CA trung gian")
async def delete_intermediate_ca_ocsp_responder(
    intermediate_ca_id: int,
    ocsp_responder_id: int,
    client=Depends(get_xroad_client)
):
    """
    Delete OCSP responder service information for an intermediate CA
    
    Parameters:
        - intermediate_ca_id: ID of the intermediate CA
        - ocsp_responder_id: ID of the OCSP responder to delete
    
    Returns:
        Confirmation message
    """
    result = await client.delete(f"/intermediate-cas/{intermediate_ca_id}/ocsp-responders/{ocsp_responder_id}")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to delete OCSP responder {ocsp_responder_id} from intermediate CA {intermediate_ca_id}")
        )
    
    return {"message": f"OCSP responder {ocsp_responder_id} deleted from intermediate CA {intermediate_ca_id} successfully"}

# ============== HEALTH CHECK ==============

@router.get("/additional-apis/health",
           summary="Health check for additional APIs")
async def additional_apis_health_check(client=Depends(get_xroad_client)):
    """Check if additional APIs are accessible"""
    try:
        # Test get initialization status endpoint
        result = await client.get("/initialization/status")
        
        return {
            "status": "healthy" if result.get("status_code", 200) < 400 else "unhealthy",
            "additional_apis_accessible": result.get("status_code", 200) < 400,
            "response_time": "OK"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "additional_apis_accessible": False,
            "error": str(e)
        }