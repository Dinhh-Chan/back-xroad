from fastapi import APIRouter, HTTPException, Query, Depends, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from typing import Optional, List, Dict, Any
import io
from app.core.config import settings
from app.utils.xroad_client_ss import xroad_client, create_xroad_client
from app.schemas.x_road_config import XRoadConfigParams, XRoadEnvironment

router = APIRouter(prefix="/initialization", tags=["Security Server - Initialization"])

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

# ============== INITIALIZATION APIs ==============

@router.post("/",
            summary="Initialize Security Server",
            description="Khởi tạo một máy chủ bảo mật mới với cấu hình ban đầu")
async def initialize_security_server(
    initialization_data: Dict[str, Any],
    client=Depends(get_xroad_client)
):
    """
    Initialize new security server with initial configuration
    
    Parameters:
        - initialization_data: JSON object with initialization parameters
    
    Request body example:
        {
            "owner_member_class": "GOV",
            "owner_member_code": "12345678-9",
            "security_server_code": "SS1",
            "software_token_pin": "sup3rs3cr3t_p!n",
            "ignore_warnings": false
        }
    
    Returns:
        Initialization result
    """
    result = await client.post("/initialization", data=initialization_data)
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to initialize security server")
        )
    
    return result["data"]

@router.get("/status",
           summary="Get initialization status",
           description="Kiểm tra trạng thái khởi tạo của máy chủ bảo mật")
async def get_initialization_status(client=Depends(get_xroad_client)):
    """
    Check initialization status of security server
    
    Returns:
        Security server initialization status with detailed information
        
    Example response:
        {
            "is_anchor_imported": true,
            "is_server_code_initialized": true,
            "is_server_owner_initialized": true,
            "software_token_init_status": "INITIALIZED",
            "enforce_token_pin_policy": true
        }
    """
    result = await client.get("/initialization/status")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to get initialization status")
        )
    
    return result["data"]

# ============== INITIALIZATION STEPS ==============

@router.get("/steps",
           summary="Get initialization steps",
           description="Xem các bước khởi tạo máy chủ bảo mật")
async def get_initialization_steps(client=Depends(get_xroad_client)):
    """
    Get security server initialization steps and their completion status
    
    Returns:
        List of initialization steps with completion status
    """
    status_result = await client.get("/initialization/status")
    
    if status_result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=status_result.get("status_code", 500), 
            detail=status_result.get("error", "Failed to get initialization status")
        )
    
    status_data = status_result["data"]
    
    # Build initialization steps based on status
    steps = [
        {
            "step": 1,
            "name": "Import Configuration Anchor",
            "description": "Import global configuration anchor file",
            "completed": status_data.get("is_anchor_imported", False),
            "required": True
        },
        {
            "step": 2,
            "name": "Initialize Software Token",
            "description": "Set up software token with PIN",
            "completed": status_data.get("software_token_init_status") == "INITIALIZED",
            "required": True
        },
        {
            "step": 3,
            "name": "Configure Server Owner",
            "description": "Set up security server owner member information",
            "completed": status_data.get("is_server_owner_initialized", False),
            "required": True
        },
        {
            "step": 4,
            "name": "Set Server Code",
            "description": "Configure unique security server code",
            "completed": status_data.get("is_server_code_initialized", False),
            "required": True
        }
    ]
    
    # Calculate overall completion
    completed_steps = len([step for step in steps if step["completed"]])
    total_steps = len(steps)
    completion_percentage = (completed_steps / total_steps) * 100
    
    return {
        "steps": steps,
        "completion_status": {
            "completed_steps": completed_steps,
            "total_steps": total_steps,
            "completion_percentage": completion_percentage,
            "fully_initialized": completion_percentage == 100.0
        },
        "initialization_status": status_data
    }

# ============== VALIDATION HELPERS ==============

@router.get("/validate-configuration",
           summary="Validate initialization configuration",
           description="Xác thực cấu hình khởi tạo")
async def validate_initialization_configuration(
    owner_member_class: Optional[str] = Query(None, description="Owner member class"),
    owner_member_code: Optional[str] = Query(None, description="Owner member code"),
    security_server_code: Optional[str] = Query(None, description="Security server code"),
    client=Depends(get_xroad_client)
):
    """
    Validate initialization configuration parameters
    
    Parameters:
        - owner_member_class: Owner member class (e.g., "GOV", "COM")
        - owner_member_code: Owner member code
        - security_server_code: Security server code
    
    Returns:
        Validation results for the provided parameters
    """
    validation_results = {
        "valid": True,
        "errors": [],
        "warnings": []
    }
    
    # Basic validation
    if owner_member_class:
        if owner_member_class not in ["GOV", "COM", "ORG", "EDU"]:
            validation_results["errors"].append("Invalid member class. Must be one of: GOV, COM, ORG, EDU")
            validation_results["valid"] = False
    
    if owner_member_code:
        if len(owner_member_code) < 3:
            validation_results["errors"].append("Member code must be at least 3 characters long")
            validation_results["valid"] = False
    
    if security_server_code:
        if len(security_server_code) < 2:
            validation_results["errors"].append("Security server code must be at least 2 characters long")
            validation_results["valid"] = False
        if not security_server_code.replace("-", "").replace("_", "").isalnum():
            validation_results["errors"].append("Security server code can only contain alphanumeric characters, hyphens, and underscores")
            validation_results["valid"] = False
    
    return validation_results

# ============== HEALTH CHECK ==============

@router.get("/health",
           summary="Health check for initialization APIs")
async def initialization_health_check(client=Depends(get_xroad_client)):
    """Check if initialization APIs are accessible"""
    try:
        # Test get initialization status endpoint
        result = await client.get("/initialization/status")
        
        return {
            "status": "healthy" if result.get("status_code", 200) < 400 else "unhealthy",
            "initialization_api_accessible": result.get("status_code", 200) < 400,
            "response_time": "OK"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "initialization_api_accessible": False,
            "error": str(e)
        }