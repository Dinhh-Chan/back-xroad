# utils/xroad_client.py
import httpx
import json
from typing import Optional, Dict, Any, Union
from urllib3.exceptions import InsecureRequestWarning
import urllib3
from app.core.config import settings
# Disable SSL warnings
urllib3.disable_warnings(InsecureRequestWarning)

class XRoadClient:
    """
    Simple utility class for forwarding requests to X-Road Central Server API
    """
    
    def __init__(self, base_url: str = None, 
                 api_key: str = None, 
                 timeout: int = None):
        # Import here to avoid circular import
        
        self.base_url = (base_url or settings.XROAD_BASE_URL_SS).rstrip('/')
        self.api_key = api_key or settings.XROAD_API_KEY_SS
        self.timeout = timeout or settings.XROAD_TIMEOUT
        self.headers = {
            "Authorization": f"X-Road-ApiKey token={self.api_key}",
            "Content-Type": "application/json"
        }
    
    def _build_url(self, endpoint: str) -> str:
        """Build full URL from endpoint"""
        if not endpoint.startswith('/'):
            endpoint = f'/{endpoint}'
        if not endpoint.startswith('/api/v1/'):
            if endpoint.startswith('/api/'):
                return f"{self.base_url}{endpoint}"
            else:
                return f"{self.base_url}/api/v1{endpoint}"
        return f"{self.base_url}{endpoint}"
    
    async def _make_request(self, method: str, endpoint: str, 
                           data: Optional[Dict] = None, 
                           files: Optional[Dict] = None,
                           params: Optional[Dict] = None) -> Dict[str, Any]:
        """Generic method to make HTTP requests"""
        url = self._build_url(endpoint)
        
        async with httpx.AsyncClient(verify=False, timeout=self.timeout) as client:
            try:
                headers = self.headers.copy()
                
                # Handle multipart/form-data requests
                if files:
                    headers.pop("Content-Type", None)  # Let httpx set it for multipart
                
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data if not files else None,
                    files=files,
                    data=data if files else None,
                    params=params
                )
                
                # Handle different response types
                if response.status_code == 204:  # No content
                    return {"status": "success", "data": None}
                
                # Try to parse as JSON first
                try:
                    result = response.json()
                    return {
                        "status_code": response.status_code,
                        "data": result,
                        "headers": dict(response.headers)
                    }
                except:
                    # Handle binary/text responses (like file downloads)
                    return {
                        "status_code": response.status_code,
                        "data": response.content,
                        "headers": dict(response.headers),
                        "content_type": response.headers.get("content-type", "application/octet-stream")
                    }
                    
            except httpx.RequestError as e:
                return {
                    "status_code": 500,
                    "error": f"Request failed: {str(e)}",
                    "data": None
                }
            except Exception as e:
                return {
                    "status_code": 500,
                    "error": f"Unexpected error: {str(e)}",
                    "data": None
                }
    
    # HTTP Methods
    async def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """GET request"""
        return await self._make_request("GET", endpoint, params=params)
    
    async def post(self, endpoint: str, data: Optional[Dict] = None, 
                   files: Optional[Dict] = None) -> Dict[str, Any]:
        """POST request"""
        return await self._make_request("POST", endpoint, data=data, files=files)
    
    async def put(self, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """PUT request"""
        return await self._make_request("PUT", endpoint, data=data)
    
    async def patch(self, endpoint: str, data: Optional[Dict] = None,
                    files: Optional[Dict] = None) -> Dict[str, Any]:
        """PATCH request"""
        return await self._make_request("PATCH", endpoint, data=data, files=files)
    
    async def delete(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """DELETE request"""
        return await self._make_request("DELETE", endpoint, params=params)

# Singleton instance - có thể tùy chỉnh khi khởi tạo
xroad_client = XRoadClient()

# Factory function để tạo client với config khác
def create_xroad_client(base_url: str = None, api_key: str = None, timeout: int = None) -> XRoadClient:
    """Create XRoad client with custom configuration"""
    return XRoadClient(
        base_url=base_url,
        api_key=api_key,
        timeout=timeout
    )