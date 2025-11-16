"""Crowdin API client using official crowdin-api-client."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from crowdin_api import CrowdinClient as OfficialCrowdinClient


@dataclass
class UntranslatedString:
    """Represents an untranslated string from Crowdin."""
    id: int
    text: str
    identifier: str
    context: Optional[str] = None
    file_id: Optional[int] = None
    labels: List[str] = field(default_factory=list)
    existing_translations: Dict[str, str] = field(default_factory=dict)
    missing_languages: List[str] = field(default_factory=list)
    translation_progress: Dict[str, Any] = field(default_factory=dict)


class CrowdinClient:
    """Client for interacting with Crowdin API using official client."""
    
    def __init__(self, api_token: str, project_id: str, base_url: str):
        """
        Initialize Crowdin client.
        
        Args:
            api_token: Crowdin API token
            project_id: Crowdin project ID
            base_url: Base URL (not used with official client)
        """
        self.project_id = int(project_id)
        self.client = OfficialCrowdinClient(token=api_token)
        self._project_languages_cache: Optional[List[str]] = None
    
    def get_project_languages(self) -> List[str]:
        """
        Get list of target languages for the project (cached).
        
        Returns:
            List of language codes
        """
        if self._project_languages_cache is not None:
            return self._project_languages_cache
            
        try:
            project_info = self.client.projects.get_project(projectId=self.project_id)
            target_languages = project_info['data'].get('targetLanguages', [])
            self._project_languages_cache = [lang['id'] for lang in target_languages]
            return self._project_languages_cache
        except Exception as e:
            raise Exception(f"Failed to get project languages: {str(e)}")
    
    def get_untranslated_strings(
        self, 
        limit: int = 500,
        exclude_labels: Optional[List[str]] = None
    ) -> List[UntranslatedString]:
        """
        Get strings that are not fully translated with detailed language-by-language status.
        
        A string is considered "untranslated" if it's missing translations for at least one target language.
        
        Features:
        - Shows exactly which languages are missing translations
        - Shows existing translations for each language
        - Filters out strings with specific labels (e.g., "do-not-translate")
        - Returns detailed progress information per language
        
        Args:
            limit: Maximum number of strings to fetch (default: 500)
            exclude_labels: List of label names to exclude (e.g., ["do-not-translate", "keep-original"])
            
        Returns:
            List of strings with incomplete translations, including:
            - existing_translations: {lang: translation_text}
            - missing_languages: [lang1, lang2, ...]
            - labels: list of labels attached to the string
            - translation_progress: detailed status per language
        """
        try:
            # Get all target languages
            target_languages = self.get_project_languages()
            total_languages = len(target_languages)
            
            # Build CroQL query to find untranslated strings
            croql = f'count of translations < {total_languages}'
            
            # Add label exclusion using count of labels
            # Exclude strings that have any of the specified labels
            if exclude_labels:
                for label_name in exclude_labels:
                    croql += f' and count of labels where (title = "{label_name}") = 0'
            
            # Fetch strings using CroQL
            result = self.client.source_strings.list_strings(
                projectId=self.project_id,
                croql=croql,
                limit=limit
            )
            
            untranslated = []
            
            for item in result['data']:
                string_data = item['data']
                string_id = string_data.get('id')
                
                # Get labels for this string
                labels = [label.get('name', '') for label in string_data.get('labels', [])]
                
                # Get existing translations and calculate missing languages
                existing_translations = self._get_string_translations(string_id)
                missing_languages = [
                    lang for lang in target_languages 
                    if lang not in existing_translations or not existing_translations[lang]
                ]
                
                # Build translation progress dictionary
                translation_progress = {}
                for lang in target_languages:
                    if lang in existing_translations and existing_translations[lang]:
                        translation_progress[lang] = {
                            'status': 'translated',
                            'has_translation': True
                        }
                    else:
                        translation_progress[lang] = {
                            'status': 'missing',
                            'has_translation': False
                        }
                
                untranslated.append(UntranslatedString(
                    id=string_id,
                    text=string_data.get('text', ''),
                    identifier=string_data.get('identifier', ''),
                    context=string_data.get('context'),
                    file_id=string_data.get('fileId'),
                    labels=labels,
                    existing_translations=existing_translations,
                    missing_languages=missing_languages,
                    translation_progress=translation_progress
                ))
            
            return untranslated
            
        except Exception as e:
            raise Exception(f"Failed to get untranslated strings: {str(e)}")
    
    def add_translation(
        self,
        string_id: int,
        language_code: str,
        translation: str
    ) -> Dict[str, Any]:
        """
        Add a translation for a specific string in a specific language.
        
        Args:
            string_id: ID of the source string
            language_code: Target language code (e.g., 'fr', 'es-ES')
            translation: Translated text
            
        Returns:
            API response data with translation details
        """
        try:
            result = self.client.string_translations.add_translation(
                stringId=string_id,
                languageId=language_code,
                text=translation,
                projectId=self.project_id
            )
            return result
        except Exception as e:
            raise Exception(f"Failed to add translation for string {string_id} in {language_code}: {str(e)}")
    
    def add_translations_batch(
        self,
        translations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Add multiple translations in a single batch operation.
        
        This method uploads multiple translations and returns detailed results
        for each translation attempt, including success/failure status.
        
        Args:
            translations: List of translation dictionaries, each containing:
                - string_id: ID of the source string
                - language_code: Target language code
                - translation: Translated text
        
        Returns:
            List of result dictionaries with:
                - success: bool - whether translation was added successfully
                - string_id: int - ID of the string
                - language_code: str - language code
                - data: dict - API response (if successful)
                - error: str - error message (if failed)
        """
        results = []
        
        for trans in translations:
            try:
                result = self.add_translation(
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
    
    def search_string(
        self,
        source_text: str
    ) -> Optional[Dict[str, Any]]:
        """
        Search for a string by source text and get all its translations.
        
        This is useful for checking translation status of a specific string
        or finding a string ID by its text content.
        
        Args:
            source_text: Source text to search for (exact match)
            
        Returns:
            Dictionary with string info and all translations, or None if not found:
            {
                "id": int,
                "text": str,
                "identifier": str,
                "context": str,
                "labels": [str],
                "translations": {lang: translation_text},
                "missing_languages": [lang]
            }
        """
        try:
            # Escape quotes for CroQL query
            escaped_text = source_text.replace('"', '\\"')
            croql = f'text = "{escaped_text}"'
            
            result = self.client.source_strings.list_strings(
                projectId=self.project_id,
                croql=croql,
                limit=1
            )
            
            if not result['data']:
                return None
            
            string_data = result['data'][0]['data']
            string_id = string_data.get('id')
            
            # Get all translations for this string
            translations = self._get_string_translations(string_id)
            
            # Get all target languages and determine missing ones
            target_languages = self.get_project_languages()
            missing_languages = [
                lang for lang in target_languages 
                if lang not in translations or not translations[lang]
            ]
            
            # Get labels
            labels = [label.get('name', '') for label in string_data.get('labels', [])]
            
            return {
                "id": string_id,
                "text": string_data.get('text'),
                "identifier": string_data.get('identifier'),
                "context": string_data.get('context'),
                "labels": labels,
                "translations": translations,
                "missing_languages": missing_languages,
                "translation_count": len(translations),
                "total_languages": len(target_languages)
            }
            
        except Exception as e:
            raise Exception(f"Failed to search string: {str(e)}")
    
    def _get_string_translations(
        self,
        string_id: int
    ) -> Dict[str, str]:
        """
        Get all translations for a specific string across all target languages.
        
        This method queries each target language individually to get the
        most recent approved or pending translation.
        
        Args:
            string_id: String ID
            
        Returns:
            Dictionary mapping language codes to translation texts
            Only includes languages that have non-empty translations
        """
        translations = {}
        
        try:
            # Get all target languages
            project_languages = self.get_project_languages()
            
            # Query translations for each language
            for lang_code in project_languages:
                try:
                    # Get translations for this string in this language
                    result = self.client.string_translations.list_string_translations(
                        projectId=self.project_id,
                        stringId=string_id,
                        languageId=lang_code,
                        limit=10
                    )
                    
                    # Get the most recent translation (usually approved or latest)
                    if result.get('data') and len(result['data']) > 0:
                        trans_data = result['data'][0].get('data', {})
                        translation_text = trans_data.get('text', '')
                        
                        # Only add non-empty translations
                        if translation_text and translation_text.strip():
                            translations[lang_code] = translation_text
                        
                except Exception:
                    # Language might not have translation, continue to next
                    continue
            
            return translations
            
        except Exception:
            # Return empty dict if we can't get translations
            return {}
    
    def list_labels(self) -> List[Dict[str, Any]]:
        """
        Get list of all labels in the project.
        
        Returns:
            List of label dictionaries with 'id' and 'title'
        """
        try:
            result = self.client.labels.list_labels(projectId=self.project_id)
            labels = []
            for item in result.get('data', []):
                label_data = item.get('data', {})
                labels.append({
                    'id': label_data.get('id'),
                    'title': label_data.get('title')
                })
            return labels
        except Exception as e:
            raise Exception(f"Failed to list labels: {str(e)}")
    
    def add_label(self, title: str) -> Dict[str, Any]:
        """
        Create a new label in the project.
        
        Args:
            title: Label name (e.g., 'do-not-translate')
            
        Returns:
            Created label data with 'id' and 'title'
        """
        try:
            result = self.client.labels.add_label(
                title=title,
                projectId=self.project_id
            )
            label_data = result.get('data', {})
            return {
                'id': label_data.get('id'),
                'title': label_data.get('title')
            }
        except Exception as e:
            raise Exception(f"Failed to create label '{title}': {str(e)}")
    
    def assign_label_to_strings(
        self,
        label_id: int,
        string_ids: List[int]
    ) -> Dict[str, Any]:
        """
        Assign a label to multiple strings.
        
        Args:
            label_id: ID of the label
            string_ids: List of string IDs to assign the label to
            
        Returns:
            API response data
        """
        try:
            result = self.client.labels.assign_label_to_strings(
                labelId=label_id,
                stringIds=string_ids,
                projectId=self.project_id
            )
            return result
        except Exception as e:
            raise Exception(f"Failed to assign label to strings: {str(e)}")
    
    def unassign_label_from_strings(
        self,
        label_id: int,
        string_ids: List[int]
    ) -> Dict[str, Any]:
        """
        Remove a label from multiple strings.
        
        Args:
            label_id: ID of the label
            string_ids: List of string IDs to remove the label from
            
        Returns:
            API response data
        """
        try:
            result = self.client.labels.unassign_label_from_strings(
                labelId=label_id,
                stringIds=string_ids,
                projectId=self.project_id
            )
            return result
        except Exception as e:
            raise Exception(f"Failed to unassign label from strings: {str(e)}")
    
    def get_or_create_label(self, title: str) -> Dict[str, Any]:
        """
        Get existing label by title or create it if it doesn't exist.
        
        Args:
            title: Label name
            
        Returns:
            Label data with 'id' and 'title'
        """
        # Check if label already exists
        existing_labels = self.list_labels()
        for label in existing_labels:
            if label['title'] == title:
                return label
        
        # Create new label if it doesn't exist
        return self.add_label(title)
