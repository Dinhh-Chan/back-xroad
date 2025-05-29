# app/api/v1/tokens.py
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List, Dict, Any
from app.core.config import settings
from app.utils.xroad_client import xroad_client, create_xroad_client
from app.schemas.x_road_config import XRoadConfigParams, XRoadEnvironment

router = APIRouter(prefix="/tokens", tags=["X-Road Central Server - Tokens"])

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
           summary="Get tokens list",
           description="Xem danh sách các token")
async def get_tokens(client=Depends(get_xroad_client)):
    """
    View list of tokens
    
    Returns:
        List of tokens with their status and configuration signing keys
        
    Example response:
        [
            {
                "active": true,
                "available": true,
                "id": "0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF",
                "logged_in": true,
                "name": "softToken-0",
                "possible_actions": ["LOGIN"],
                "configuration_signing_keys": [
                    {
                        "active": true,
                        "available": true,
                        "created_at": "2022-01-12T00:00:00.001Z",
                        "id": "123",
                        "key_hash": "0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF",
                        "token_id": "0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF",
                        "label": {
                            "label": "string"
                        },
                        "possible_actions": ["DELETE"],
                        "source_type": "INTERNAL"
                    }
                ],
                "serial_number": "12345",
                "status": "OK"
            }
        ]
    """
    result = await client.get("/tokens")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to get tokens list")
        )
    return result["data"]

@router.put("/{token_id}/login",
           summary="Login to token",
           description="Đăng nhập vào một token")
async def login_token(
    token_id: str,
    login_data: Dict[str, str],
    client=Depends(get_xroad_client)
):
    """
    Login to a token
    
    Parameters:
        - token_id: ID of the token to login to
        - login_data: JSON object with password
    
    Request body example:
        {
            "password": "sm3!!ycat"
        }
    
    Returns:
        Updated token information after login
        
    Example response:
        {
            "active": true,
            "available": true,
            "id": "0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF",
            "logged_in": true,
            "name": "softToken-0",
            "possible_actions": ["LOGIN"],
            "configuration_signing_keys": [
                {
                    "active": true,
                    "available": true,
                    "created_at": "2022-01-12T00:00:00.001Z",
                    "id": "123",
                    "key_hash": "0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF",
                    "token_id": "0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF",
                    "label": {
                        "label": "string"
                    },
                    "possible_actions": ["DELETE"],
                    "source_type": "INTERNAL"
                }
            ],
            "serial_number": "12345",
            "status": "OK"
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
           description="Đăng xuất khỏi token")
async def logout_token(
    token_id: str,
    client=Depends(get_xroad_client)
):
    """
    Logout from a token
    
    Parameters:
        - token_id: ID of the token to logout from
    
    Returns:
        Updated token information after logout
        
    Example response:
        {
            "active": true,
            "available": true,
            "id": "0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF",
            "logged_in": false,
            "name": "softToken-0",
            "possible_actions": ["LOGIN"],
            "configuration_signing_keys": [
                {
                    "active": true,
                    "available": true,
                    "created_at": "2022-01-12T00:00:00.001Z",
                    "id": "123",
                    "key_hash": "0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF",
                    "token_id": "0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF",
                    "label": {
                        "label": "string"
                    },
                    "possible_actions": ["DELETE"],
                    "source_type": "INTERNAL"
                }
            ],
            "serial_number": "12345",
            "status": "OK"
        }
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
           summary="Health check for tokens APIs")
async def tokens_health_check(client=Depends(get_xroad_client)):
    """Check if tokens APIs are accessible"""
    try:
        # Test get tokens endpoint
        result = await client.get("/tokens")
        
        return {
            "status": "healthy" if result.get("status_code", 200) < 400 else "unhealthy",
            "tokens_api_accessible": result.get("status_code", 200) < 400,
            "response_time": "OK"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "tokens_api_accessible": False,
            "error": str(e)
        }