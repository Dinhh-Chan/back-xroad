# app/api/v1/timestamping_management_requests.py
from fastapi import APIRouter, HTTPException, Query, Depends, UploadFile, File, Form
from typing import Optional, List, Dict, Any
from app.core.config import settings
from app.utils.xroad_client import xroad_client, create_xroad_client
from app.schemas.x_road_config import XRoadConfigParams, XRoadEnvironment

router = APIRouter(tags=["X-Road Central Server - Timestamping Services & Management Requests"])

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

# ============== TIMESTAMPING SERVICES APIs ==============

@router.get("/timestamping-services",
           summary="Get timestamping services",
           description="CS administrator xem danh sách dịch vụ ghi thời gian đã được phê duyệt")
async def get_timestamping_services(client=Depends(get_xroad_client)):
    """
    CS administrator view list of approved timestamping services
    
    Returns:
        List of approved timestamping services with certificates and details
        
    Example response:
        [
            {
                "url": "http://dev.xroad.rocks:8899",
                "certificate": {
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
                },
                "id": 123,
                "timestamping_interval": 60,
                "cost": "FREE"
            }
        ]
    """
    result = await client.get("/timestamping-services")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to get timestamping services")
        )
    return result["data"]

@router.post("/timestamping-services",
            summary="Add timestamping service",
            description="CS administrator thêm một dịch vụ ghi thời gian vào danh sách đã phê duyệt")
async def add_timestamping_service(
    url: str = Form(..., description="Timestamping service URL"),
    certificate: UploadFile = File(..., description="Timestamping service certificate"),
    client=Depends(get_xroad_client)
):
    """
    CS administrator add timestamping service to approved list
    
    Parameters:
        - url: Timestamping service URL
        - certificate: Timestamping service certificate file (multipart/form-data)
    
    Returns:
        Added timestamping service information with certificate details
        
    Example response:
        {
            "url": "http://dev.xroad.rocks:8899",
            "certificate": {
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
            },
            "id": 123,
            "timestamping_interval": 60,
            "cost": "FREE"
        }
    """
    # Read certificate file content
    cert_content = await certificate.read()
    
    # Prepare multipart form data
    files = {"certificate": (certificate.filename, cert_content, certificate.content_type or "application/x-x509-ca-cert")}
    data = {"url": url}
    
    result = await client.post("/timestamping-services", files=files, data=data)
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to add timestamping service")
        )
    return result["data"]

@router.get("/timestamping-services/{timestamping_service_id}",
           summary="Get timestamping service details",
           description="Xem chi tiết của một dịch vụ ghi thời gian đã được phê duyệt")
async def get_timestamping_service(
    timestamping_service_id: int,
    client=Depends(get_xroad_client)
):
    """
    View details of an approved timestamping service
    
    Parameters:
        - timestamping_service_id: ID of the timestamping service
    
    Returns:
        Detailed information about the timestamping service
        
    Example response:
        {
            "url": "http://dev.xroad.rocks:8899",
            "certificate": {
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
            },
            "id": 123,
            "timestamping_interval": 60,
            "cost": "FREE"
        }
    """
    result = await client.get(f"/timestamping-services/{timestamping_service_id}")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to get timestamping service {timestamping_service_id}")
        )
    return result["data"]

@router.delete("/timestamping-services/{timestamping_service_id}",
              summary="Delete timestamping service",
              description="Xóa một dịch vụ ghi thời gian đã được phê duyệt")
async def delete_timestamping_service(
    timestamping_service_id: int,
    client=Depends(get_xroad_client)
):
    """
    Delete an approved timestamping service
    
    Parameters:
        - timestamping_service_id: ID of the timestamping service to delete
    
    Returns:
        Confirmation message
    """
    result = await client.delete(f"/timestamping-services/{timestamping_service_id}")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to delete timestamping service {timestamping_service_id}")
        )
    
    return {"message": f"Timestamping service {timestamping_service_id} deleted successfully"}

@router.patch("/timestamping-services/{timestamping_service_id}",
             summary="Update timestamping service",
             description="Chỉnh sửa URL hoặc chứng chỉ của một dịch vụ ghi thời gian")
async def update_timestamping_service(
    timestamping_service_id: int,
    url: Optional[str] = Form(None, description="New timestamping service URL"),
    certificate: Optional[UploadFile] = File(None, description="New timestamping service certificate (optional)"),
    client=Depends(get_xroad_client)
):
    """
    Edit URL or certificate of a timestamping service
    
    Parameters:
        - timestamping_service_id: ID of the timestamping service to update
        - url: New timestamping service URL (optional)
        - certificate: New timestamping service certificate file (optional, multipart/form-data)
    
    Returns:
        Updated timestamping service information
        
    Example response:
        {
            "url": "http://dev.xroad.rocks:8899",
            "certificate": {
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
            },
            "id": 123,
            "timestamping_interval": 60,
            "cost": "FREE"
        }
    """
    # Prepare form data
    data = {}
    files = {}
    
    # Add URL if provided
    if url:
        data["url"] = url
    
    # Add certificate if provided
    if certificate:
        cert_content = await certificate.read()
        files["certificate"] = (certificate.filename, cert_content, certificate.content_type or "application/x-x509-ca-cert")
    
    # At least one field should be provided for update
    if not data and not files:
        raise HTTPException(
            status_code=400,
            detail="At least one field (url or certificate) must be provided for update"
        )
    
    result = await client.patch(f"/timestamping-services/{timestamping_service_id}", files=files, data=data)
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to update timestamping service {timestamping_service_id}")
        )
    return result["data"]

# ============== MANAGEMENT REQUESTS APIs ==============

@router.get("/management-requests",
           summary="Get management requests",
           description="Danh sách các yêu cầu quản lý")
async def get_management_requests(
    sort: Optional[str] = Query(None, description="Sort field"),
    desc: Optional[bool] = Query(None, description="Sort descending"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: Optional[int] = Query(25, description="Page size limit"),
    offset: Optional[int] = Query(0, description="Page offset"),
    client=Depends(get_xroad_client)
):
    """
    List of management requests
    
    Parameters:
        - sort: Sort field (optional)
        - desc: Sort in descending order (optional)
        - status: Filter by request status (optional)
        - limit: Page size limit (default: 25)
        - offset: Page offset (default: 0)
    
    Returns:
        Paginated list of management requests
        
    Example response:
        {
            "items": [
                {
                    "id": 0,
                    "type": "AUTH_CERT_REGISTRATION_REQUEST",
                    "origin": "CENTER",
                    "security_server_owner": "string",
                    "security_server_id": {
                        "instance_id": "FI",
                        "type": "SERVER",
                        "member_class": "GOV",
                        "member_code": "123",
                        "encoded_id": "string",
                        "server_code": "server123"
                    },
                    "address": "string",
                    "status": "WAITING",
                    "client_id": {
                        "instance_id": "FI",
                        "type": "MEMBER",
                        "member_class": "GOV",
                        "member_code": "123",
                        "encoded_id": "string",
                        "subsystem_code": "ABC"
                    },
                    "client_owner_name": "string",
                    "created_at": "2024-10-08T08:50:37.363Z"
                }
            ],
            "paging_metadata": {
                "total_items": 0,
                "items": 0,
                "limit": 25,
                "offset": 0
            }
        }
    """
    # Build query parameters
    params = {}
    if sort:
        params["sort"] = sort
    if desc is not None:
        params["desc"] = str(desc).lower()
    if status:
        params["status"] = status
    if limit:
        params["limit"] = limit
    if offset:
        params["offset"] = offset
    
    result = await client.get("/management-requests", params=params)
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to get management requests")
        )
    return result["data"]

@router.get("/management-requests/{management_request_id}",
           summary="Get management request details",
           description="Xem chi tiết yêu cầu quản lý")
async def get_management_request(
    management_request_id: int,
    client=Depends(get_xroad_client)
):
    """
    View detailed information of a management request
    
    Parameters:
        - management_request_id: ID of the management request
    
    Returns:
        Detailed management request information including certificate details
        
    Example response:
        {
            "id": 0,
            "type": "AUTH_CERT_REGISTRATION_REQUEST",
            "origin": "CENTER",
            "security_server_owner": "string",
            "security_server_id": {
                "instance_id": "FI",
                "type": "SERVER",
                "member_class": "GOV",
                "member_code": "123",
                "encoded_id": "string",
                "server_code": "server123"
            },
            "address": "string",
            "status": "WAITING",
            "client_id": {
                "instance_id": "FI",
                "type": "MEMBER",
                "member_class": "GOV",
                "member_code": "123",
                "encoded_id": "string",
                "subsystem_code": "ABC"
            },
            "client_owner_name": "string",
            "created_at": "2024-10-08T08:51:16.236Z",
            "comments": "string",
            "certificate_details": {
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
    result = await client.get(f"/management-requests/{management_request_id}")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to get management request {management_request_id}")
        )
    return result["data"]

# ============== HEALTH CHECK ==============

@router.get("/timestamping-management/health",
           summary="Health check for timestamping services and management requests APIs")
async def timestamping_management_health_check(client=Depends(get_xroad_client)):
    """Check if timestamping services and management requests APIs are accessible"""
    try:
        # Test get timestamping services endpoint
        timestamping_result = await client.get("/timestamping-services")
        timestamping_accessible = timestamping_result.get("status_code", 200) < 400
        
        # Test get management requests endpoint
        management_result = await client.get("/management-requests")
        management_accessible = management_result.get("status_code", 200) < 400
        
        overall_status = "healthy" if (timestamping_accessible and management_accessible) else "unhealthy"
        
        return {
            "status": overall_status,
            "timestamping_services_api_accessible": timestamping_accessible,
            "management_requests_api_accessible": management_accessible,
            "response_time": "OK"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamping_services_api_accessible": False,
            "management_requests_api_accessible": False,
            "error": str(e)
        }