from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum

class XRoadEnvironment(str, Enum):
    """Available X-Road environments"""
    dev = "dev"
    prod = "prod"
    test = "test"

class XRoadConfigParams(BaseModel):
    """Common X-Road configuration parameters"""
    custom_base_url: Optional[str] = Field(None, description="Custom X-Road base URL to override default")
    custom_api_key: Optional[str] = Field(None, description="Custom X-Road API key to override default")
    env_prefix: Optional[XRoadEnvironment] = Field(None, description="Environment prefix (dev, prod, test)")
    
    class Config:
        schema_extra = {
            "example": {
                "custom_base_url": "https://custom-xroad.server.com:4000",
                "custom_api_key": "custom-api-key-here",
                "env_prefix": "dev"
            }
        }
