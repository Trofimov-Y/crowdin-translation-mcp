"""Crowdin API client."""

import httpx
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class UntranslatedString:
    """Represents an untranslated string from Crowdin."""
    id: int
    text: str
    identifier: str
    context: Optional[str] = None
    file_id: Optional[int] = None


class CrowdinClient:
    """Client for interacting with Crowdin API."""
    
    def __init__(self, api_token: str, project_id: str, base_url: str):
        """
        Initialize Crowdin client.
        
        Args:
            api_token: Crowdin API token
            project_id: Crowdin project ID
            base_url: Base URL for Crowdin API
        """
        self.api_token = api_token
        self.project_id = project_id
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        }
    
    async def get_project_languages(self) -> List[str]:
        """
        Get list of target languages for the project.
        
        Returns:
            List of language codes
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/projects/{self.project_id}",
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            
            # Extract target language codes
            target_languages = data.get("data", {}).get("targetLanguages", [])
            return [lang["id"] for lang in target_languages]
    
    async def get_untranslated_strings(
        self, 
        language_code: str,
        limit: int = 500
    ) -> List[UntranslatedString]:
        """
        Get untranslated strings for a specific language.
        
        Args:
            language_code: Target language code (e.g., 'fr', 'de')
            limit: Maximum number of strings to fetch
            
        Returns:
            List of untranslated strings
        """
        untranslated = []
        offset = 0
        
        async with httpx.AsyncClient() as client:
            while len(untranslated) < limit:
                response = await client.get(
                    f"{self.base_url}/projects/{self.project_id}/strings",
                    headers=self.headers,
                    params={
                        "limit": min(500, limit - len(untranslated)),
                        "offset": offset,
                        "filter": "untranslated"
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                strings = data.get("data", [])
                if not strings:
                    break
                
                for item in strings:
                    string_data = item.get("data", {})
                    untranslated.append(UntranslatedString(
                        id=string_data.get("id"),
                        text=string_data.get("text", ""),
                        identifier=string_data.get("identifier", ""),
                        context=string_data.get("context"),
                        file_id=string_data.get("fileId")
                    ))
                
                offset += len(strings)
                
                # Check if we've fetched all available strings
                if len(strings) < 500:
                    break
        
        return untranslated[:limit]
    
    async def add_translation(
        self,
        string_id: int,
        language_code: str,
        translation: str
    ) -> Dict[str, Any]:
        """
        Add a translation for a string.
        
        Args:
            string_id: ID of the source string
            language_code: Target language code
            translation: Translated text
            
        Returns:
            API response data
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/projects/{self.project_id}/translations",
                headers=self.headers,
                json={
                    "stringId": string_id,
                    "languageId": language_code,
                    "text": translation
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def add_translations_batch(
        self,
        translations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Add multiple translations in batch.
        
        Args:
            translations: List of translation dictionaries with keys:
                - string_id: ID of the source string
                - language_code: Target language code
                - translation: Translated text
        
        Returns:
            List of API responses
        """
        results = []
        
        async with httpx.AsyncClient() as client:
            for trans in translations:
                try:
                    result = await self.add_translation(
                        trans["string_id"],
                        trans["language_code"],
                        trans["translation"]
                    )
                    results.append({
                        "success": True,
                        "string_id": trans["string_id"],
                        "language_code": trans["language_code"],
                        "data": result
                    })
                except Exception as e:
                    results.append({
                        "success": False,
                        "string_id": trans["string_id"],
                        "language_code": trans["language_code"],
                        "error": str(e)
                    })
        
        return results
