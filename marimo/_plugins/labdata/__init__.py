"""Labdata integration for marimo."""
import os
from pathlib import Path
from typing import Optional

from marimo._config.config import get_config

class LabdataManager:
    """Manages Labdata integration and authentication."""
    
    def __init__(self):
        self._config = get_config().get("labdata", {})
        self._client: Optional["Labdata"] = None

    def get_client(self) -> "Labdata":
        """Get or create a Labdata client."""
        if self._client is None:
            from labdata import Labdata
            
            credentials = self._load_credentials()
            self._client = Labdata(**credentials)
            
        return self._client

    def _load_credentials(self) -> dict:
        """Load credentials from config file or environment."""
        creds_path = Path(
            os.path.expanduser(self._config.get("credentials_path"))
        )
        
        if creds_path.exists():
            import json
            with open(creds_path) as f:
                return json.load(f)
                
        # Fallback to environment variables
        return {
            "token": os.environ.get("LABDATA_TOKEN"),
            "api_url": os.environ.get("LABDATA_API_URL"),
        }

# Global instance
_manager = LabdataManager()

def get_labdata() -> "Labdata":
    """Get a configured Labdata client."""
    return _manager.get_client()