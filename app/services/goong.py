import httpx
import json
import logging
from typing import List, Optional

from app.core.config import GOONG_API_KEY

logger = logging.getLogger(__name__)

class GoongMapsClient:
    """A client for interacting with the Goong Maps Geocoding API."""
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://rsapi.goong.io"
    
    async def autocomplete(self, input_text: str) -> List[dict]:
        """
        Fetches address predictions from Goong's Place Autocomplete API.
        """
        if not self.api_key:
            logger.error("Goong API key is not configured.")
            return []
        
        url = f"{self.base_url}/Place/AutoComplete"
        params = {"api_key": self.api_key, "input": input_text}
        
        try:
            async with httpx.AsyncClient() as client:
                logger.debug(f"Calling Goong Autocomplete API: {url} with params: {params}")
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                logger.debug(f"Goong Autocomplete response: {json.dumps(data, ensure_ascii=False)}")
                return data.get("predictions", [])
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error calling Goong Autocomplete API: {e.response.status_code} - {e.response.text}")
            return []
        except Exception as e:
            logger.error(f"An unexpected error occurred during Goong Autocomplete call: {str(e)}")
            return []

    async def get_place_details(self, place_id: str) -> Optional[dict]:
        """
        Fetches detailed information for a specific place_id from Goong's Place Detail API.
        """
        if not self.api_key:
            logger.error("Goong API key is not configured.")
            return None
            
        url = f"{self.base_url}/Place/Detail"
        params = {"api_key": self.api_key, "place_id": place_id}
        
        try:
            async with httpx.AsyncClient() as client:
                logger.debug(f"Calling Goong Place Detail API: {url} with params: {params}")
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                logger.debug(f"Goong Place Detail response: {json.dumps(data, ensure_ascii=False)}")
                return data.get("result")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error calling Goong Place Detail API: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred during Goong Place Detail call: {str(e)}")
            return None

goong_client = GoongMapsClient(GOONG_API_KEY) 