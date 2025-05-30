# app/api/v1/x_road_cs.py
from fastapi import APIRouter, HTTPException, UploadFile, File, Query, Form
from fastapi.responses import StreamingResponse
from typing import Optional, Dict, Any, List
import io
from app.core.config import settings
from app.utils.xroad_client_cs import xroad_client, create_xroad_client

router = APIRouter(prefix="/xroad-cs", tags=["X-Road Central Server Backup"])

# Helper function to get XRoad client
def get_xroad_client(custom_base_url: Optional[str] = None,
                     custom_api_key: Optional[str] = None,
                     env_prefix: Optional[str] = None):
    """Get XRoad client with configuration priority"""
    if env_prefix:
        config = settings.get_xroad_config(env_prefix)
        return create_xroad_client(
            base_url=custom_base_url or config["base_url"],
            api_key=custom_api_key or config["api_key"],
            timeout=config["timeout"]
        )
    
    if custom_base_url or custom_api_key:
        return create_xroad_client(
            base_url=custom_base_url,
            api_key=custom_api_key
        )
    
    return xroad_client

# ============== BACKUP MANAGEMENT APIs ==============

@router.get("/backups", 
           summary="Get list of backups",
           description="Xem các bản sao lưu cho máy chủ trung tâm",
           response_description="Danh sách các file backup")
async def get_backups(env_prefix: Optional[str] = Query(None, description="Environment prefix (dev, prod, test)"),
                     custom_base_url: Optional[str] = Query(None, description="Custom X-Road base URL"),
                     custom_api_key: Optional[str] = Query(None, description="Custom X-Road API key")):
    """
    Get list of backups from X-Road Central Server
    
    Returns:
        List of backup files with filename
        
    Example response:
        [
            {
                "filename": "configuration_backup_20181224.tar"
            }
        ]
    """
    client = get_xroad_client(custom_base_url, custom_api_key, env_prefix)
    result = await client.get("/backups")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to get backups from X-Road Central Server")
        )
    return result["data"]

@router.post("/backups",
            summary="Create new backup", 
            description="Tạo bản sao lưu máy chủ trung tâm mới",
            response_description="Thông tin file backup được tạo")
async def create_backup(env_prefix: Optional[str] = Query(None, description="Environment prefix (dev, prod, test)"),
                       custom_base_url: Optional[str] = Query(None, description="Custom X-Road base URL"),
                       custom_api_key: Optional[str] = Query(None, description="Custom X-Road API key")):
    """
    Create new backup on X-Road Central Server
    
    Returns:
        Information about the created backup file
        
    Example response:
        {
            "filename": "configuration_backup_20181224.tar"
        }
    """
    client = get_xroad_client(custom_base_url, custom_api_key, env_prefix)
    result = await client.post("/backups")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to create backup on X-Road Central Server")
        )
    return result["data"]

@router.post("/backups/upload",
            summary="Upload backup file",
            description="Tải lên file backup. Có thể ghi đè nếu ignore_warnings = true",
            response_description="Thông tin file backup đã upload")
async def upload_backup(file: UploadFile = File(..., description="File backup cần tải lên (.tar)"),
                       ignore_warnings: bool = Form(False, description="Bỏ qua cảnh báo nếu file đã tồn tại"),
                       env_prefix: Optional[str] = Query(None, description="Environment prefix (dev, prod, test)"),
                       custom_base_url: Optional[str] = Query(None, description="Custom X-Road base URL"),
                       custom_api_key: Optional[str] = Query(None, description="Custom X-Road API key")):
    """
    Upload backup file to X-Road Central Server
    
    Parameters:
        - file: Backup archive file (multipart/form-data)
        - ignore_warnings: Boolean, default false. If true, warnings can be ignored and file will be overwritten
    
    Returns:
        Information about uploaded backup file
        
    Success response:
        {
            "filename": "configuration_backup_20181224.tar"
        }
        
    Warning response (when file exists and ignore_warnings=false):
        {
            "error": {
                "code": "warnings_detected"
            },
            "status": 400,
            "warnings": [
                {
                    "code": "warning_file_already_exists",
                    "metadata": ["conf_backup_20201006-094932.tar"]
                }
            ]
        }
    """
    client = get_xroad_client(custom_base_url, custom_api_key, env_prefix)
    
    # Đọc file content
    file_content = await file.read()
    
    # Prepare multipart form data
    files = {"file": (file.filename, file_content, file.content_type or "application/octet-stream")}
    
    # Add ignore_warnings as query parameter trong URL
    endpoint = f"/backups/upload?ignore_warnings={str(ignore_warnings).lower()}"
    
    result = await client.post(endpoint, files=files)
    
    # Handle warnings (status 400 with warnings_detected)
    if result.get("status_code") == 400 and "warnings" in result.get("data", {}):
        # Return the warning response as-is for client to handle
        raise HTTPException(
            status_code=400,
            detail=result["data"]
        )
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to upload backup to X-Road Central Server")
        )
    
    return result["data"]

@router.delete("/backups/{filename}",
              summary="Delete backup file",
              description="Xóa file backup trên server bằng cách cung cấp tên file",
              response_description="Confirmation message")
async def delete_backup(filename: str,
                       env_prefix: Optional[str] = Query(None, description="Environment prefix (dev, prod, test)"),
                       custom_base_url: Optional[str] = Query(None, description="Custom X-Road base URL"),
                       custom_api_key: Optional[str] = Query(None, description="Custom X-Road API key")):
    """
    Delete backup file from X-Road Central Server
    
    Parameters:
        - filename: Name of the backup file to delete
    
    Returns:
        Confirmation message
    """
    client = get_xroad_client(custom_base_url, custom_api_key, env_prefix)
    result = await client.delete(f"/backups/{filename}")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to delete backup file '{filename}' from X-Road Central Server")
        )
    
    return {"message": f"Backup file '{filename}' deleted successfully"}

@router.get("/backups/{filename}/download",
           summary="Download backup file",
           description="Tải xuống file backup từ server bằng cách cung cấp tên file",
           response_description="Binary file download")
async def download_backup(filename: str,
                         env_prefix: Optional[str] = Query(None, description="Environment prefix (dev, prod, test)"),
                         custom_base_url: Optional[str] = Query(None, description="Custom X-Road base URL"),
                         custom_api_key: Optional[str] = Query(None, description="Custom X-Road API key")):
    """
    Download backup file from X-Road Central Server
    
    Parameters:
        - filename: Name of the backup file to download
    
    Returns:
        Binary file stream for download
    """
    client = get_xroad_client(custom_base_url, custom_api_key, env_prefix)
    result = await client.get(f"/backups/{filename}/download")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to download backup file '{filename}' from X-Road Central Server")
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

@router.put("/backups/{filename}/restore",
           summary="Restore from backup",
           description="Phục hồi cấu hình server từ bản sao lưu",
           response_description="Restore result information")
async def restore_backup(filename: str,
                        env_prefix: Optional[str] = Query(None, description="Environment prefix (dev, prod, test)"),
                        custom_base_url: Optional[str] = Query(None, description="Custom X-Road base URL"),
                        custom_api_key: Optional[str] = Query(None, description="Custom X-Road API key")):
    """
    Restore X-Road Central Server configuration from backup
    
    Parameters:
        - filename: Name of the backup file to restore from
    
    Returns:
        Restore operation result
        
    Success response:
        {
            "hsm_tokens_logged_out": false
        }
        
    Note: 
        If restore fails, response will contain metadata with error script output information
    """
    client = get_xroad_client(custom_base_url, custom_api_key, env_prefix)
    result = await client.put(f"/backups/{filename}/restore")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to restore from backup file '{filename}' on X-Road Central Server")
        )
    
    return result["data"]

# ============== HEALTH CHECK cho Backup APIs ==============

@router.get("/health/backup",
           summary="Health check for backup functionality",
           description="Kiểm tra tình trạng hoạt động của các API backup")
async def backup_health_check(env_prefix: Optional[str] = Query(None),
                             custom_base_url: Optional[str] = Query(None),
                             custom_api_key: Optional[str] = Query(None)):
    """Check if backup APIs are accessible"""
    client = get_xroad_client(custom_base_url, custom_api_key, env_prefix)
    
    try:
        # Test get backups endpoint
        result = await client.get("/backups")
        
        return {
            "status": "healthy" if result.get("status_code", 200) < 400 else "unhealthy",
            "backup_api_accessible": result.get("status_code", 200) < 400,
            "response_time": "OK",
            "config": {
                "env_prefix": env_prefix,
                "using_custom_config": bool(custom_base_url or custom_api_key)
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy", 
            "backup_api_accessible": False,
            "error": str(e),
            "config": {
                "env_prefix": env_prefix,
                "using_custom_config": bool(custom_base_url or custom_api_key)
            }
        }