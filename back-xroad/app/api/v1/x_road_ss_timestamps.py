from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List, Dict, Any
from app.core.config import settings
from app.utils.xroad_client_ss import xroad_client, create_xroad_client
from app.schemas.x_road_config import XRoadConfigParams, XRoadEnvironment

router = APIRouter(prefix="/security-server-timestamping", tags=["Security Server - Timestamping Services"])

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
           summary="Get approved timestamping services",
           description="Xem các dịch vụ đóng dấu thời gian đã được phê duyệt")
async def get_approved_timestamping_services(client=Depends(get_xroad_client)):
    """
    Xem danh sách các dịch vụ đóng dấu thời gian đã được phê duyệt
    
    Returns:
        Danh sách các dịch vụ timestamping đã được phê duyệt
        
    Example response:
        [
            {
                "name": "X-Road Test TSA CN",
                "url": "http://dev.xroad.rocks:123"
            }
        ]
    """
    result = await client.get("/timestamping-services")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to get approved timestamping services")
        )
    return result["data"]

# ============== HEALTH CHECK ==============

@router.get("/health",
           summary="Health check for timestamping services APIs")
async def timestamping_services_health_check(client=Depends(get_xroad_client)):
    """Check if timestamping services APIs are accessible"""
    try:
        # Test get timestamping services endpoint
        result = await client.get("/timestamping-services")
        
        services_count = len(result.get("data", [])) if result.get("status_code", 200) < 400 else 0
        
        return {
            "status": "healthy" if result.get("status_code", 200) < 400 else "unhealthy",
            "timestamping_services_api_accessible": result.get("status_code", 200) < 400,
            "approved_services_count": services_count,
            "response_time": "OK"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamping_services_api_accessible": False,
            "error": str(e)
        }