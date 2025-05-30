from fastapi import APIRouter, HTTPException, Query, Depends, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from typing import Optional, List, Dict, Any
import io
from app.core.config import settings
from app.utils.xroad_client_ss import xroad_client, create_xroad_client
from app.schemas.x_road_config import XRoadConfigParams, XRoadEnvironment

router = APIRouter(prefix="/diagnostics", tags=["Security Server - Diagnostics"])

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

# ============== DIAGNOSTICS APIs ==============

@router.get("/globalconf",
           summary="Get global configuration diagnostics",
           description="Xem thông tin chẩn đoán cấu hình toàn cục")
async def get_globalconf_diagnostics(client=Depends(get_xroad_client)):
    """
    View global configuration diagnostic information
    
    Returns:
        Global configuration status with update timestamps
        
    Example response:
        {
            "status_class": "OK",
            "status_code": "SUCCESS",
            "prev_update_at": "2018-12-15T00:00:00.001Z",
            "next_update_at": "2018-12-15T00:00:00.001Z"
        }
    """
    result = await client.get("/diagnostics/globalconf")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to get global configuration diagnostics")
        )
    
    return result["data"]

@router.get("/ocsp-responders",
           summary="Get OCSP responders diagnostics",
           description="Xem thông tin chẩn đoán các phản hồi OCSP")
async def get_ocsp_responders_diagnostics(client=Depends(get_xroad_client)):
    """
    View OCSP responders diagnostic information
    
    Returns:
        OCSP responders status grouped by distinguished name
        
    Example response:
        [
            {
                "distinguished_name": "C=FI, O=X-Road Test, OU=X-Road Test CA OU, CN=X-Road Test CA CN",
                "ocsp_responders": [
                    {
                        "url": "http://dev.xroad.rocks:123",
                        "status_class": "OK",
                        "status_code": "SUCCESS",
                        "prev_update_at": "2018-12-15T00:00:00.001Z",
                        "next_update_at": "2018-12-15T00:00:00.001Z"
                    }
                ]
            }
        ]
    """
    result = await client.get("/diagnostics/ocsp-responders")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to get OCSP responders diagnostics")
        )
    
    return result["data"]

@router.get("/timestamping-services",
           summary="Get timestamping services diagnostics",
           description="Xem thông tin chẩn đoán dịch vụ đóng dấu thời gian")
async def get_timestamping_services_diagnostics(client=Depends(get_xroad_client)):
    """
    View timestamping services diagnostic information
    
    Returns:
        Timestamping services status and diagnostic information
    """
    result = await client.get("/diagnostics/timestamping-services")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to get timestamping services diagnostics")
        )
    
    return result["data"]

@router.get("/addon-status",
           summary="Get addon services diagnostics",
           description="Xem thông tin chẩn đoán dịch vụ bổ trợ")
async def get_addon_status_diagnostics(client=Depends(get_xroad_client)):
    """
    View addon services diagnostic information
    
    Returns:
        Addon services status including message log status
        
    Example response:
        {
            "messagelog_enabled": true
        }
    """
    result = await client.get("/diagnostics/addon-status")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to get addon status diagnostics")
        )
    
    return result["data"]

@router.get("/backup-encryption-status",
           summary="Get backup encryption diagnostics",
           description="Xem thông tin chẩn đoán dịch vụ mã hóa sao lưu")
async def get_backup_encryption_status_diagnostics(client=Depends(get_xroad_client)):
    """
    View backup encryption service diagnostic information
    
    Returns:
        Backup encryption status and available encryption keys
        
    Example response:
        {
            "backup_encryption_status": true,
            "backup_encryption_keys": ["string"]
        }
    """
    result = await client.get("/diagnostics/backup-encryption-status")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to get backup encryption status diagnostics")
        )
    
    return result["data"]

@router.get("/message-log-encryption-status",
           summary="Get message log encryption diagnostics",
           description="Xem thông tin chẩn đoán mã hóa và nhóm nhật ký tin nhắn")
async def get_message_log_encryption_status_diagnostics(client=Depends(get_xroad_client)):
    """
    View message log encryption and grouping diagnostic information
    
    Returns:
        Message log encryption status, grouping rules and member information
        
    Example response:
        {
            "message_log_archive_encryption_status": true,
            "message_log_database_encryption_status": true,
            "message_log_grouping_rule": "string",
            "members": [
                {
                    "member_id": "string",
                    "keys": ["string"],
                    "default_key_used": true
                }
            ]
        }
    """
    result = await client.get("/diagnostics/message-log-encryption-status")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to get message log encryption status diagnostics")
        )
    
    return result["data"]

# ============== COMPREHENSIVE DIAGNOSTICS ==============

@router.get("/all",
           summary="Get all diagnostics information",
           description="Lấy tất cả thông tin chẩn đoán hệ thống")
async def get_all_diagnostics(client=Depends(get_xroad_client)):
    """
    Get comprehensive diagnostics information from all available endpoints
    
    Returns:
        Combined diagnostic information from all services
    """
    try:
        # Collect diagnostics from all endpoints
        diagnostics = {}
        
        # Global configuration
        try:
            globalconf_result = await client.get("/diagnostics/globalconf")
            if globalconf_result.get("status_code", 200) < 400:
                diagnostics["global_configuration"] = globalconf_result["data"]
        except:
            diagnostics["global_configuration"] = {"error": "Failed to retrieve"}
        
        # OCSP responders
        try:
            ocsp_result = await client.get("/diagnostics/ocsp-responders")
            if ocsp_result.get("status_code", 200) < 400:
                diagnostics["ocsp_responders"] = ocsp_result["data"]
        except:
            diagnostics["ocsp_responders"] = {"error": "Failed to retrieve"}
        
        # Timestamping services
        try:
            ts_result = await client.get("/diagnostics/timestamping-services")
            if ts_result.get("status_code", 200) < 400:
                diagnostics["timestamping_services"] = ts_result["data"]
        except:
            diagnostics["timestamping_services"] = {"error": "Failed to retrieve"}
        
        # Addon status
        try:
            addon_result = await client.get("/diagnostics/addon-status")
            if addon_result.get("status_code", 200) < 400:
                diagnostics["addon_status"] = addon_result["data"]
        except:
            diagnostics["addon_status"] = {"error": "Failed to retrieve"}
        
        # Backup encryption
        try:
            backup_result = await client.get("/diagnostics/backup-encryption-status")
            if backup_result.get("status_code", 200) < 400:
                diagnostics["backup_encryption"] = backup_result["data"]
        except:
            diagnostics["backup_encryption"] = {"error": "Failed to retrieve"}
        
        # Message log encryption
        try:
            msglog_result = await client.get("/diagnostics/message-log-encryption-status")
            if msglog_result.get("status_code", 200) < 400:
                diagnostics["message_log_encryption"] = msglog_result["data"]
        except:
            diagnostics["message_log_encryption"] = {"error": "Failed to retrieve"}
        
        return {
            "timestamp": "2024-12-01T12:00:00.000Z",
            "diagnostics": diagnostics
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to collect comprehensive diagnostics: {str(e)}"
        )

# ============== HEALTH CHECK ==============

@router.get("/health",
           summary="Health check for diagnostics APIs")
async def diagnostics_health_check(client=Depends(get_xroad_client)):
    """Check if diagnostics APIs are accessible"""
    try:
        # Test global configuration diagnostics endpoint
        result = await client.get("/diagnostics/globalconf")
        
        return {
            "status": "healthy" if result.get("status_code", 200) < 400 else "unhealthy",
            "diagnostics_api_accessible": result.get("status_code", 200) < 400,
            "response_time": "OK"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "diagnostics_api_accessible": False,
            "error": str(e)
        }