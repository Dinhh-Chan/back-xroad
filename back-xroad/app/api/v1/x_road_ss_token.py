from fastapi import APIRouter, HTTPException, Query, Depends, Path
from typing import Optional, List, Dict, Any
from app.core.config import settings
from app.utils.xroad_client_ss import xroad_client, create_xroad_client
from app.schemas.x_road_config import XRoadConfigParams, XRoadEnvironment

router = APIRouter(prefix="/security-server-tokens", tags=["Security Server - Token Management"])

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

# ============== TOKENS APIs ==============

@router.get("/",
           summary="Get security server tokens",
           description="Xem các token của máy chủ bảo mật")
async def get_security_server_tokens(client=Depends(get_xroad_client)):
    """
    Xem danh sách các token của máy chủ bảo mật
    
    Returns:
        Danh sách các token với thông tin chi tiết
        
    Example response:
        [
            {
                "id": "0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF",
                "name": "softToken-0",
                "type": "SOFTWARE",
                "keys": [...],
                "status": "OK",
                "logged_in": true,
                "available": true,
                "saved_to_configuration": true,
                "read_only": true,
                "serial_number": "12345",
                "token_infos": [...],
                "possible_actions": ["DELETE"]
            }
        ]
    """
    result = await client.get("/tokens")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to get security server tokens")
        )
    return result["data"]

@router.get("/{token_id}",
           summary="Get token details",
           description="Xem thông tin chi tiết của mã thông báo máy chủ bảo mật")
async def get_token_details(
    token_id: str = Path(..., description="ID của token"),
    client=Depends(get_xroad_client)
):
    """
    Xem thông tin chi tiết của một token cụ thể
    
    Parameters:
        - token_id: ID của token
    
    Returns:
        Thông tin chi tiết của token
        
    Example response:
        {
            "id": "0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF",
            "name": "softToken-0",
            "type": "SOFTWARE",
            "keys": [...],
            "status": "OK",
            "logged_in": true,
            "available": true,
            "saved_to_configuration": true,
            "read_only": true,
            "serial_number": "12345",
            "token_infos": [...],
            "possible_actions": ["DELETE"]
        }
    """
    result = await client.get(f"/tokens/{token_id}")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to get token details for {token_id}")
        )
    return result["data"]

@router.patch("/{token_id}",
             summary="Update token information",
             description="Cập nhật thông tin mã thông báo")
async def update_token_info(
    token_data: Dict[str, Any],
    token_id: str = Path(..., description="ID của token cần cập nhật"),
    client=Depends(get_xroad_client)
):
    """
    Cập nhật thông tin token (hiện tại chỉ hỗ trợ cập nhật tên)
    
    Parameters:
        - token_id: ID của token
        - token_data: Thông tin cập nhật cho token
    
    Returns:
        Thông tin token đã được cập nhật
        
    Example request:
        {
            "name": "my-token-0"
        }
    """
    result = await client.patch(f"/tokens/{token_id}", data=token_data)
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to update token {token_id}")
        )
    return result["data"]

@router.put("/{token_id}/pin",
           summary="Update software token PIN",
           description="Cập nhật mã pin của mã thông báo phần mềm")
async def update_token_pin(
    pin_data: Dict[str, Any],
    token_id: str = Path(..., description="ID của token"),
    client=Depends(get_xroad_client)
):
    """
    Cập nhật mã PIN của token phần mềm
    
    Parameters:
        - token_id: ID của token
        - pin_data: Thông tin PIN cũ và mới
    
    Returns:
        Kết quả cập nhật PIN
        
    Example request:
        {
            "old_pin": 0,
            "new_pin": 1234
        }
    """
    result = await client.put(f"/tokens/{token_id}/pin", data=pin_data)
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to update PIN for token {token_id}")
        )
    return result["data"]

@router.post("/{token_id}/keys-with-csrs",
            summary="Add new key and create CSR",
            description="Thêm một khóa mới và tạo yêu cầu chứng nhận (CSR) cho nó")
async def add_key_with_csr(
    key_csr_data: Dict[str, Any],
    token_id: str = Path(..., description="ID của token"),
    client=Depends(get_xroad_client)
):
    """
    Thêm khóa mới và tạo CSR cho token
    
    Parameters:
        - token_id: ID của token
        - key_csr_data: Thông tin để tạo key và CSR
    
    Returns:
        Thông tin key đã tạo và CSR ID
        
    Example request:
        {
            "key_label": "My new key",
            "csr_generate_request": {
                "key_usage_type": "SIGNING",
                "ca_name": "Customized Test CA CN",
                "csr_format": "DER",
                "member_id": "CS:NIIS:1234",
                "subject_field_values": {
                    "CN": "something.niis.org",
                    "C": "FI",
                    "O": "NIIS",
                    "serialNumber": "CS/SS1/NIIS"
                }
            }
        }
        
    Example response:
        {
            "key": {...},
            "csr_id": "0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF"
        }
    """
    result = await client.post(f"/tokens/{token_id}/keys-with-csrs", data=key_csr_data)
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to add key with CSR for token {token_id}")
        )
    return result["data"]

@router.post("/{token_id}/keys",
            summary="Add new key to token",
            description="Thêm khóa mới cho mã thông báo đã chọn")
async def add_key_to_token(
    key_data: Dict[str, Any],
    token_id: str = Path(..., description="ID của token"),
    client=Depends(get_xroad_client)
):
    """
    Thêm khóa mới cho token đã chọn
    
    Parameters:
        - token_id: ID của token
        - key_data: Thông tin để tạo key
    
    Returns:
        Thông tin key đã được tạo
        
    Example request:
        {
            "key_label": "My new key",
            "csr_generate_request": {
                "key_usage_type": "SIGNING",
                "ca_name": "Customized Test CA CN",
                "csr_format": "DER",
                "member_id": "CS:NIIS:1234",
                "subject_field_values": {
                    "CN": "something.niis.org",
                    "C": "FI",
                    "O": "NIIS",
                    "serialNumber": "CS/SS1/NIIS"
                }
            }
        }
    """
    result = await client.post(f"/tokens/{token_id}/keys", data=key_data)
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to add key to token {token_id}")
        )
    return result["data"]

@router.put("/{token_id}/login",
           summary="Login to token",
           description="Đăng nhập vào một token")
async def login_to_token(
    login_data: Dict[str, Any],
    token_id: str = Path(..., description="ID của token"),
    client=Depends(get_xroad_client)
):
    """
    Đăng nhập vào token với password
    
    Parameters:
        - token_id: ID của token
        - login_data: Thông tin đăng nhập
    
    Returns:
        Thông tin token sau khi đăng nhập
        
    Example request:
        {
            "password": "sm3!!ycat"
        }
    """
    result = await client.put(f"/tokens/{token_id}/login", data=login_data)
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to login to token {token_id}")
        )
    return result["data"]

@router.put("/{token_id}/logout",
           summary="Logout from token",
           description="Đăng xuất khỏi một token")
async def logout_from_token(
    token_id: str = Path(..., description="ID của token"),
    client=Depends(get_xroad_client)
):
    """
    Đăng xuất khỏi token
    
    Parameters:
        - token_id: ID của token
    
    Returns:
        Thông tin token sau khi đăng xuất
    """
    result = await client.put(f"/tokens/{token_id}/logout")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", f"Failed to logout from token {token_id}")
        )
    return result["data"]

# ============== HEALTH CHECK ==============

@router.get("/health",
           summary="Health check for security server tokens APIs")
async def security_server_tokens_health_check(client=Depends(get_xroad_client)):
    """Check if security server tokens APIs are accessible"""
    try:
        # Test get tokens endpoint
        result = await client.get("/tokens")
        
        tokens_count = len(result.get("data", [])) if result.get("status_code", 200) < 400 else 0
        
        return {
            "status": "healthy" if result.get("status_code", 200) < 400 else "unhealthy",
            "security_server_tokens_api_accessible": result.get("status_code", 200) < 400,
            "tokens_count": tokens_count,
            "response_time": "OK"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "security_server_tokens_api_accessible": False,
            "error": str(e)
        }