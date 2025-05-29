import os
from typing import Optional
from pydantic_settings import BaseSettings
from keycloak.keycloak_openid import KeycloakOpenID

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))

class Settings(BaseSettings):
    PROJECT_NAME: str = os.environ.get("PROJECT_NAME", "FASTAPI_BASE")
    SECRET_KEY: str = os.environ.get("SECRET_KEY", None)
    API_PREFIX: str = os.environ.get("API_PREFIX", "/api")
    API_VERSIONS: str = os.environ.get("API_VERSIONS", "")
    API_VERSION: str = os.environ.get("API_VERSION", "v1")
    BACKEND_CORS_ORIGINS: str = os.environ.get("BACKEND_CORS_ORIGINS", '["*"]')
    DATABASE_URL: str = (
        f"postgresql+psycopg2://{os.environ.get('POSTGRES_USER')}:{os.environ.get('POSTGRES_PASSWORD')}@{os.environ.get('POSTGRES_HOST')}:{os.environ.get('POSTGRES_PORT')}/{os.environ.get('POSTGRES_DB')}"
    )
    ACCESS_TOKEN_EXPIRE_SECONDS: int = 60 * 60 * 24 * 7  # Token expired after 7 days
    SECURITY_ALGORITHM: str = "HS256"
    LOGGING_CONFIG_FILE: str = os.path.join(BASE_DIR, "logging.ini")
    DEBUG: bool = os.environ.get("DEBUG", "False").lower() == "true"
    
    # Keycloak Settings
    KEYCLOAK_SERVER_URL: Optional[str] = os.environ.get("KEYCLOAK_SERVER_URL", None)
    KEYCLOAK_REALM: Optional[str] = os.environ.get("KEYCLOAK_REALM", None)
    KEYCLOAK_CLIENT_ID: Optional[str] = os.environ.get("KEYCLOAK_CLIENT_ID", None)
    KEYCLOAK_CLIENT_SECRET: Optional[str] = os.environ.get("KEYCLOAK_CLIENT_SECRET", None)
    KEYCLOAK_VERIFY: Optional[bool] = os.environ.get("KEYCLOAK_VERIFY", "False").lower() == "true"
    GOOGLE_CLIENT_ID: Optional[str] = os.environ.get("GOOGLE_CLIENT_ID", None)
    
    # X-Road Settings
    XROAD_BASE_URL_CS: str = os.environ.get("XROAD_BASE_URL", "https://192.168.30.195:4000")
    XROAD_API_KEY: str = os.environ.get("XROAD_API_KEY", "d54a4bfe-104c-4c39-87a4-5b847fa6680d")
    XROAD_TIMEOUT: int = int(os.environ.get("XROAD_TIMEOUT", "30"))
    
    # X-Road Multiple Environment Support
    XROAD_DEV_BASE_URL: Optional[str] = os.environ.get("XROAD_DEV_BASE_URL", None)
    XROAD_DEV_API_KEY: Optional[str] = os.environ.get("XROAD_DEV_API_KEY", None)
    XROAD_DEV_TIMEOUT: Optional[int] = int(os.environ.get("XROAD_DEV_TIMEOUT", "30")) if os.environ.get("XROAD_DEV_TIMEOUT") else None
    
    XROAD_PROD_BASE_URL: Optional[str] = os.environ.get("XROAD_PROD_BASE_URL", None)
    XROAD_PROD_API_KEY: Optional[str] = os.environ.get("XROAD_PROD_API_KEY", None)
    XROAD_PROD_TIMEOUT: Optional[int] = int(os.environ.get("XROAD_PROD_TIMEOUT", "30")) if os.environ.get("XROAD_PROD_TIMEOUT") else None
    
    XROAD_TEST_BASE_URL: Optional[str] = os.environ.get("XROAD_TEST_BASE_URL", None)
    XROAD_TEST_API_KEY: Optional[str] = os.environ.get("XROAD_TEST_API_KEY", None)
    XROAD_TEST_TIMEOUT: Optional[int] = int(os.environ.get("XROAD_TEST_TIMEOUT", "30")) if os.environ.get("XROAD_TEST_TIMEOUT") else None
    
    def get_xroad_config(self, env_prefix: Optional[str] = None) -> dict:
        """Get X-Road configuration for specific environment or default"""
        if env_prefix:
            prefix = env_prefix.upper()
            return {
                "base_url": getattr(self, f"XROAD_{prefix}_BASE_URL", None) or self.XROAD_BASE_URL,
                "api_key": getattr(self, f"XROAD_{prefix}_API_KEY", None) or self.XROAD_API_KEY,
                "timeout": getattr(self, f"XROAD_{prefix}_TIMEOUT", None) or self.XROAD_TIMEOUT
            }
        return {
            "base_url": self.XROAD_BASE_URL,
            "api_key": self.XROAD_API_KEY,
            "timeout": self.XROAD_TIMEOUT
        }
    
    def get_available_xroad_environments(self) -> list:
        """Get list of configured X-Road environments"""
        environments = []
        for env in ["DEV", "PROD", "TEST"]:
            if getattr(self, f"XROAD_{env}_BASE_URL", None):
                environments.append(env.lower())
        return environments

settings = Settings()

# Keycloak OpenID setup
if (
    settings.KEYCLOAK_SERVER_URL != None
    and settings.KEYCLOAK_REALM != None
    and settings.KEYCLOAK_CLIENT_ID != None
    and settings.KEYCLOAK_CLIENT_SECRET != None
    and settings.KEYCLOAK_VERIFY != None
):
    keycloak_openid = KeycloakOpenID(
        server_url=settings.KEYCLOAK_SERVER_URL,
        realm_name=settings.KEYCLOAK_REALM,
        client_id=settings.KEYCLOAK_CLIENT_ID,
        client_secret_key=settings.KEYCLOAK_CLIENT_SECRET,
        verify=settings.KEYCLOAK_VERIFY,
    )
else:
    keycloak_openid = None

def get_openid_config():
    if keycloak_openid == None:
        return {}
    return keycloak_openid.well_known()