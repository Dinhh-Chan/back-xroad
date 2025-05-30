# app/api/v1/security_server_backups.py
from fastapi import APIRouter, HTTPException, Query, Depends, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from typing import Optional, List, Dict, Any
import io
from app.core.config import settings
from app.utils.xroad_client_ss import xroad_client, create_xroad_client
from app.schemas.x_road_config import XRoadConfigParams, XRoadEnvironment

router = APIRouter(prefix="/security-server-backups", tags=["Security Server - Backup Management"])

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

# ============== SECURITY SERVER BACKUP APIs ==============

@router.get("/",
           summary="Get security server backups",
           description="Xem danh sách các bản sao lưu của security server")
async def get_security_server_backups(client=Depends(get_xroad_client)):
    """
    View list of security server backups
    
    Returns:
        List of security server backups with filename and creation timestamp
        
    Example response:
        [
            {
                "filename": "configuration_backup_20181224.tar",
                "created_at": "2018-12-15T00:00:00.001Z"
            }
        ]
    """
    result = await client.get("/backups")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to get security server backups")
        )
    return result["data"]

@router.post("/",
            summary="Create security server backup",
            description="Thêm bản sao lưu mới cho security server")
async def create_security_server_backup(client=Depends(get_xroad_client)):
    """
    Add new backup for security server
    
    Returns:
        Created backup information with filename and creation timestamp
        
    Example response:
        {
            "filename": "configuration_backup_20181224.tar",
            "created_at": "2018-12-15T00:00:00.001Z"
        }
    """
    result = await client.post("/backups")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to create security server backup")
        )
    return result["data"]

@router.post("/ext",
            summary="Add external security server backup",
            description="Thêm bản sao lưu máy chủ bảo mật vào hệ thống")
async def add_external_security_server_backup(client=Depends(get_xroad_client)):
    """
    Add security server backup to system
    
    Returns:
        Added backup information with local configuration presence status
        
    Example response:
        {
            "filename": "configuration_backup_20181224.tar",
            "created_at": "2018-12-15T00:00:00.001Z",
            "local_conf_present": true
        }
    """
    result = await client.post("/backups/ext")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to add external security server backup")
        )
    return result["data"]

@router.post("/upload",
            summary="Upload security server backup",
            description="Tải lên một bản sao lưu mới cho security server")
async def upload_security_server_backup(
    file: UploadFile = File(..., description="Backup file to upload"),
    ignore_warnings: bool = Query(False, description="Ignore warnings if file already exists"),
    client=Depends(get_xroad_client)
):
    """
    Upload new backup for security server
    
    Parameters:
        - file: Backup file to upload (multipart/form-data)
        - ignore_warnings: Ignore warnings if file already exists (query parameter)
    
    Returns:
        Uploaded backup information
        
    Example response:
        {
            "filename": "configuration_backup_20181224.tar",
            "created_at": "2018-12-15T00:00:00.001Z"
        }
    """
    # Read file content
    file_content = await file.read()
    
    # Prepare multipart form data
    files = {"file": (file.filename, file_content, file.content_type or "application/octet-stream")}
    
    # Add ignore_warnings as query parameter
    endpoint = f"/backups/upload?ignore_warnings={str(ignore_warnings).lower()}"
    
    result = await client.post(endpoint, files=files)
    
    # Handle warnings (status 400 with warnings_detected)
    if result.get("status_code") == 400 and "warnings" in result.get("data", {}):
        raise HTTPException(
            status_code=400,
            detail=result["data"]
        )
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to upload security server backup")
        )
    
    return result["data"]

@router.delete("/{filename}",
              summary="Delete security server backup",
              description="Xóa một bản sao lưu của security server")
async def delete_security_server_backup(
    filename: str,
    client=Depends(get_xroad_client)
):
    """
    Delete a security server backup
    
    Parameters:
        - filename: Name of the backup file to delete
    
    Returns:
        Confirmation message
    """
    result = await client.delete(f"/backups/{filename}")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to delete security server backup {filename}")
        )
    
    return {"message": f"Security server backup {filename} deleted successfully"}

@router.get("/{filename}/download",
           summary="Download security server backup",
           description="Tải về bản sao lưu của security server")
async def download_security_server_backup(
    filename: str,
    client=Depends(get_xroad_client)
):
    """
    Download security server backup
    
    Parameters:
        - filename: Name of the backup file to download
    
    Returns:
        Binary file stream for backup download
    """
    result = await client.get(f"/backups/{filename}/download")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to download security server backup {filename}")
        )
    
    # Extract file content and content type
    content = result["data"]
    content_type = result.get("content_type", "application/octet-stream")
    
    # Return as streaming response for file download
    return StreamingResponse(
        io.BytesIO(content),
        media_type=content_type,
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Length": str(len(content))
        }
    )

@router.put("/{filename}/restore",
           summary="Restore from security server backup",
           description="Khôi phục cấu hình security server từ bản sao lưu")
async def restore_security_server_backup(
    filename: str,
    client=Depends(get_xroad_client)
):
    """
    Restore security server configuration from backup
    
    Parameters:
        - filename: Name of the backup file to restore from
    
    Returns:
        Restore operation result
        
    Example response:
        {
            "hsm_tokens_logged_out": false
        }
    """
    result = await client.put(f"/backups/{filename}/restore")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to restore security server from backup {filename}")
        )
    
    return result["data"]

# ============== HEALTH CHECK ==============

@router.get("/health",
           summary="Health check for security server backup APIs")
async def security_server_backups_health_check(client=Depends(get_xroad_client)):
    """Check if security server backup APIs are accessible"""
    try:
        # Test get security server backups endpoint
        result = await client.get("/backups")
        
        return {
            "status": "healthy" if result.get("status_code", 200) < 400 else "unhealthy",
            "security_server_backups_api_accessible": result.get("status_code", 200) < 400,
            "response_time": "OK"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "security_server_backups_api_accessible": False,
            "error": str(e)
        }