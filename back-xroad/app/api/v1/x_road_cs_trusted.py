# app/api/v1/trusted_anchors.py
from fastapi import APIRouter, HTTPException, Query, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import Optional, List, Dict, Any
import io
from app.core.config import settings
from app.utils.xroad_client_cs import xroad_client, create_xroad_client
from app.schemas.x_road_config import XRoadConfigParams, XRoadEnvironment

router = APIRouter(prefix="/trusted-anchors", tags=["X-Road Central Server - Trusted Anchors"])

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

# ============== TRUSTED ANCHORS APIs ==============

@router.get("/",
           summary="Get trusted anchors",
           description="Xem danh sách các trusted anchor")
async def get_trusted_anchors(client=Depends(get_xroad_client)):
    """
    View list of trusted anchors
    
    Returns:
        List of trusted anchors with instance identifier, generation time and hash
        
    Example response:
        [
            {
                "instance_identifier": "CS",
                "generated_at": "2023-03-17T00:00:00.001Z",
                "hash": "42:34:C3:22:55:42:34:C3:22:55:42:34:C3:22:55:42:34:C3:22:55:42:34:C3:22:55:42:34:C3"
            }
        ]
    """
    result = await client.get("/trusted-anchors")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to get trusted anchors list")
        )
    return result["data"]

@router.post("/",
            summary="Upload trusted anchor",
            description="Tải lên một trusted anchor mới")
async def upload_trusted_anchor(
    anchor: UploadFile = File(..., description="Trusted anchor file"),
    client=Depends(get_xroad_client)
):
    """
    Upload new trusted anchor
    
    Parameters:
        - anchor: Trusted anchor file (multipart/form-data)
    
    Returns:
        Uploaded trusted anchor information
        
    Example response:
        {
            "instance_identifier": "CS",
            "generated_at": "2023-03-17T00:00:00.001Z",
            "hash": "42:34:C3:22:55:42:34:C3:22:55:42:34:C3:22:55:42:34:C3:22:55:42:34:C3:22:55:42:34:C3"
        }
    """
    # Read anchor file content
    anchor_content = await anchor.read()
    
    # Prepare multipart form data
    files = {"anchor": (anchor.filename, anchor_content, anchor.content_type or "application/xml")}
    
    result = await client.post("/trusted-anchors", files=files)
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to upload trusted anchor")
        )
    return result["data"]

@router.post("/preview",
            summary="Preview trusted anchor",
            description="Tải lên một trusted anchor để xem trước")
async def preview_trusted_anchor(
    anchor: UploadFile = File(..., description="Trusted anchor file for preview"),
    client=Depends(get_xroad_client)
):
    """
    Upload trusted anchor for preview
    
    Parameters:
        - anchor: Trusted anchor file to preview (multipart/form-data)
    
    Returns:
        Preview information of the trusted anchor
        
    Example response:
        {
            "instance_identifier": "CS",
            "generated_at": "2023-03-17T00:00:00.001Z",
            "hash": "42:34:C3:22:55:42:34:C3:22:55:42:34:C3:22:55:42:34:C3:22:55:42:34:C3:22:55:42:34:C3"
        }
    """
    # Read anchor file content
    anchor_content = await anchor.read()
    
    # Prepare multipart form data
    files = {"anchor": (anchor.filename, anchor_content, anchor.content_type or "application/xml")}
    
    result = await client.post("/trusted-anchors/preview", files=files)
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to preview trusted anchor")
        )
    return result["data"]

@router.delete("/{hash}",
              summary="Delete trusted anchor",
              description="Xóa một trusted anchor")
async def delete_trusted_anchor(
    hash: str,
    client=Depends(get_xroad_client)
):
    """
    Delete a trusted anchor
    
    Parameters:
        - hash: Hash of the trusted anchor to delete
    
    Returns:
        Confirmation message
    """
    result = await client.delete(f"/trusted-anchors/{hash}")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to delete trusted anchor {hash}")
        )
    
    return {"message": f"Trusted anchor {hash} deleted successfully"}

@router.get("/{hash}/download",
           summary="Download trusted anchor",
           description="Tải xuống một trusted anchor")
async def download_trusted_anchor(
    hash: str,
    client=Depends(get_xroad_client)
):
    """
    Download a trusted anchor
    
    Parameters:
        - hash: Hash of the trusted anchor to download
    
    Returns:
        Binary file stream for trusted anchor download
    """
    result = await client.get(f"/trusted-anchors/{hash}/download")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to download trusted anchor {hash}")
        )
    
    # Extract file content and content type
    content = result["data"]
    content_type = result.get("content_type", "application/xml")
    
    # Return as streaming response for file download
    return StreamingResponse(
        io.BytesIO(content),
        media_type=content_type,
        headers={
            "Content-Disposition": f"attachment; filename=trusted_anchor_{hash[:8]}.xml",
            "Content-Length": str(len(content))
        }
    )

# ============== HEALTH CHECK ==============

@router.get("/health",
           summary="Health check for trusted anchors APIs")
async def trusted_anchors_health_check(client=Depends(get_xroad_client)):
    """Check if trusted anchors APIs are accessible"""
    try:
        # Test get trusted anchors endpoint
        result = await client.get("/trusted-anchors")
        
        return {
            "status": "healthy" if result.get("status_code", 200) < 400 else "unhealthy",
            "trusted_anchors_api_accessible": result.get("status_code", 200) < 400,
            "response_time": "OK"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "trusted_anchors_api_accessible": False,
            "error": str(e)
        }