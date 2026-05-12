"""
Authentication and authorization utilities
"""
import os
import logging
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.env import load_env
load_env()

logger = logging.getLogger('ha_cursor_agent')

# Security
security = HTTPBearer()

# Get tokens from environment
SUPERVISOR_TOKEN = os.getenv('SUPERVISOR_TOKEN', '')  # Auto-provided by HA when running as add-on
HA_TOKEN = os.getenv('HA_TOKEN', '')  # Long-Lived Access Token for standalone mode
DEV_TOKEN = os.getenv('HA_AGENT_KEY', '')  # For local development only

# Global variable for API key (will be set by main.py)
API_KEY = None


def set_api_key(key: str):
    """Set the API key (called from main.py)"""
    global API_KEY
    API_KEY = key


async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """
    Verify API key.
    
    Supervisor / Standalone mode (SUPERVISOR_TOKEN or HA_TOKEN exists):
    - Validates against configured API_KEY
    - Agent uses the available token internally for all HA API operations
    
    Development mode (no tokens):
    - Validates against DEV_TOKEN environment variable
    """
    token = credentials.credentials
    token_preview = f"{token[:20]}..." if len(token) > 20 else token
    
    if SUPERVISOR_TOKEN or HA_TOKEN:
        # Supervisor or Standalone mode: Check against API_KEY
        if token != API_KEY:
            logger.warning(f"❌ Invalid API key: {token_preview}")
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        logger.debug(f"✅ API key validated: {token_preview}")
        return token
    else:
        # Development mode: Check against DEV_TOKEN
        logger.debug(f"Development mode: Checking token against DEV_TOKEN")
        if not DEV_TOKEN or token != DEV_TOKEN:
            logger.warning(f"❌ Token mismatch in development mode")
            raise HTTPException(status_code=401, detail="Invalid authentication token")
        logger.info(f"✅ Token validated in development mode")
        return token


