# app/api/v1/security_server_keys.py
from fastapi import APIRouter, HTTPException, Query, Depends, Path
from fastapi.responses import StreamingResponse
from typing import Optional, List, Dict, Any
import io
from app.core.config import settings
from app.utils.xroad_client_ss import xroad_client, create_xroad_client
from app.schemas.x_road_config import XRoadConfigParams, XRoadEnvironment

router = APIRouter(prefix="/security-server-keys", tags=["Security Server - Key Management"])

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

# ============== SECURITY SERVER KEYS APIs ==============

@router.get("/{key_id}",
           summary="Get key information",
           description="Lấy thông tin cho khóa đã chọn trong token")
async def get_key_info(
    key_id: str = Path(..., description="ID của khóa cần lấy thông tin"),
    client=Depends(get_xroad_client)
):
    """
    Lấy thông tin chi tiết cho khóa đã chọn
    
    Parameters:
        - key_id: ID của khóa (hex string)
    
    Returns:
        Thông tin chi tiết của khóa bao gồm certificates và CSRs
        
    Example response:
        {
            "id": "0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF",
            "name": "friendly name",
            "label": "key label",
            "certificates": [...],
            "certificate_signing_requests": [...],
            "usage": "AUTHENTICATION",
            "available": true,
            "saved_to_configuration": true,
            "possible_actions": ["DELETE"]
        }
    """
    result = await client.get(f"/keys/{key_id}")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to get key information for {key_id}")
        )
    return result["data"]

@router.patch("/{key_id}",
             summary="Update key information",
             description="Cập nhật thông tin khóa")
async def update_key_info(
    key_data: Dict[str, Any],
    key_id: str = Path(..., description="ID của khóa cần cập nhật"),
    client=Depends(get_xroad_client)
):
    """
    Cập nhật thông tin khóa (hiện tại chỉ hỗ trợ cập nhật tên)
    
    Parameters:
        - key_id: ID của khóa
        - key_data: Thông tin cập nhật cho khóa
    
    Returns:
        Thông tin khóa đã được cập nhật
        
    Example request:
        {
            "name": "my-key-0"
        }
    """
    result = await client.patch(f"/keys/{key_id}", data=key_data)
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to update key {key_id}")
        )
    return result["data"]

@router.delete("/{key_id}",
              summary="Delete key",
              description="Xóa khóa")
async def delete_key(
    key_id: str = Path(..., description="ID của khóa cần xóa"),
    client=Depends(get_xroad_client)
):
    """
    Xóa khóa khỏi token
    
    Parameters:
        - key_id: ID của khóa cần xóa
    
    Returns:
        Confirmation message
    """
    result = await client.delete(f"/keys/{key_id}")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to delete key {key_id}")
        )
    
    return {"message": f"Key {key_id} deleted successfully"}

@router.get("/{key_id}/possible-actions",
           summary="Get possible actions for key",
           description="Lấy các hành động có thể thực hiện cho một khóa")
async def get_key_possible_actions(
    key_id: str = Path(..., description="ID của khóa"),
    client=Depends(get_xroad_client)
):
    """
    Lấy danh sách các hành động có thể thực hiện trên khóa
    
    Parameters:
        - key_id: ID của khóa
    
    Returns:
        Danh sách các hành động có thể thực hiện
        
    Example response:
        ["DELETE"]
    """
    result = await client.get(f"/keys/{key_id}/possible-actions")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to get possible actions for key {key_id}")
        )
    return result["data"]

# ============== CERTIFICATE SIGNING REQUEST (CSR) APIs ==============

@router.post("/{key_id}/csrs",
            summary="Create CSR for key",
            description="Tạo CSR cho khóa đã chọn")
async def create_csr_for_key(
    csr_data: Dict[str, Any],
    key_id: str = Path(..., description="ID của khóa"),
    client=Depends(get_xroad_client)
):
    """
    Tạo Certificate Signing Request cho khóa đã chọn
    
    Parameters:
        - key_id: ID của khóa
        - csr_data: Thông tin để tạo CSR
    
    Returns:
        Thông tin CSR đã được tạo
        
    Example request:
        {
            "key_usage_type": "SIGNING",
            "ca_name": "Customized Test CA CN",
            "csr_format": "DER",
            "member_id": "CS:NIIS:1234",
            "subject_field_values": {
                "CN": "something.niis.org",
                "C": "FI",
                "O": "NIIS",
                "serialNumber": "CS/SS1/NIIS"
            }
        }
    """
    result = await client.post(f"/keys/{key_id}/csrs", data=csr_data)
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to create CSR for key {key_id}")
        )
    return result["data"]

@router.get("/{key_id}/csrs/{csr_id}",
           summary="Download CSR binary",
           description="Tải xuống CSR nhị phân")
async def download_csr(
    key_id: str = Path(..., description="ID của khóa"),
    csr_id: str = Path(..., description="ID của CSR"),
    client=Depends(get_xroad_client)
):
    """
    Tải xuống Certificate Signing Request dưới dạng binary
    
    Parameters:
        - key_id: ID của khóa
        - csr_id: ID của CSR
    
    Returns:
        Binary file stream cho CSR download
    """
    result = await client.get(f"/keys/{key_id}/csrs/{csr_id}")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to download CSR {csr_id} for key {key_id}")
        )
    
    # Extract file content and content type
    content = result["data"]
    content_type = result.get("content_type", "application/octet-stream")
    
    # Return as streaming response for file download
    return StreamingResponse(
        io.BytesIO(content),
        media_type=content_type,
        headers={
            "Content-Disposition": f"attachment; filename=csr_{csr_id}.csr",
            "Content-Length": str(len(content))
        }
    )

@router.delete("/{key_id}/csrs/{csr_id}",
              summary="Delete CSR from key",
              description="Xóa CSR từ khóa đã chọn")
async def delete_csr(
    key_id: str = Path(..., description="ID của khóa"),
    csr_id: str = Path(..., description="ID của CSR cần xóa"),
    client=Depends(get_xroad_client)
):
    """
    Xóa Certificate Signing Request khỏi khóa
    
    Parameters:
        - key_id: ID của khóa
        - csr_id: ID của CSR cần xóa
    
    Returns:
        Confirmation message
    """
    result = await client.delete(f"/keys/{key_id}/csrs/{csr_id}")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to delete CSR {csr_id} from key {key_id}")
        )
    
    return {"message": f"CSR {csr_id} deleted successfully from key {key_id}"}

@router.get("/{key_id}/csrs/{csr_id}/possible-actions",
           summary="Get possible actions for CSR",
           description="Lấy các hành động có thể thực hiện cho một CSR")
async def get_csr_possible_actions(
    key_id: str = Path(..., description="ID của khóa"),
    csr_id: str = Path(..., description="ID của CSR"),
    client=Depends(get_xroad_client)
):
    """
    Lấy danh sách các hành động có thể thực hiện trên CSR
    
    Parameters:
        - key_id: ID của khóa
        - csr_id: ID của CSR
    
    Returns:
        Danh sách các hành động có thể thực hiện
        
    Example response:
        ["DELETE"]
    """
    result = await client.get(f"/keys/{key_id}/csrs/{csr_id}/possible-actions")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to get possible actions for CSR {csr_id} of key {key_id}")
        )
    return result["data"]

# ============== HEALTH CHECK ==============

@router.get("/health",
           summary="Health check for security server keys APIs")
async def security_server_keys_health_check(client=Depends(get_xroad_client)):
    """Check if security server keys APIs are accessible"""
    try:
        # Test endpoint by checking if we can access keys API
        # Note: This might fail if no keys exist, but that's expected
        result = await client.get("/keys")
        
        return {
            "status": "healthy" if result.get("status_code", 200) < 500 else "unhealthy",
            "security_server_keys_api_accessible": result.get("status_code", 200) < 500,
            "response_time": "OK"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "security_server_keys_api_accessible": False,
            "error": str(e)
        }