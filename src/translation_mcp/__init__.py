"""Translation MCP Server - AI-powered Crowdin translation automation."""

__version__ = "1.0.0"

from .config import TranslationConfig
from .crowdin_client import CrowdinClient, UntranslatedString

__all__ = [
    "TranslationConfig",
    "CrowdinClient",
    "UntranslatedString",
]
