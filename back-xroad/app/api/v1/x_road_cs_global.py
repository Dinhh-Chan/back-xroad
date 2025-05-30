from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.core.config import settings
from app.utils.xroad_client_cs import xroad_client, create_xroad_client
from app.schemas.x_road_config import XRoadConfigParams, XRoadEnvironment

router = APIRouter(prefix="/global-groups", tags=["X-Road Central Server - Global Groups"])

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

# ============== GLOBAL GROUPS APIs ==============

@router.get("/",
           summary="Get global groups",
           description="Tìm kiếm và hiển thị danh sách các global groups")
async def get_global_groups(client=Depends(get_xroad_client)):
    """
    Search and display list of global groups
    
    Returns:
        List of global groups with basic information
        
    Example response:
        [
            {
                "code": "groupcode",
                "description": "description",
                "created_at": "2022-01-20T00:00:00.001Z",
                "updated_at": "2022-01-22T07:30:00.001Z",
                "member_count": 10
            }
        ]
    """
    result = await client.get("/global-groups")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to get global groups")
        )
    return result["data"]

@router.post("/",
            summary="Create global group",
            description="Thêm mới một nhóm toàn cầu với mã nhóm và mô tả")
async def create_global_group(
    group_data: Dict[str, str],
    client=Depends(get_xroad_client)
):
    """
    Add new global group with group code and description
    
    Parameters:
        - group_data: JSON object with code and description
    
    Request body example:
        {
            "code": "groupcode",
            "description": "description"
        }
    
    Returns:
        Created global group information with timestamps and member count
        
    Example response:
        {
            "code": "groupcode",
            "description": "description",
            "created_at": "2022-01-20T00:00:00.001Z",
            "updated_at": "2022-01-22T07:30:00.001Z",
            "member_count": 10
        }
    """
    result = await client.post("/global-groups", data=group_data)
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to create global group")
        )
    return result["data"]

@router.get("/{group_code}",
           summary="Get global group details",
           description="Hiển thị thông tin chi tiết về một nhóm toàn cầu cụ thể")
async def get_global_group(
    group_code: str,
    client=Depends(get_xroad_client)
):
    """
    Display detailed information about a specific global group
    
    Parameters:
        - group_code: Code of the global group
    
    Returns:
        Detailed global group information
        
    Example response:
        {
            "code": "groupcode",
            "description": "description",
            "created_at": "2022-01-20T00:00:00.001Z",
            "updated_at": "2022-01-22T07:30:00.001Z",
            "member_count": 10
        }
    """
    result = await client.get(f"/global-groups/{group_code}")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to get global group {group_code}")
        )
    return result["data"]

@router.delete("/{group_code}",
              summary="Delete global group",
              description="Xóa một nhóm toàn cầu")
async def delete_global_group(
    group_code: str,
    client=Depends(get_xroad_client)
):
    """
    Delete a global group
    
    Parameters:
        - group_code: Code of the global group to delete
    
    Returns:
        Confirmation message
    """
    result = await client.delete(f"/global-groups/{group_code}")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to delete global group {group_code}")
        )
    
    return {"message": f"Global group {group_code} deleted successfully"}

@router.patch("/{group_code}",
             summary="Update global group",
             description="Cập nhật mô tả của nhóm toàn cầu")
async def update_global_group(
    group_code: str,
    update_data: Dict[str, str],
    client=Depends(get_xroad_client)
):
    """
    Update global group description
    
    Parameters:
        - group_code: Code of the global group
        - update_data: JSON object with description to update
    
    Request body example:
        {
            "description": "description"
        }
    
    Returns:
        Updated global group information
        
    Example response:
        {
            "code": "groupcode",
            "description": "description",
            "created_at": "2022-01-20T00:00:00.001Z",
            "updated_at": "2022-01-22T07:30:00.001Z",
            "member_count": 10
        }
    """
    result = await client.patch(f"/global-groups/{group_code}", data=update_data)
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to update global group {group_code}")
        )
    return result["data"]

# ============== GLOBAL GROUP MEMBERS APIs ==============

@router.get("/{group_code}/members/filter-model",
           summary="Get members filter model",
           description="Lấy mô hình lọc để tìm kiếm các thành viên của nhóm toàn cầu")
async def get_members_filter_model(
    group_code: str,
    client=Depends(get_xroad_client)
):
    """
    Get filter model for searching global group members
    
    Parameters:
        - group_code: Code of the global group
    
    Returns:
        Filter model with available options for searching members
        
    Example response:
        {
            "instances": ["string"],
            "member_classes": ["string"],
            "codes": ["string"],
            "subsystems": ["string"]
        }
    """
    result = await client.get(f"/global-groups/{group_code}/members/filter-model")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to get filter model for global group {group_code}")
        )
    return result["data"]

@router.post("/{group_code}/members/add",
            summary="Add members to global group",
            description="Cho phép CS thêm một thành viên X-Road hoặc một subsystem của thành viên vào nhóm toàn cầu")
async def add_members_to_global_group(
    group_code: str,
    members_data: Dict[str, List[str]],
    client=Depends(get_xroad_client)
):
    """
    Allow CS to add X-Road member or member subsystem to global group
    
    Parameters:
        - group_code: Code of the global group
        - members_data: JSON object with list of member/subsystem IDs to add
    
    Request body example:
        {
            "items": [
                "FI:GOV:123",
                "FI:GOV:123:SS1",
                "FI:GOV:123:SS2"
            ]
        }
    
    Returns:
        List of added members/subsystems
        
    Example response:
        {
            "items": [
                "FI:GOV:123",
                "FI:GOV:123:SS1",
                "FI:GOV:123:SS2"
            ]
        }
    """
    result = await client.post(f"/global-groups/{group_code}/members/add", data=members_data)
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to add members to global group {group_code}")
        )
    return result["data"]

@router.post("/{group_code}/members",
            summary="View global group members",
            description="CS có thể xem danh sách các thành viên của nhóm toàn cầu")
async def view_global_group_members(
    group_code: str,
    search_criteria: Dict[str, Any],
    client=Depends(get_xroad_client)
):
    """
    CS can view list of global group members with search and pagination
    
    Parameters:
        - group_code: Code of the global group
        - search_criteria: JSON object with search and pagination parameters (Request Body)
    
    Request body example:
        {
            "query": "string",
            "member_class": "string",
            "instance": "string",
            "codes": ["string"],
            "subsystems": ["string"],
            "types": ["SUBSYSTEM"],
            "paging_sorting": {
                "sort": "title",
                "desc": false,
                "limit": 25,
                "offset": 0
            }
        }
    
    Returns:
        Paginated list of global group members
        
    Example response:
        {
            "items": [
                {
                    "created_at": "2022-01-20T00:00:00.001Z",
                    "id": 123,
                    "client_id": {
                        "instance_id": "FI",
                        "type": "MEMBER",
                        "member_class": "GOV",
                        "member_code": "123",
                        "encoded_id": "string",
                        "subsystem_code": "ABC"
                    },
                    "name": "Member123"
                }
            ],
            "paging_metadata": {
                "total_items": 0,
                "items": 0,
                "limit": 25,
                "offset": 0
            }
        }
    """
    # Truyền search_criteria như JSON data trong request body
    result = await client.post(f"/global-groups/{group_code}/members", data=search_criteria)
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to get members of global group {group_code}")
        )
    return result["data"]

@router.delete("/{group_code}/members/{client_id}",
              summary="Remove member from global group",
              description="Có thể xóa một thành viên khỏi nhóm toàn cầu")
async def remove_member_from_global_group(
    group_code: str,
    client_id: str,
    xroad_client=Depends(get_xroad_client)
):
    """
    Remove a member from global group
    
    Parameters:
        - group_code: Code of the global group
        - client_id: ID of the client/member to remove
    
    Returns:
        Confirmation message
    """
    result = await xroad_client.delete(f"/global-groups/{group_code}/members/{client_id}")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to remove member {client_id} from global group {group_code}")
        )
    
    return {"message": f"Member {client_id} removed from global group {group_code} successfully"}

# ============== MEMBER'S GLOBAL GROUPS API ==============

@router.get("/members/{member_id}/global-groups",
           summary="Get member's global groups",
           description="CS xem nhóm toàn cầu của các thành viên")
async def get_member_global_groups(
    member_id: str,
    client=Depends(get_xroad_client)
):
    """
    CS can view global groups of members
    
    Parameters:
        - member_id: ID of the member (format: instance:member_class:member_code or instance:member_class:member_code:subsystem_code)
    
    Returns:
        List of global groups that the member belongs to
        
    Example response:
        [
            {
                "group_code": "string",
                "subsystem": "string", 
                "added_to_group": "2022-01-22T07:30:00.001Z"
            }
        ]
    """
    result = await client.get(f"/members/{member_id}/global-groups")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to get global groups for member {member_id}")
        )
    return result["data"]

# ============== HEALTH CHECK ==============

@router.get("/health",
           summary="Health check for global groups")
async def global_groups_health_check(client=Depends(get_xroad_client)):
    """Check if global groups APIs are accessible"""
    try:
        # Test get global groups endpoint
        result = await client.get("/global-groups")
        
        return {
            "status": "healthy" if result.get("status_code", 200) < 400 else "unhealthy",
            "global_groups_api_accessible": result.get("status_code", 200) < 400,
            "response_time": "OK"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "global_groups_api_accessible": False,
            "error": str(e)
        }