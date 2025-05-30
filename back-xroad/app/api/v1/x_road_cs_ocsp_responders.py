from fastapi import APIRouter, HTTPException, Query, Depends, UploadFile, File, Form
from typing import Optional, List, Dict, Any
from app.core.config import settings
from app.utils.xroad_client_cs import xroad_client, create_xroad_client
from app.schemas.x_road_config import XRoadConfigParams, XRoadEnvironment

router = APIRouter(prefix="/ocsp-responders", tags=["X-Road Central Server - OCSP Responders"])

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

# ============== OCSP RESPONDERS APIs ==============

@router.get("/{ocsp_responder_id}",
           summary="Get OCSP Responder details",
           description="Xem chi tiết của một OCSP Responder")
async def get_ocsp_responder(
    ocsp_responder_id: int,
    client=Depends(get_xroad_client)
):
    """
    View details of an OCSP Responder
    
    Parameters:
        - ocsp_responder_id: ID of the OCSP Responder
    
    Returns:
        OCSP Responder information including URL, ID and certificate status
        
    Example response:
        {
            "url": "http://dev.xroad.rocks:123",
            "id": 123,
            "has_certificate": false
        }
    """
    result = await client.get(f"/ocsp-responders/{ocsp_responder_id}")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to get OCSP Responder {ocsp_responder_id}")
        )
    return result["data"]

@router.delete("/{ocsp_responder_id}",
              summary="Delete OCSP Responder",
              description="Xóa một OCSP Responder")
async def delete_ocsp_responder(
    ocsp_responder_id: int,
    client=Depends(get_xroad_client)
):
    """
    Delete an OCSP Responder
    
    Parameters:
        - ocsp_responder_id: ID of the OCSP Responder to delete
    
    Returns:
        Confirmation message
    """
    result = await client.delete(f"/ocsp-responders/{ocsp_responder_id}")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to delete OCSP Responder {ocsp_responder_id}")
        )
    
    return {"message": f"OCSP Responder {ocsp_responder_id} deleted successfully"}

@router.patch("/{ocsp_responder_id}",
             summary="Update OCSP Responder",
             description="Cập nhật thông tin của OCSP Responder")
async def update_ocsp_responder(
    ocsp_responder_id: int,
    url: Optional[str] = Form(None, description="New OCSP Responder URL"),
    certificate: Optional[UploadFile] = File(None, description="New OCSP Responder certificate"),
    client=Depends(get_xroad_client)
):
    """
    Update OCSP Responder information
    
    Parameters:
        - ocsp_responder_id: ID of the OCSP Responder to update
        - url: New OCSP Responder URL (optional)
        - certificate: New OCSP Responder certificate file (optional, multipart/form-data)
    
    Returns:
        Updated OCSP Responder information
        
    Example response:
        {
            "url": "http://dev.xroad.rocks:123",
            "id": 123,
            "has_certificate": false
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
    
    result = await client.patch(f"/ocsp-responders/{ocsp_responder_id}", files=files, data=data)
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to update OCSP Responder {ocsp_responder_id}")
        )
    return result["data"]

@router.get("/{ocsp_responder_id}/certificate",
           summary="Get OCSP Responder certificate",
           description="Xem chứng chỉ của OCSP Responder đã được phê duyệt")
async def get_ocsp_responder_certificate(
    ocsp_responder_id: int,
    client=Depends(get_xroad_client)
):
    """
    View certificate of approved OCSP Responder
    
    Parameters:
        - ocsp_responder_id: ID of the OCSP Responder
    
    Returns:
        Detailed certificate information of the OCSP Responder
        
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
    result = await client.get(f"/ocsp-responders/{ocsp_responder_id}/certificate")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to get certificate for OCSP Responder {ocsp_responder_id}")
        )
    return result["data"]

# ============== HEALTH CHECK ==============

@router.get("/health",
           summary="Health check for OCSP Responders APIs")
async def ocsp_responders_health_check(client=Depends(get_xroad_client)):
    """Check if OCSP Responders APIs are accessible"""
    try:
        # Since we can't test a specific OCSP responder without knowing an ID,
        # we'll test by trying to get a non-existent one and check if we get a proper 404
        # This at least verifies the API endpoint is accessible
        result = await client.get("/ocsp-responders/999999")
        
        # We expect either success (if responder exists) or 404 (which means API is working)
        api_accessible = result.get("status_code", 500) in [200, 404]
        
        return {
            "status": "healthy" if api_accessible else "unhealthy",
            "ocsp_responders_api_accessible": api_accessible,
            "response_time": "OK",
            "note": "Health check performed by testing API endpoint accessibility"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "ocsp_responders_api_accessible": False,
            "error": str(e)
        }