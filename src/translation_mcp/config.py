"""Configuration management for Translation MCP."""

import os
from pydantic import BaseModel, Field


class TranslationConfig(BaseModel):
    """Configuration for translation settings."""
    
    # Crowdin settings - loaded from MCP environment variables
    crowdin_api_token: str = Field(default_factory=lambda: os.getenv("CROWDIN_API_TOKEN", ""))
    crowdin_project_id: str = Field(default_factory=lambda: os.getenv("CROWDIN_PROJECT_ID", ""))
    crowdin_base_url: str = "https://api.crowdin.com/api/v2"
    
    # Translation settings
    batch_size: int = 10  # Number of strings to process in one batch
