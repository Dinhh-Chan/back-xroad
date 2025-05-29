# app/api/v1/configuration.py
from fastapi import APIRouter, HTTPException, Query, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import Optional, List, Dict, Any
import io
from app.core.config import settings
from app.utils.xroad_client import xroad_client, create_xroad_client
from app.schemas.x_road_config import XRoadConfigParams, XRoadEnvironment

router = APIRouter(prefix="/configuration", tags=["X-Road Central Server - Configuration"])

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

# ============== CONFIGURATION SOURCE ANCHOR APIs ==============

@router.get("/sources/{configuration_type}/anchor",
           summary="Get configuration source anchor",
           description="Có thể xem 'anchor' của một nguồn cấu hình cụ thể")
async def get_configuration_source_anchor(
    configuration_type: str,
    client=Depends(get_xroad_client)
):
    """
    View anchor of a specific configuration source
    
    Parameters:
        - configuration_type: Type of configuration source (INTERNAL, EXTERNAL)
    
    Returns:
        Anchor information with timestamps and hash
        
    Example response:
        {
            "anchor": {
                "created_at": "2022-01-20T00:00:00.001Z",
                "updated_at": "2022-01-22T07:30:00.001Z",
                "hash": "42:34:C3:22:55:42:34:C3:22:55:42:34:C3:22:55:42:34:C3:22:55:42:34:C3:22:55:42:34:C3"
            }
        }
    """
    result = await client.get(f"/configuration-sources/{configuration_type}/anchor")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to get anchor for configuration source {configuration_type}")
        )
    return result["data"]

@router.get("/sources/{configuration_type}/anchor/download",
           summary="Download configuration source anchor",
           description="Có thể tải xuống thông tin 'anchor' của một nguồn cấu hình cụ thể")
async def download_configuration_source_anchor(
    configuration_type: str,
    client=Depends(get_xroad_client)
):
    """
    Download anchor information of a specific configuration source
    
    Parameters:
        - configuration_type: Type of configuration source (INTERNAL, EXTERNAL)
    
    Returns:
        Binary file stream for anchor download
    """
    result = await client.get(f"/configuration-sources/{configuration_type}/anchor/download")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to download anchor for configuration source {configuration_type}")
        )
    
    # Extract file content and content type
    content = result["data"]
    content_type = result.get("content_type", "application/octet-stream")
    
    # Return as streaming response for file download
    return StreamingResponse(
        io.BytesIO(content),
        media_type=content_type,
        headers={
            "Content-Disposition": f"attachment; filename={configuration_type}_anchor.xml",
            "Content-Length": str(len(content))
        }
    )

@router.put("/sources/{configuration_type}/anchor/re-create",
           summary="Re-create configuration source anchor",
           description="Có thể tạo lại thông tin 'anchor' cho một nguồn cấu hình cụ thể")
async def recreate_configuration_source_anchor(
    configuration_type: str,
    client=Depends(get_xroad_client)
):
    """
    Re-create anchor information for a specific configuration source
    
    Parameters:
        - configuration_type: Type of configuration source (INTERNAL, EXTERNAL)
    
    Returns:
        New anchor information with updated timestamps and hash
        
    Example response:
        {
            "created_at": "2022-01-20T00:00:00.001Z",
            "updated_at": "2022-01-22T07:30:00.001Z",
            "hash": "42:34:C3:22:55:42:34:C3:22:55:42:34:C3:22:55:42:34:C3:22:55:42:34:C3:22:55:42:34:C3"
        }
    """
    result = await client.put(f"/configuration-sources/{configuration_type}/anchor/re-create")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to re-create anchor for configuration source {configuration_type}")
        )
    return result["data"]

# ============== CONFIGURATION PARTS APIs ==============

@router.get("/sources/{configuration_type}/configuration-parts",
           summary="Get configuration parts",
           description="Có thể xem các phần cấu hình của một nguồn cấu hình cụ thể")
async def get_configuration_parts(
    configuration_type: str,
    client=Depends(get_xroad_client)
):
    """
    View configuration parts of a specific configuration source
    
    Parameters:
        - configuration_type: Type of configuration source (INTERNAL, EXTERNAL)
    
    Returns:
        List of configuration parts with metadata
        
    Example response:
        [
            {
                "content_identifier": "SHARED-PARAMETERS",
                "file_name": "shared-params.xml",
                "optional": true,
                "file_updated_at": "2022-01-12T00:00:00.001Z",
                "version": 3
            }
        ]
    """
    result = await client.get(f"/configuration-sources/{configuration_type}/configuration-parts")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to get configuration parts for {configuration_type}")
        )
    return result["data"]

@router.post("/sources/{configuration_type}/configuration-parts",
            summary="Upload configuration part file",
            description="Có thể tải lên tệp phần cấu hình bổ sung")
async def upload_configuration_part(
    configuration_type: str,
    file: UploadFile = File(..., description="Configuration part file"),
    client=Depends(get_xroad_client)
):
    """
    Upload additional configuration part file
    
    Parameters:
        - configuration_type: Type of configuration source (INTERNAL, EXTERNAL)
        - file: Configuration part file to upload
    
    Returns:
        Upload result information
    """
    # Read file content
    file_content = await file.read()
    
    # Prepare multipart form data
    files = {"file": (file.filename, file_content, file.content_type or "application/xml")}
    
    result = await client.post(f"/configuration-sources/{configuration_type}/configuration-parts", files=files)
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to upload configuration part for {configuration_type}")
        )
    return result["data"]

@router.get("/sources/{configuration_type}/configuration-parts/{content_identifier}/{version}/download",
           summary="Download configuration part file",
           description="Có thể tải xuống một tệp phần cấu hình cụ thể")
async def download_configuration_part(
    configuration_type: str,
    content_identifier: str,
    version: int,
    client=Depends(get_xroad_client)
):
    """
    Download specific configuration part file
    
    Parameters:
        - configuration_type: Type of configuration source (INTERNAL, EXTERNAL)
        - content_identifier: Content identifier of the configuration part
        - version: Version number of the configuration part
    
    Returns:
        Binary file stream for configuration part download
    """
    result = await client.get(f"/configuration-sources/{configuration_type}/configuration-parts/{content_identifier}/{version}/download")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to download configuration part {content_identifier} version {version}")
        )
    
    # Extract file content and content type
    content = result["data"]
    content_type = result.get("content_type", "application/xml")
    
    # Return as streaming response for file download
    return StreamingResponse(
        io.BytesIO(content),
        media_type=content_type,
        headers={
            "Content-Disposition": f"attachment; filename={content_identifier}_v{version}.xml",
            "Content-Length": str(len(content))
        }
    )

# ============== GLOBAL CONFIGURATION SIGNING KEYS APIs ==============

@router.post("/sources/{configuration_type}/signing-keys",
            summary="Add signing key",
            description="Thêm khóa ký cấu hình cho nguồn cấu hình và mã thông báo đã chọn")
async def add_signing_key(
    configuration_type: str,
    key_data: Dict[str, str],
    client=Depends(get_xroad_client)
):
    """
    Add signing key for configuration source and selected token
    
    Parameters:
        - configuration_type: Type of configuration source (INTERNAL, EXTERNAL)
        - key_data: JSON object with key label and token ID
    
    Request body example:
        {
            "key_label": "string",
            "token_id": "0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF"
        }
    
    Returns:
        Created signing key information
        
    Example response:
        {
            "active": true,
            "available": true,
            "created_at": "2022-01-12T00:00:00.001Z",
            "id": "123",
            "key_hash": "0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF",
            "token_id": "0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF",
            "label": {
                "label": "string"
            },
            "possible_actions": ["DELETE"],
            "source_type": "INTERNAL"
        }
    """
    result = await client.post(f"/configuration-sources/{configuration_type}/signing-keys", data=key_data)
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to add signing key for {configuration_type}")
        )
    return result["data"]

@router.delete("/signing-keys/{sign_key_id}",
              summary="Delete signing key",
              description="Xóa khóa ký cấu hình")
async def delete_signing_key(
    sign_key_id: str,
    client=Depends(get_xroad_client)
):
    """
    Delete configuration signing key
    
    Parameters:
        - sign_key_id: ID of the signing key to delete
    
    Returns:
        Confirmation message
    """
    result = await client.delete(f"/signing-keys/{sign_key_id}")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to delete signing key {sign_key_id}")
        )
    
    return {"message": f"Signing key {sign_key_id} deleted successfully"}

@router.put("/signing-keys/{sign_key_id}/activate",
           summary="Activate signing key",
           description="Kích hoạt khóa ký cấu hình")
async def activate_signing_key(
    sign_key_id: str,
    client=Depends(get_xroad_client)
):
    """
    Activate configuration signing key
    
    Parameters:
        - sign_key_id: ID of the signing key to activate
    
    Returns:
        Activation result
    """
    result = await client.put(f"/signing-keys/{sign_key_id}/activate")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to activate signing key {sign_key_id}")
        )
    
    return {"message": f"Signing key {sign_key_id} activated successfully"}

# ============== HEALTH CHECK ==============

@router.get("/health",
           summary="Health check for configuration APIs")
async def configuration_health_check(client=Depends(get_xroad_client)):
    """Check if configuration APIs are accessible"""
    try:
        # Test get configuration parts endpoint for INTERNAL source
        result = await client.get("/configuration-sources/INTERNAL/configuration-parts")
        
        return {
            "status": "healthy" if result.get("status_code", 200) < 400 else "unhealthy",
            "configuration_api_accessible": result.get("status_code", 200) < 400,
            "response_time": "OK"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "configuration_api_accessible": False,
            "error": str(e)
        }