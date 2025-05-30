from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List, Dict, Any
from app.core.config import settings
from app.utils.xroad_client_cs import xroad_client, create_xroad_client
from app.schemas.x_road_config import XRoadConfigParams, XRoadEnvironment

router = APIRouter(prefix="/system", tags=["X-Road Central Server - System"])

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

# ============== SYSTEM APIs ==============

@router.put("/server-address",
           summary="Update central server address",
           description="Cập nhật địa chỉ máy chủ trung tâm")
async def update_server_address(
    address_data: Dict[str, str],
    client=Depends(get_xroad_client)
):
    """
    Update central server address
    
    Parameters:
        - address_data: JSON object with central server address
    
    Request body example:
        {
            "central_server_address": "string"
        }
    
    Returns:
        System status including high availability and initialization status
        
    Example response:
        {
            "high_availability_status": {
                "is_ha_configured": false,
                "node_name": "node_0"
            },
            "initialization_status": {
                "instance_identifier": "FI-TEST",
                "central_server_address": "string",
                "software_token_init_status": "INITIALIZED"
            }
        }
    """
    result = await client.put("/system/server-address", data=address_data)
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to update central server address")
        )
    return result["data"]

@router.get("/status",
           summary="Get system status",
           description="Lấy trạng thái hệ thống")
async def get_system_status(client=Depends(get_xroad_client)):
    """
    Get system status
    
    Returns:
        System status including high availability and initialization information
        
    Example response:
        {
            "high_availability_status": {
                "is_ha_configured": false,
                "node_name": "node_0"
            },
            "initialization_status": {
                "instance_identifier": "FI-TEST",
                "central_server_address": "string",
                "software_token_init_status": "INITIALIZED"
            }
        }
    """
    result = await client.get("/system/status")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to get system status")
        )
    return result["data"]

@router.get("/version",
           summary="Get system version",
           description="Lấy thông tin phiên bản hệ thống")
async def get_system_version(client=Depends(get_xroad_client)):
    """
    Get system version information
    
    Returns:
        System version information
        
    Example response:
        {
            "info": "Security Server version 6.21.0-SNAPSHOT-20190411git32add470"
        }
    """
    result = await client.get("/system/version")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to get system version")
        )
    return result["data"]

@router.get("/high-availability-cluster/status",
           summary="Get high availability cluster status",
           description="Lấy trạng thái của cụm hệ thống có tính khả dụng cao")
async def get_high_availability_cluster_status(client=Depends(get_xroad_client)):
    """
    Get high availability cluster status
    
    Returns:
        High availability cluster status including all nodes information
        
    Example response:
        {
            "is_ha_configured": false,
            "node_name": "node_0",
            "nodes": [
                {
                    "node_name": "node_0",
                    "node_address": "string",
                    "configuration_generated": "2022-01-12T00:00:00.001Z",
                    "status": "OK"
                }
            ],
            "all_nodes_ok": true
        }
    """
    result = await client.get("/system/high-availability-cluster/status")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to get high availability cluster status")
        )
    return result["data"]

# ============== HEALTH CHECK ==============

@router.get("/health",
           summary="Health check for system APIs")
async def system_health_check(client=Depends(get_xroad_client)):
    """Check if system APIs are accessible"""
    try:
        # Test get system status endpoint
        result = await client.get("/system/status")
        
        return {
            "status": "healthy" if result.get("status_code", 200) < 400 else "unhealthy",
            "system_api_accessible": result.get("status_code", 200) < 400,
            "response_time": "OK"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "system_api_accessible": False,
            "error": str(e)
        }