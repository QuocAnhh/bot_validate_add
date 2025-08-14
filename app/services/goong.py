import httpx
import json
import logging
from typing import List, Optional, Dict, Any

from app.core.config import GOONG_API_KEY

logger = logging.getLogger(__name__)

class GoongMapsClient:
    """tương tác với api goong"""
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://rsapi.goong.io"
    
    async def autocomplete(self, input_text: str) -> Dict[str, Any]:
        """
        Searches for a location and analyzes the results to determine if they are clear
        or ambiguous, providing a structured response.
        """
        if not self.api_key:
            logger.error("Goong API key is not configured.")
            return {"status": "ERROR", "message": "API key not configured."}
        
        url = f"{self.base_url}/Place/AutoComplete"
        params = {"api_key": self.api_key, "input": input_text, "limit": 5} # Limit to 5 results
        
        try:
            async with httpx.AsyncClient() as client:
                logger.debug(f"Calling Goong Autocomplete API: {url} with params: {params}")
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                logger.debug(f"Goong Autocomplete response: {json.dumps(data, ensure_ascii=False)}")
                
                predictions = data.get("predictions", [])
                return self._analyze_predictions(predictions)

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error calling Goong API: {e.response.status_code} - {e.response.text}")
            return {"status": "ERROR", "message": "Failed to connect to mapping service."}
        except Exception as e:
            logger.error(f"An unexpected error occurred during Goong Autocomplete call: {str(e)}")
            return {"status": "ERROR", "message": "An unexpected error occurred."}

    def _analyze_predictions(self, predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyzes autocomplete predictions to classify the result."""
        if not predictions:
            return {"status": "NOT_FOUND", "predictions": []}

        if len(predictions) == 1:
            return {"status": "CONFIRMED", "predictions": predictions}

        # Heuristic: If there are multiple results, it's ambiguous.
        # The first result is often the most relevant. We let the LLM decide how to handle it.
        # This simplifies the logic and gives the LLM more control.
        return {"status": "AMBIGUOUS", "predictions": predictions}

    async def get_place_details(self, place_id: str) -> Optional[dict]:
        """lấy chi tiết địa điểm"""
        if not self.api_key or not place_id:
            logger.error("Goong API key or place_id is missing.")
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

    async def get_coords_from_address(self, address: str) -> Optional[dict]:
        """Helper to get coordinates from an address string."""
        if not address:
            return None
        
        autocomplete_result = await self.autocomplete(address)
        
        # Only proceed if we have a confirmed or ambiguous result with predictions
        if autocomplete_result["status"] in ["CONFIRMED", "AMBIGUOUS"] and autocomplete_result["predictions"]:
            top_prediction = autocomplete_result["predictions"][0]
            place_id = top_prediction.get("place_id")
            
            if not place_id:
                logger.warning(f"No place_id in top prediction for: '{address}'")
                return None

            details = await self.get_place_details(place_id)
            if not details or "geometry" not in details:
                logger.warning(f"No details or geometry found for place_id: {place_id}")
                return None
                
            location = details["geometry"]["location"]
            return {"lat": location["lat"], "lng": location["lng"]}
        
        logger.warning(f"Could not get coordinates for address: '{address}'. Status: {autocomplete_result['status']}")
        return None

goong_client = GoongMapsClient(GOONG_API_KEY) 