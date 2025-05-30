from fastapi import APIRouter, HTTPException, Query, Depends, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from typing import Optional, List, Dict, Any
import io
from app.core.config import settings
from app.utils.xroad_client_ss import xroad_client, create_xroad_client
from app.schemas.x_road_config import XRoadConfigParams, XRoadEnvironment

router = APIRouter(prefix="/security-server-system", tags=["Security Server - System Configuration"])

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

# ============== SYSTEM ANCHOR APIs ==============

@router.get("/anchor",
           summary="Get anchor configuration info",
           description="Xem thông tin cấu hình anchor")
async def get_anchor_info(client=Depends(get_xroad_client)):
    """
    Xem thông tin cấu hình anchor của hệ thống
    
    Returns:
        Thông tin anchor bao gồm hash và thời gian tạo
        
    Example response:
        {
            "hash": "42:34:C3:22:55:42:34:C3:22:55:42:34:C3:22:55:42:34:C3:22:55:42:34:C3:22:55:42:34:C3",
            "created_at": "2018-12-15T00:00:00.001Z"
        }
    """
    result = await client.get("/system/anchor")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to get anchor configuration")
        )
    return result["data"]

@router.post("/anchor",
            summary="Upload new anchor configuration during server initialization",
            description="Tải lên file cấu hình anchor mới khi khởi tạo máy chủ bảo mật")
async def upload_initial_anchor(
    file: UploadFile = File(..., description="Anchor configuration file"),
    client=Depends(get_xroad_client)
):
    """
    Tải lên file cấu hình anchor mới khi khởi tạo máy chủ bảo mật
    
    Parameters:
        - file: File cấu hình anchor (multipart/form-data)
    
    Returns:
        Kết quả upload anchor configuration
    """
    # Read file content
    file_content = await file.read()
    
    # Prepare multipart form data
    files = {"file": (file.filename, file_content, file.content_type or "application/octet-stream")}
    
    result = await client.post("/system/anchor", files=files)
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to upload initial anchor configuration")
        )
    return result["data"]

@router.put("/anchor",
           summary="Replace current anchor configuration",
           description="Tải lên file cấu hình anchor để thay thế cái hiện tại")
async def replace_anchor(
    file: UploadFile = File(..., description="New anchor configuration file"),
    client=Depends(get_xroad_client)
):
    """
    Thay thế file cấu hình anchor hiện tại
    
    Parameters:
        - file: File cấu hình anchor mới (multipart/form-data)
    
    Returns:
        Kết quả thay thế anchor configuration
    """
    # Read file content
    file_content = await file.read()
    
    # Prepare multipart form data
    files = {"file": (file.filename, file_content, file.content_type or "application/octet-stream")}
    
    result = await client.put("/system/anchor", files=files)
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to replace anchor configuration")
        )
    return result["data"]

@router.post("/anchor/previews",
            summary="Preview anchor configuration",
            description="Đọc file cấu hình anchor và trả về hash để xem trước")
async def preview_anchor(
    file: UploadFile = File(..., description="Anchor configuration file to preview"),
    client=Depends(get_xroad_client)
):
    """
    Đọc file cấu hình anchor và trả về hash để xem trước
    
    Parameters:
        - file: File cấu hình anchor để preview
    
    Returns:
        Hash và thông tin preview của anchor
        
    Example response:
        {
            "hash": "42:34:C3:22:55:42:34:C3:22:55:42:34:C3:22:55:42:34:C3:22:55:42:34:C3:22:55:42:34:C3",
            "created_at": "2018-12-15T00:00:00.001Z"
        }
    """
    # Read file content
    file_content = await file.read()
    
    # Prepare multipart form data
    files = {"file": (file.filename, file_content, file.content_type or "application/octet-stream")}
    
    result = await client.post("/system/anchor/previews", files=files)
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to preview anchor configuration")
        )
    return result["data"]

@router.get("/anchor/download",
           summary="Download anchor configuration",
           description="Tải xuống thông tin cấu hình anchor")
async def download_anchor(client=Depends(get_xroad_client)):
    """
    Tải xuống file cấu hình anchor hiện tại
    
    Returns:
        Binary file stream cho anchor download
    """
    result = await client.get("/system/anchor/download")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to download anchor configuration")
        )
    
    # Extract file content and content type
    content = result["data"]
    content_type = result.get("content_type", "application/octet-stream")
    
    # Return as streaming response for file download
    return StreamingResponse(
        io.BytesIO(content),
        media_type=content_type,
        headers={
            "Content-Disposition": "attachment; filename=anchor.xml",
            "Content-Length": str(len(content))
        }
    )

# ============== SYSTEM CERTIFICATE APIs ==============

@router.get("/certificate",
           summary="Get TLS certificate info",
           description="Xem thông tin chứng chỉ TLS của máy chủ bảo mật")
async def get_tls_certificate_info(client=Depends(get_xroad_client)):
    """
    Xem thông tin chứng chỉ TLS của máy chủ bảo mật
    
    Returns:
        Thông tin chi tiết về chứng chỉ TLS
        
    Example response:
        {
            "issuer_distinguished_name": "issuer123",
            "issuer_common_name": "domain.com",
            "subject_distinguished_name": "subject123",
            "subject_common_name": "domain.com",
            "not_before": "2018-12-15T00:00:00.001Z",
            "not_after": "2018-12-15T00:00:00.001Z",
            "serial": "123456789",
            "version": 3,
            "signature_algorithm": "sha256WithRSAEncryption",
            "key_usages": ["NON_REPUDIATION"]
        }
    """
    result = await client.get("/system/certificate")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to get TLS certificate information")
        )
    return result["data"]

@router.post("/certificate",
            summary="Generate new internal TLS key and certificate",
            description="Tạo mới khóa và chứng chỉ TLS nội bộ")
async def generate_tls_certificate(client=Depends(get_xroad_client)):
    """
    Tạo mới khóa và chứng chỉ TLS nội bộ
    
    Returns:
        Kết quả tạo chứng chỉ TLS mới
    """
    result = await client.post("/system/certificate")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to generate new TLS certificate")
        )
    return result["data"]

@router.get("/certificate/export",
           summary="Export TLS certificate",
           description="Tải xuống chứng chỉ TLS của máy chủ bảo mật dưới dạng tệp nén tar gzip")
async def export_tls_certificate(client=Depends(get_xroad_client)):
    """
    Tải xuống chứng chỉ TLS dưới dạng file tar.gz
    
    Returns:
        Binary file stream cho certificate export
    """
    result = await client.get("/system/certificate/export")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to export TLS certificate")
        )
    
    # Extract file content and content type
    content = result["data"]
    content_type = result.get("content_type", "application/gzip")
    
    # Return as streaming response for file download
    return StreamingResponse(
        io.BytesIO(content),
        media_type=content_type,
        headers={
            "Content-Disposition": "attachment; filename=tls_certificate.tar.gz",
            "Content-Length": str(len(content))
        }
    )

@router.post("/certificate/csr",
            summary="Create certificate signing request",
            description="Tạo yêu cầu chứng chỉ mới")
async def create_certificate_csr(
    csr_data: Dict[str, Any],
    client=Depends(get_xroad_client)
):
    """
    Tạo Certificate Signing Request cho TLS certificate
    
    Parameters:
        - csr_data: Thông tin để tạo CSR
    
    Returns:
        Kết quả tạo CSR
        
    Example request:
        {
            "name": "C=FI, O=X-Road Test, OU=X-Road Test CA OU, CN=X-Road Test CA CN"
        }
    """
    result = await client.post("/system/certificate/csr", data=csr_data)
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to create certificate CSR")
        )
    return result["data"]

@router.post("/certificate/import",
            summary="Import internal TLS certificate",
            description="Nhập chứng chỉ TLS nội bộ mới")
async def import_tls_certificate(
    file: UploadFile = File(..., description="TLS certificate file to import"),
    client=Depends(get_xroad_client)
):
    """
    Nhập chứng chỉ TLS nội bộ mới từ file
    
    Parameters:
        - file: File chứng chỉ TLS để import
    
    Returns:
        Thông tin chứng chỉ đã được import
    """
    # Read file content
    file_content = await file.read()
    
    # Prepare multipart form data
    files = {"file": (file.filename, file_content, file.content_type or "application/octet-stream")}
    
    result = await client.post("/system/certificate/import", files=files)
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to import TLS certificate")
        )
    return result["data"]

# ============== SYSTEM SERVER ADDRESS APIs ==============

@router.get("/server-address",
           summary="Get server address and status",
           description="Xem địa chỉ và trạng thái của máy chủ bảo mật")
async def get_server_address(client=Depends(get_xroad_client)):
    """
    Xem địa chỉ hiện tại và thay đổi được yêu cầu của máy chủ bảo mật
    
    Returns:
        Thông tin địa chỉ server hiện tại và yêu cầu thay đổi
        
    Example response:
        {
            "current_address": {
                "address": "127.0.0.1"
            },
            "requested_change": {
                "address": "127.0.0.1"
            }
        }
    """
    result = await client.get("/system/server-address")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to get server address")
        )
    return result["data"]

@router.put("/server-address",
           summary="Change server address",
           description="Thay đổi địa chỉ máy chủ bảo mật")
async def change_server_address(
    address_data: Dict[str, Any],
    client=Depends(get_xroad_client)
):
    """
    Thay đổi địa chỉ máy chủ bảo mật
    
    Parameters:
        - address_data: Thông tin địa chỉ mới
    
    Returns:
        Kết quả thay đổi địa chỉ server
        
    Example request:
        {
            "address": "127.0.0.1"
        }
    """
    result = await client.put("/system/server-address", data=address_data)
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to change server address")
        )
    return result["data"]

# ============== SYSTEM TIMESTAMPING SERVICES APIs ==============

@router.get("/timestamping-services",
           summary="Get configured timestamping services",
           description="Xem các dịch vụ timestamping đã được cấu hình")
async def get_timestamping_services(client=Depends(get_xroad_client)):
    """
    Xem danh sách các dịch vụ timestamping đã được cấu hình
    
    Returns:
        Danh sách các dịch vụ timestamping
        
    Example response:
        [
            {
                "name": "X-Road Test TSA CN",
                "url": "http://dev.xroad.rocks:123"
            }
        ]
    """
    result = await client.get("/system/timestamping-services")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to get timestamping services")
        )
    return result["data"]

@router.post("/timestamping-services",
            summary="Add new timestamping service",
            description="Thêm một dịch vụ timestamping đã được cấu hình mới")
async def add_timestamping_service(
    service_data: Dict[str, Any],
    client=Depends(get_xroad_client)
):
    """
    Thêm dịch vụ timestamping mới
    
    Parameters:
        - service_data: Thông tin dịch vụ timestamping
    
    Returns:
        Thông tin dịch vụ timestamping đã được thêm
        
    Example request:
        {
            "name": "X-Road Test TSA CN",
            "url": "http://dev.xroad.rocks:123"
        }
    """
    result = await client.post("/system/timestamping-services", data=service_data)
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to add timestamping service")
        )
    return result["data"]

@router.post("/timestamping-services/delete",
            summary="Delete timestamping service",
            description="Xóa dịch vụ timestamping đã được cấu hình")
async def delete_timestamping_service(
    service_data: Dict[str, Any],
    client=Depends(get_xroad_client)
):
    """
    Xóa dịch vụ timestamping đã được cấu hình
    
    Parameters:
        - service_data: Thông tin dịch vụ timestamping cần xóa
    
    Returns:
        Confirmation message
        
    Example request:
        {
            "name": "X-Road Test TSA CN",
            "url": "http://dev.xroad.rocks:123"
        }
    """
    result = await client.post("/system/timestamping-services/delete", data=service_data)
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to delete timestamping service")
        )
    
    return {"message": "Timestamping service deleted successfully"}

# ============== SYSTEM NODE TYPE APIs ==============

@router.get("/node-type",
           summary="Get system node type",
           description="Xem loại nút (node type) của hệ thống")
async def get_node_type(client=Depends(get_xroad_client)):
    """
    Xem loại nút (node type) của hệ thống
    
    Returns:
        Thông tin loại nút của hệ thống
    """
    result = await client.get("/system/node-type")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to get system node type")
        )
    return result["data"]

# ============== SYSTEM VERSION APIs ==============

@router.get("/version",
           summary="Get system version information",
           description="Xem thông tin chi tiết về phiên bản hệ thống")
async def get_system_version(client=Depends(get_xroad_client)):
    """
    Xem thông tin chi tiết về phiên bản hệ thống
    
    Returns:
        Thông tin chi tiết về phiên bản hệ thống và Java
        
    Example response:
        {
            "info": "Security Server version 6.21.0-SNAPSHOT-20190411git32add470",
            "java_version": 0,
            "min_java_version": 0,
            "max_java_version": 0,
            "using_supported_java_version": true,
            "java_vendor": "string",
            "java_runtime_version": "string"
        }
    """
    result = await client.get("/system/version")
    
    if result.get("status_code", 200) >= 400:
        raise HTTPException(
            status_code=result.get("status_code", 500), 
            detail=result.get("error", "Failed to get system version")
        )
    return result["data"]

# ============== HEALTH CHECK ==============

@router.get("/health",
           summary="Health check for security server system APIs")
async def security_server_system_health_check(client=Depends(get_xroad_client)):
    """Check if security server system APIs are accessible"""
    try:
        # Test get system version endpoint
        result = await client.get("/system/version")
        
        return {
            "status": "healthy" if result.get("status_code", 200) < 400 else "unhealthy",
            "security_server_system_api_accessible": result.get("status_code", 200) < 400,
            "system_version": result.get("data", {}).get("info", "Unknown") if result.get("status_code", 200) < 400 else "Unknown",
            "response_time": "OK"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "security_server_system_api_accessible": False,
            "error": str(e)
        }