"""Translation MCP Server - works with any AI client."""

import asyncio
import json
from typing import Any, Dict, List
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp import stdio_server

from .config import TranslationConfig
from .classifier import StringClassifier, StringType
from .crowdin_client import CrowdinClient


# Initialize server
app = Server("translation-mcp")

# Global state
config: TranslationConfig = None
crowdin_client: CrowdinClient = None
classifier: StringClassifier = None


def initialize_clients():
    """Initialize all clients with configuration."""
    global config, crowdin_client, classifier
    
    config = TranslationConfig()
    
    crowdin_client = CrowdinClient(
        api_token=config.crowdin_api_token,
        project_id=config.crowdin_project_id,
        base_url=config.crowdin_base_url
    )
    
    classifier = StringClassifier(
        names=config.known_names,
        brands=config.known_brands
    )


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="get_project_info",
            description="Get Crowdin project information including target languages",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_untranslated_strings",
            description="Get untranslated strings with classification and translation instructions for AI",
            inputSchema={
                "type": "object",
                "properties": {
                    "languages": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional: specific language codes. If not provided, uses all project languages."
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of strings to fetch (default: 50)",
                        "default": 50
                    }
                }
            }
        ),
        Tool(
            name="upload_translations",
            description="Upload translated strings to Crowdin",
            inputSchema={
                "type": "object",
                "properties": {
                    "translations": {
                        "type": "array",
                        "description": "Array of translation objects",
                        "items": {
                            "type": "object",
                            "properties": {
                                "string_id": {"type": "integer"},
                                "language_code": {"type": "string"},
                                "translation": {"type": "string"}
                            },
                            "required": ["string_id", "language_code", "translation"]
                        }
                    }
                },
                "required": ["translations"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls."""
    
    # Ensure clients are initialized
    if crowdin_client is None:
        initialize_clients()
    
    if name == "get_project_info":
        return await handle_get_project_info()
    
    elif name == "get_untranslated_strings":
        return await handle_get_untranslated(arguments)
    
    elif name == "upload_translations":
        return await handle_upload_translations(arguments)
    
    else:
        raise ValueError(f"Unknown tool: {name}")


async def handle_get_project_info() -> List[TextContent]:
    """Get project information including target languages."""
    try:
        languages = await crowdin_client.get_project_languages()
        
        info = {
            "project_id": config.crowdin_project_id,
            "target_languages": languages,
            "total_languages": len(languages),
            "message": "Project loaded successfully"
        }
        
        return [TextContent(
            type="text",
            text=json.dumps(info, indent=2)
        )]
        
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error getting project info: {str(e)}"
        )]


async def handle_get_untranslated(arguments: Dict[str, Any]) -> List[TextContent]:
    """Get untranslated strings with AI translation instructions."""
    try:
        # Get target languages
        languages = arguments.get("languages")
        if not languages:
            languages = await crowdin_client.get_project_languages()
        
        limit = arguments.get("limit", 50)
        
        # Get untranslated strings (from first language to get the list)
        first_lang = languages[0]
        untranslated = await crowdin_client.get_untranslated_strings(first_lang, limit)
        
        if not untranslated:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "message": "No untranslated strings found",
                    "languages": languages
                }, indent=2)
            )]
        
        # Classify and prepare strings for AI translation
        strings_data = []
        for s in untranslated:
            string_type = classifier.classify(s.text, s.identifier)
            
            strings_data.append({
                "id": s.id,
                "text": s.text,
                "identifier": s.identifier,
                "context": s.context,
                "type": string_type.value,
                "translation_note": _get_translation_note(string_type)
            })
        
        # Prepare response with instructions for AI
        response = {
            "strings": strings_data,
            "target_languages": languages,
            "total_strings": len(strings_data),
            "instructions": _get_translation_instructions(),
            "message": f"Found {len(strings_data)} untranslated strings. Please translate them according to the type rules."
        }
        
        return [TextContent(
            type="text",
            text=json.dumps(response, indent=2, ensure_ascii=False)
        )]
        
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error getting untranslated strings: {str(e)}"
        )]


def _get_translation_note(string_type: StringType) -> str:
    """Get translation note based on string type."""
    notes = {
        StringType.REGULAR: "Translate naturally to target language",
        StringType.LANGUAGE_NAME: "Keep original - do NOT translate language names (e.g., 'English' stays 'English')",
        StringType.PROPER_NAME: "Keep original - do NOT translate proper names",
        StringType.BRAND: "Keep original - do NOT translate brand names",
        StringType.TECHNICAL: "Technical term - translate carefully or keep as-is"
    }
    return notes.get(string_type, "Translate normally")


def _get_translation_instructions() -> str:
    """Get general translation instructions for AI."""
    return """
Translation Guidelines:
1. REGULAR text: Translate naturally, maintain professional tone for restaurant POS system
2. LANGUAGE NAMES: Keep original (English → English, Spanish → Spanish)
3. PROPER NAMES: Keep original (Steve Jobs → Steve Jobs)
4. BRANDS: Keep original (iPhone → iPhone, Google → Google)
5. TECHNICAL: Evaluate context - API/technical terms usually stay in English

After translating, call upload_translations with this format:
{
  "translations": [
    {"string_id": 123, "language_code": "fr", "translation": "Bonjour"},
    {"string_id": 123, "language_code": "de", "translation": "Hallo"},
    ...
  ]
}
"""


async def handle_upload_translations(arguments: Dict[str, Any]) -> List[TextContent]:
    """Upload translations to Crowdin."""
    try:
        translations = arguments.get("translations", [])
        
        if not translations:
            return [TextContent(
                type="text",
                text="Error: No translations provided"
            )]
        
        # Upload translations in batch
        results = await crowdin_client.add_translations_batch(translations)
        
        # Count successes and failures
        success_count = sum(1 for r in results if r.get("success"))
        failure_count = len(results) - success_count
        
        response = {
            "total": len(results),
            "successful": success_count,
            "failed": failure_count,
            "message": f"Uploaded {success_count}/{len(results)} translations successfully"
        }
        
        if failure_count > 0:
            failed_items = [r for r in results if not r.get("success")]
            response["failures"] = failed_items[:5]  # Show first 5 failures
        
        return [TextContent(
            type="text",
            text=json.dumps(response, indent=2)
        )]
        
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error uploading translations: {str(e)}"
        )]


async def main():
    """Run the MCP server."""
    # Initialize clients
    initialize_clients()
    
    # Run server with stdio transport
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
