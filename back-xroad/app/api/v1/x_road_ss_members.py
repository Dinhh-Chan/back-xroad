from fastapi import APIRouter, HTTPException, Query, Depends, Path
from typing import Optional, List, Dict, Any
from app.core.config import settings
from app.utils.xroad_client_ss import xroad_client, create_xroad_client
from app.schemas.x_road_config import XRoadConfigParams, XRoadEnvironment

router = APIRouter(prefix="/security-server-members", tags=["Security Server - Member Management"])

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

@router.get("/member-classes",
           summary="Get known member classes",
           description="Lấy danh sách các lớp thành viên đã biết")
async def get_member_classes(client=Depends(get_xroad_client)):
    """
    Lấy danh sách các lớp thành viên đã biết trong hệ thống X-Road
    
    Returns:
        Danh sách các lớp thành viên
        
    Example response:
        [
            "GOV",
            "COM", 
            "NGO",
            "NEE"
        ]
    """
    result = await client.get("/member-classes")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to get member classes")
        )
    return result["data"]

@router.get("/member-classes/{instance_id}",
           summary="Get known member classes for instance",
           description="Lấy danh sách các lớp thành viên đã biết cho một phiên bản cụ thể")
async def get_member_classes_for_instance(
    instance_id: str = Path(..., description="ID của phiên bản X-Road"),
    client=Depends(get_xroad_client)
):
    """
    Lấy danh sách các lớp thành viên đã biết cho một phiên bản X-Road cụ thể
    
    Parameters:
        - instance_id: ID của phiên bản X-Road
    
    Returns:
        Danh sách các lớp thành viên cho phiên bản đó
        
    Example response:
        [
            "GOV",
            "COM", 
            "NGO"
        ]
    """
    result = await client.get(f"/member-classes/{instance_id}")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to get member classes for instance {instance_id}")
        )
    return result["data"]

# ============== MEMBER NAMES APIs ==============

@router.get("/member-names",
           summary="Find member name by class and code",
           description="Tìm tên thành viên theo lớp thành viên và mã thành viên")
async def get_member_name(
    member_class: str = Query(..., description="Lớp thành viên (ví dụ: GOV, COM)"),
    member_code: str = Query(..., description="Mã thành viên"),
    instance_id: Optional[str] = Query(None, description="ID phiên bản X-Road (tùy chọn)"),
    client=Depends(get_xroad_client)
):
    """
    Tìm tên thành viên dựa trên lớp thành viên và mã thành viên
    
    Parameters:
        - member_class: Lớp thành viên (GOV, COM, NGO, etc.)
        - member_code: Mã định danh thành viên
        - instance_id: ID phiên bản X-Road (tùy chọn)
    
    Returns:
        Thông tin tên thành viên
        
    Example response:
        {
            "member_name": "Ministry of Finance"
        }
    """
    # Build query parameters
    params = {
        "member_class": member_class,
        "member_code": member_code
    }
    
    if instance_id:
        params["instance_id"] = instance_id
    
    result = await client.get("/member-names", params=params)
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to get member name for {member_class}:{member_code}")
        )
    return result["data"]

@router.get("/member-names/search",
           summary="Search member names",
           description="Tìm kiếm tên thành viên với nhiều tiêu chí")
async def search_member_names(
    member_class: Optional[str] = Query(None, description="Lọc theo lớp thành viên"),
    member_code: Optional[str] = Query(None, description="Lọc theo mã thành viên"),
    member_name: Optional[str] = Query(None, description="Tìm kiếm theo tên thành viên"),
    instance_id: Optional[str] = Query(None, description="Lọc theo phiên bản X-Road"),
    limit: Optional[int] = Query(50, description="Giới hạn số kết quả trả về", ge=1, le=1000),
    offset: Optional[int] = Query(0, description="Bỏ qua số kết quả từ đầu", ge=0),
    client=Depends(get_xroad_client)
):
    """
    Tìm kiếm thành viên với nhiều tiêu chí lọc
    
    Parameters:
        - member_class: Lọc theo lớp thành viên
        - member_code: Lọc theo mã thành viên  
        - member_name: Tìm kiếm theo tên (hỗ trợ partial match)
        - instance_id: Lọc theo phiên bản X-Road
        - limit: Số lượng kết quả tối đa
        - offset: Bỏ qua số kết quả từ đầu
    
    Returns:
        Danh sách thành viên phù hợp với tiêu chí tìm kiếm
        
    Example response:
        [
            {
                "member_class": "GOV",
                "member_code": "70006317",
                "member_name": "Ministry of Finance",
                "instance_id": "FI"
            }
        ]
    """
    # Build query parameters, only include non-None values
    params = {}
    
    if member_class:
        params["member_class"] = member_class
    if member_code:
        params["member_code"] = member_code
    if member_name:
        params["member_name"] = member_name
    if instance_id:
        params["instance_id"] = instance_id
    if limit:
        params["limit"] = limit
    if offset:
        params["offset"] = offset
    
    result = await client.get("/member-names/search", params=params)
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to search member names")
        )
    return result["data"]

# ============== MEMBER DETAILS APIs ==============

@router.get("/members/{member_class}/{member_code}",
           summary="Get member details",
           description="Lấy thông tin chi tiết của thành viên")
async def get_member_details(
    member_class: str = Path(..., description="Lớp thành viên"),
    member_code: str = Path(..., description="Mã thành viên"),
    instance_id: Optional[str] = Query(None, description="ID phiên bản X-Road"),
    client=Depends(get_xroad_client)
):
    """
    Lấy thông tin chi tiết của một thành viên cụ thể
    
    Parameters:
        - member_class: Lớp thành viên 
        - member_code: Mã thành viên
        - instance_id: ID phiên bản X-Road (tùy chọn)
    
    Returns:
        Thông tin chi tiết của thành viên
        
    Example response:
        {
            "member_class": "GOV",
            "member_code": "70006317", 
            "member_name": "Ministry of Finance",
            "instance_id": "FI",
            "subsystems": [
                {
                    "subsystem_code": "management",
                    "subsystem_name": "Management System"
                }
            ]
        }
    """
    # Build query parameters
    params = {}
    if instance_id:
        params["instance_id"] = instance_id
    
    result = await client.get(f"/members/{member_class}/{member_code}", params=params)
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to get details for member {member_class}:{member_code}")
        )
    return result["data"]

# ============== UTILITY APIs ==============

@router.get("/instances",
           summary="Get available X-Road instances",
           description="Lấy danh sách các phiên bản X-Road có sẵn")
async def get_xroad_instances(client=Depends(get_xroad_client)):
    """
    Lấy danh sách các phiên bản X-Road có sẵn trong hệ thống
    
    Returns:
        Danh sách các phiên bản X-Road
        
    Example response:
        [
            {
                "instance_id": "FI",
                "instance_name": "Finland X-Road Instance"
            },
            {
                "instance_id": "EE", 
                "instance_name": "Estonia X-Road Instance"
            }
        ]
    """
    result = await client.get("/instances")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to get X-Road instances")
        )
    return result["data"]

# ============== HEALTH CHECK ==============

@router.get("/health",
           summary="Health check for security server members APIs")
async def security_server_members_health_check(client=Depends(get_xroad_client)):
    """Check if security server members APIs are accessible"""
    try:
        # Test get member classes endpoint
        result = await client.get("/member-classes")
        
        return {
            "status": "healthy" if result.get("status_code", 200) < 400 else "unhealthy",
            "security_server_members_api_accessible": result.get("status_code", 200) < 400,
            "member_classes_count": len(result.get("data", [])) if result.get("status_code", 200) < 400 else 0,
            "response_time": "OK"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "security_server_members_api_accessible": False,
            "error": str(e)
        }