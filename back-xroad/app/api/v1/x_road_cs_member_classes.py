from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List, Dict, Any
from app.core.config import settings
from app.utils.xroad_client_cs import xroad_client, create_xroad_client
from app.schemas.x_road_config import XRoadConfigParams, XRoadEnvironment

router = APIRouter(prefix="/member-classes", tags=["X-Road Central Server - Member Classes"])

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

# ============== MEMBER CLASSES APIs ==============

@router.get("/",
           summary="Get member classes",
           description="Liệt kê các lớp thành viên")
async def get_member_classes(client=Depends(get_xroad_client)):
    """
    List member classes
    
    Returns:
        List of member classes with description and code
        
    Example response:
        [
            {
                "description": "Non-profit organisations",
                "code": "ORG"
            },
            {
                "description": "Governmental organizations",
                "code": "GOV"
            },
            {
                "description": "Commercial organizations",
                "code": "COM"
            },
            {
                "description": "Educational organizations",
                "code": "EDU"
            }
        ]
    """
    result = await client.get("/member-classes")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to get member classes")
        )
    return result["data"]

@router.post("/",
            summary="Create member class",
            description="Thêm một lớp thành viên mới")
async def create_member_class(
    class_data: Dict[str, str],
    client=Depends(get_xroad_client)
):
    """
    Add new member class
    
    Parameters:
        - class_data: JSON object with description and code
    
    Request body example:
        {
            "description": "Non-profit organisations",
            "code": "ORG"
        }
    
    Returns:
        Created member class information
        
    Example response:
        {
            "description": "Non-profit organisations",
            "code": "ORG"
        }
    """
    result = await client.post("/member-classes", data=class_data)
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to create member class")
        )
    return result["data"]

@router.delete("/{code}",
              summary="Delete member class",
              description="Xóa một lớp thành viên")
async def delete_member_class(
    code: str,
    client=Depends(get_xroad_client)
):
    """
    Delete a member class
    
    Parameters:
        - code: Code of the member class to delete (e.g., "ORG", "GOV", "COM", "EDU")
    
    Returns:
        Confirmation message
    """
    result = await client.delete(f"/member-classes/{code}")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to delete member class {code}")
        )
    
    return {"message": f"Member class {code} deleted successfully"}

@router.patch("/{code}",
             summary="Update member class",
             description="Cập nhật mô tả của một lớp thành viên")
async def update_member_class(
    code: str,
    update_data: Dict[str, str],
    client=Depends(get_xroad_client)
):
    """
    Update member class description
    
    Parameters:
        - code: Code of the member class to update (e.g., "ORG", "GOV", "COM", "EDU")
        - update_data: JSON object with description to update
    
    Request body example:
        {
            "description": "Non-profit organisations"
        }
    
    Returns:
        Updated member class information
        
    Example response:
        {
            "description": "Non-profit organisations",
            "code": "ORG"
        }
    """
    result = await client.patch(f"/member-classes/{code}", data=update_data)
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to update member class {code}")
        )
    return result["data"]

# ============== HEALTH CHECK ==============

@router.get("/health",
           summary="Health check for member classes APIs")
async def member_classes_health_check(client=Depends(get_xroad_client)):
    """Check if member classes APIs are accessible"""
    try:
        # Test get member classes endpoint
        result = await client.get("/member-classes")
        
        return {
            "status": "healthy" if result.get("status_code", 200) < 400 else "unhealthy",
            "member_classes_api_accessible": result.get("status_code", 200) < 400,
            "response_time": "OK"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "member_classes_api_accessible": False,
            "error": str(e)
        }