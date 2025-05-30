from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List, Dict, Any
from app.core.config import settings
from app.utils.xroad_client_ss import xroad_client, create_xroad_client
from app.schemas.x_road_config import XRoadConfigParams, XRoadEnvironment

router = APIRouter(prefix="/security-server-xroad-instances", tags=["Security Server - X-Road Instances"])

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

# ============== X-ROAD INSTANCES APIs ==============

@router.get("/xroad-instances",
           summary="Get X-Road instance identifiers",
           description="Lấy danh sách các định danh phiên bản X-Road")
async def get_xroad_instances(client=Depends(get_xroad_client)):
    """
    Lấy danh sách các định danh phiên bản X-Road có sẵn
    
    Returns:
        Danh sách các định danh phiên bản X-Road
        
    Example response:
        [
            "FI",
            "EE", 
            "LV",
            "LT"
        ]
    """
    result = await client.get("/xroad-instances")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to get X-Road instances")
        )
    return result["data"]

# ============== HEALTH CHECK ==============

@router.get("/health",
           summary="Health check for X-Road instances APIs")
async def xroad_instances_health_check(client=Depends(get_xroad_client)):
    """Check if X-Road instances APIs are accessible"""
    try:
        # Test get X-Road instances endpoint
        result = await client.get("/xroad-instances")
        
        instances_count = len(result.get("data", [])) if result.get("status_code", 200) < 400 else 0
        
        return {
            "status": "healthy" if result.get("status_code", 200) < 400 else "unhealthy",
            "xroad_instances_api_accessible": result.get("status_code", 200) < 400,
            "instances_count": instances_count,
            "response_time": "OK"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "xroad_instances_api_accessible": False,
            "error": str(e)
        }