# app/api/v1/token_certificates.py
from fastapi import APIRouter, HTTPException, Query, Depends, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from typing import Optional, List, Dict, Any
import io
from app.core.config import settings
from app.utils.xroad_client_ss import xroad_client, create_xroad_client
from app.schemas.x_road_config import XRoadConfigParams, XRoadEnvironment

router = APIRouter(prefix="/token-certificates", tags=["Security Server - Token Certificates"])

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

# ============== TOKEN CERTIFICATES APIs ==============

@router.post("/",
            summary="Import certificate",
            description="Nhập chứng chỉ mới vào hệ thống")
async def import_certificate(
    file: UploadFile = File(..., description="Certificate file to import"),
    client=Depends(get_xroad_client)
):
    """
    Import new certificate into system
    
    Parameters:
        - file: Certificate file to import (multipart/form-data)
    
    Returns:
        Imported certificate information with details and status
        
    Example response:
        {
            "ocsp_status": "IN_USE",
            "owner_id": "FI:GOV:123",
            "active": true,
            "saved_to_configuration": true,
            "certificate_details": {
                "issuer_distinguished_name": "issuer123",
                "issuer_common_name": "domain.com",
                "subject_distinguished_name": "subject123",
                "subject_common_name": "domain.com",
                "not_before": "2018-12-15T00:00:00.001Z",
                "not_after": "2018-12-15T00:00:00.001Z",
                "serial": "123456789",
                "version": 3,
                "signature_algorithm": "sha256WithRSAEncryption",
                "signature": "30af2fdc1780...",
                "public_key_algorithm": "sha256WithRSAEncryption",
                "rsa_public_key_modulus": "c44421d601...",
                "rsa_public_key_exponent": 65537,
                "hash": "1234567890ABCDEF",
                "key_usages": ["NON_REPUDIATION"],
                "subject_alternative_names": "DNS:*.example.org"
            },
            "status": "IN_USE",
            "possible_actions": ["DELETE"]
        }
    """
    # Read certificate file content
    cert_content = await file.read()
    
    # Prepare multipart form data
    files = {"file": (file.filename, cert_content, file.content_type or "application/x-x509-ca-cert")}
    
    result = await client.post("/token-certificates", files=files)
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to import certificate")
        )
    
    return result["data"]

@router.get("/{hash}",
           summary="Get certificate information",
           description="Nhận thông tin chứng chỉ")
async def get_certificate(
    hash: str,
    client=Depends(get_xroad_client)
):
    """
    Get certificate information
    
    Parameters:
        - hash: Hash of the certificate
    
    Returns:
        Certificate information with details, status and possible actions
        
    Example response:
        {
            "ocsp_status": "IN_USE",
            "owner_id": "FI:GOV:123",
            "active": true,
            "saved_to_configuration": true,
            "certificate_details": {
                "issuer_distinguished_name": "issuer123",
                "issuer_common_name": "domain.com",
                "subject_distinguished_name": "subject123",
                "subject_common_name": "domain.com",
                "not_before": "2018-12-15T00:00:00.001Z",
                "not_after": "2018-12-15T00:00:00.001Z",
                "serial": "123456789",
                "version": 3,
                "signature_algorithm": "sha256WithRSAEncryption",
                "signature": "30af2fdc1780...",
                "public_key_algorithm": "sha256WithRSAEncryption",
                "rsa_public_key_modulus": "c44421d601...",
                "rsa_public_key_exponent": 65537,
                "hash": "1234567890ABCDEF",
                "key_usages": ["NON_REPUDIATION"],
                "subject_alternative_names": "DNS:*.example.org"
            },
            "status": "IN_USE",
            "possible_actions": ["DELETE"]
        }
    """
    result = await client.get(f"/token-certificates/{hash}")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to get certificate {hash}")
        )
    
    return result["data"]

@router.delete("/{hash}",
              summary="Delete certificate",
              description="Xóa chứng chỉ")
async def delete_certificate(
    hash: str,
    client=Depends(get_xroad_client)
):
    """
    Delete certificate
    
    Parameters:
        - hash: Hash of the certificate to delete
    
    Returns:
        Confirmation message
    """
    result = await client.delete(f"/token-certificates/{hash}")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to delete certificate {hash}")
        )
    
    return {"message": f"Certificate {hash} deleted successfully"}

@router.put("/{hash}/activate",
           summary="Activate certificate",
           description="Kích hoạt chứng chỉ")
async def activate_certificate(
    hash: str,
    client=Depends(get_xroad_client)
):
    """
    Activate certificate
    
    Parameters:
        - hash: Hash of the certificate to activate
    
    Returns:
        Activation result
    """
    result = await client.put(f"/token-certificates/{hash}/activate")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to activate certificate {hash}")
        )
    
    return {"message": f"Certificate {hash} activated successfully"}

@router.put("/{hash}/disable",
           summary="Disable certificate",
           description="Vô hiệu hóa chứng chỉ")
async def disable_certificate(
    hash: str,
    client=Depends(get_xroad_client)
):
    """
    Disable certificate
    
    Parameters:
        - hash: Hash of the certificate to disable
    
    Returns:
        Disable result
    """
    result = await client.put(f"/token-certificates/{hash}/disable")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to disable certificate {hash}")
        )
    
    return {"message": f"Certificate {hash} disabled successfully"}

@router.get("/{hash}/possible-actions",
           summary="Get possible actions for certificate",
           description="Nhận các hành động có thể thực hiện được cho một chứng chỉ")
async def get_certificate_possible_actions(
    hash: str,
    client=Depends(get_xroad_client)
):
    """
    Get possible actions that can be performed on a certificate
    
    Parameters:
        - hash: Hash of the certificate
    
    Returns:
        List of possible actions for the certificate
        
    Example response:
        [
            "DELETE"
        ]
    """
    result = await client.get(f"/token-certificates/{hash}/possible-actions")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to get possible actions for certificate {hash}")
        )
    
    return result["data"]

@router.put("/{hash}/register",
           summary="Register certificate",
           description="Đăng ký chứng chỉ")
async def register_certificate(
    hash: str,
    registration_data: Dict[str, str],
    client=Depends(get_xroad_client)
):
    """
    Register certificate
    
    Parameters:
        - hash: Hash of the certificate to register
        - registration_data: JSON object with registration information
    
    Request body example:
        {
            "address": "127.0.0.1"
        }
    
    Returns:
        Registration result
    """
    result = await client.put(f"/token-certificates/{hash}/register", data=registration_data)
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to register certificate {hash}")
        )
    
    return {"message": f"Certificate {hash} registered successfully"}

@router.put("/{hash}/unregister",
           summary="Unregister certificate",
           description="Hủy đăng ký chứng chỉ xác thực")
async def unregister_certificate(
    hash: str,
    client=Depends(get_xroad_client)
):
    """
    Unregister authentication certificate
    
    Parameters:
        - hash: Hash of the certificate to unregister
    
    Returns:
        Unregistration result
    """
    result = await client.put(f"/token-certificates/{hash}/unregister")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to unregister certificate {hash}")
        )
    
    return {"message": f"Certificate {hash} unregistered successfully"}

@router.put("/{hash}/mark-for-deletion",
           summary="Mark certificate for deletion",
           description="Đánh dấu chứng chỉ xác thực để xóa")
async def mark_certificate_for_deletion(
    hash: str,
    client=Depends(get_xroad_client)
):
    """
    Mark authentication certificate for deletion
    
    Parameters:
        - hash: Hash of the certificate to mark for deletion
    
    Returns:
        Mark for deletion result
    """
    result = await client.put(f"/token-certificates/{hash}/mark-for-deletion")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to mark certificate {hash} for deletion")
        )
    
    return {"message": f"Certificate {hash} marked for deletion successfully"}

# ============== HEALTH CHECK ==============

@router.get("/health",
           summary="Health check for token certificates APIs")
async def token_certificates_health_check(client=Depends(get_xroad_client)):
    """Check if token certificates APIs are accessible"""
    try:
        # Since we can't test a specific certificate without knowing a hash,
        # we'll test by trying to get a non-existent one and check if we get a proper 404
        # This at least verifies the API endpoint is accessible
        result = await client.get("/token-certificates/nonexistent")
        
        # We expect either success (if cert exists) or 404 (which means API is working)
        api_accessible = result.get("status_code", 500) in [200, 404]
        
        return {
            "status": "healthy" if api_accessible else "unhealthy",
            "token_certificates_api_accessible": api_accessible,
            "response_time": "OK",
            "note": "Health check performed by testing API endpoint accessibility"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "token_certificates_api_accessible": False,
            "error": str(e)
        }