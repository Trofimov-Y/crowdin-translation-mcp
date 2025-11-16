"""Translation MCP Server - Professional Crowdin translation workflow automation.

This MCP server provides tools for managing translations in Crowdin projects.
It helps AI assistants and developers efficiently handle translation workflows.
"""

import asyncio
import json
from typing import Any, Dict, List
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp import stdio_server

from .config import TranslationConfig
from .crowdin_client import CrowdinClient


# Initialize server
app = Server("translation-mcp")

# Global state
config: TranslationConfig = None
crowdin_client: CrowdinClient = None


def initialize_clients():
    """Initialize all clients with configuration."""
    global config, crowdin_client
    
    config = TranslationConfig()
    
    crowdin_client = CrowdinClient(
        api_token=config.crowdin_api_token,
        project_id=config.crowdin_project_id,
        base_url=config.crowdin_base_url
    )


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available MCP tools with detailed descriptions for AI understanding."""
    return [
        Tool(
            name="get_project_info",
            description="""Get Crowdin project information and configuration.
            
            USE THIS WHEN:
            - User asks "what languages are in the project?"
            - User wants to know project configuration
            - Starting a new translation session
            - Need to understand project setup
            
            RETURNS:
            - Project ID
            - List of all target languages (e.g., ['fr', 'es-ES', 'de'])
            - Total language count
            
            This is a good first step before checking untranslated strings.""",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_untranslated_strings",
            description="""Get strings that need translation in a compact table format.
            
            USE THIS WHEN:
            - User asks "what needs to be translated?"
            - User wants to see translation progress
            - Need to find strings missing in specific languages
            - Starting translation work
            
            🔴 CRITICAL RESPONSE FORMAT:
            You MUST return ONLY a markdown table. No summaries, no tips, no extra text.
            
            CORRECT FORMAT:
            | ID | Text | Identifier | Missing Languages |
            |----|------|------------|-------------------|
            | 36 | `Routine` | `routine` | fr, de, it |
            | 38 | `{numMinutes} min` | `numMinutes` | fr, es-ES, it |
            
            MANDATORY RULES:
            ✅ ALWAYS display the complete table with ALL rows
            ✅ Show EVERY missing language in full (no "and more...")
            ✅ Only output the table - nothing before/after
            ✅ If no strings: show empty table with "All strings translated"
            
            ❌ NEVER add: summaries, headers, tips, emojis outside table
            ❌ NEVER truncate: "...and 5 more languages" or similar
            ❌ NEVER split: table + "How to proceed" sections
            
            WRONG EXAMPLES:
            ❌ "Found 27 strings needing translation:\n[Table]\n💡 Next steps..."
            ❌ "# Translation Status\n[Table]\n## How to Proceed"
            ❌ "Here are untranslated strings: [Table]"
            
            CORRECT EXAMPLE:
            ✅ Just the table, nothing else
            
            PARAMETERS:
            - limit: Max strings to return (default: 35, max: 500)
            - exclude_labels: Labels to filter out (default: ['do-not-translate'])
              Use [] to see all strings including marked ones
            
            WORKFLOW:
            1. Call this tool → Review table
            2. Mark names/brands: use manage_labels with 'do-not-translate'
            3. Provide translations → Use upload_translations
            
            EXAMPLES:
            "Show untranslated strings" → Returns table only
            "Get all untranslated including marked" → Use exclude_labels=[]
            "Show 100 strings" → Use limit=100""",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of strings to fetch (default: 35, max: 500)",
                        "default": 35,
                        "minimum": 1,
                        "maximum": 500
                    },
                    "exclude_labels": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of label names to exclude (default: ['do-not-translate']). Use [] to see all strings.",
                        "default": ["do-not-translate"]
                    }
                }
            }
        ),
        Tool(
            name="manage_labels",
            description="""Manage labels for strings in Crowdin (mark as do-not-translate, etc).
            
            USE THIS WHEN:
            - User wants to mark strings as 'do not translate'
            - Need to organize strings with labels
            - Want to see available labels
            - Need to remove labels from strings
            
            ACTIONS:
            - 'list': Get all labels in project
            - 'assign': Add label to strings (creates label if needed)
            - 'unassign': Remove label from strings
            
            COMMON USE CASE:
            User sees strings in untranslated list that shouldn't be translated:
            1. User: "Mark strings 274, 284, 300 as do not translate"
            2. You: manage_labels(action="assign", label_name="do-not-translate", string_ids=[274, 284, 300])
            3. Next get_untranslated_strings call will filter these out automatically
            
            PARAMETERS:
            - action: 'list', 'assign', or 'unassign'
            - label_name: Name of label (for assign/unassign)
            - string_ids: List of string IDs (for assign/unassign)
            
            EXAMPLES:
            - See all labels: manage_labels(action="list")
            - Mark strings: manage_labels(action="assign", label_name="do-not-translate", string_ids=[38, 346])
            - Remove label: manage_labels(action="unassign", label_name="do-not-translate", string_ids=[38])""",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["list", "assign", "unassign"],
                        "description": "Action to perform: list labels, assign label to strings, or unassign label"
                    },
                    "label_name": {
                        "type": "string",
                        "description": "Name of the label (e.g., 'do-not-translate', 'reviewed')"
                    },
                    "string_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "List of string IDs to assign/unassign label to/from"
                    }
                },
                "required": ["action"]
            }
        ),
        Tool(
            name="upload_translations",
            description="""Upload translated strings to Crowdin in batch.
            
            USE THIS WHEN:
            - User provides translations ready to upload
            - After translating strings from get_untranslated_strings
            - Need to add multiple translations at once
            
            IMPORTANT:
            - Only upload translations for languages shown as MISSING
            - Don't upload for languages already translated
            - Each translation needs: string_id, language_code, translation text
            
            INPUT FORMAT:
            {
              "translations": [
                {"string_id": 38, "language_code": "fr", "translation": "Votre traduction"},
                {"string_id": 38, "language_code": "de", "translation": "Ihre Übersetzung"}
              ]
            }
            
            RETURNS:
            - Success/failure count
            - Details for any failed uploads
            - Summary of uploaded translations
            
            WORKFLOW:
            1. Get untranslated strings
            2. User provides translations
            3. Upload with this tool
            4. Check results for any failures""",
            inputSchema={
                "type": "object",
                "properties": {
                    "translations": {
                        "type": "array",
                        "description": "Array of translation objects to upload",
                        "items": {
                            "type": "object",
                            "properties": {
                                "string_id": {
                                    "type": "integer",
                                    "description": "ID of the source string"
                                },
                                "language_code": {
                                    "type": "string",
                                    "description": "Target language code (e.g., 'fr', 'es-ES')"
                                },
                                "translation": {
                                    "type": "string",
                                    "description": "Translated text"
                                }
                            },
                            "required": ["string_id", "language_code", "translation"]
                        }
                    }
                },
                "required": ["translations"]
            }
        ),
        Tool(
            name="search_string",
            description="""Search for a specific string by text and see all its translations.
            
            USE THIS WHEN:
            - User asks "is X translated?"
            - Need to check status of a specific string
            - Want to see existing translations for reference
            - Looking for a string's ID
            
            INPUT:
            - source_text: Exact text of the string to search for
            
            RETURNS:
            - String ID
            - Source text
            - Identifier and context
            - ALL existing translations by language
            - List of missing languages
            - Labels attached to the string
            
            EXAMPLE USE:
            "Is 'Hello World' translated?" -> search_string("Hello World")
            "Show me translations for scriptExample5" -> Use the identifier to find it""",
            inputSchema={
                "type": "object",
                "properties": {
                    "source_text": {
                        "type": "string",
                        "description": "Exact source text to search for"
                    }
                },
                "required": ["source_text"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls with proper routing."""
    
    # Ensure clients are initialized
    if crowdin_client is None:
        initialize_clients()
    
    if name == "get_project_info":
        return await handle_get_project_info()
    
    elif name == "get_untranslated_strings":
        return await handle_get_untranslated(arguments)
    
    elif name == "manage_labels":
        return await handle_manage_labels(arguments)
    
    elif name == "upload_translations":
        return await handle_upload_translations(arguments)
    
    elif name == "search_string":
        return await handle_search_string(arguments)
    
    else:
        raise ValueError(f"Unknown tool: {name}")


async def handle_get_project_info() -> List[TextContent]:
    """Get project information including target languages."""
    try:
        languages = crowdin_client.get_project_languages()
        
        info = {
            "project_id": config.crowdin_project_id,
            "target_languages": languages,
            "total_languages": len(languages),
            "message": "✅ Project loaded successfully"
        }
        
        return [TextContent(
            type="text",
            text=json.dumps(info, indent=2, ensure_ascii=False)
        )]
        
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"❌ Error getting project info: {str(e)}"
        )]


async def handle_get_untranslated(arguments: Dict[str, Any]) -> List[TextContent]:
    """Get untranslated strings with beautiful table format - ALWAYS returns a table."""
    try:
        # Get parameters with default to exclude 'do-not-translate' label
        limit = arguments.get("limit", 50)
        exclude_labels = arguments.get("exclude_labels", ["do-not-translate"])
        
        # Get target languages
        target_languages = crowdin_client.get_project_languages()
        
        # Get untranslated strings
        untranslated = crowdin_client.get_untranslated_strings(
            limit=limit,
            exclude_labels=exclude_labels
        )
        
        # Prepare string data
        strings_data = []
        for s in untranslated:
            strings_data.append({
                "id": s.id,
                "text": s.text[:80] + "..." if len(s.text) > 80 else s.text,
                "identifier": s.identifier,
                "context": s.context,
                "labels": s.labels,
                "existing_translations": s.existing_translations,
                "missing_languages": s.missing_languages,
                "translation_progress": s.translation_progress
            })
        
        # Build response - ALWAYS returns table, even if empty
        response = _build_translation_table(strings_data)
        
        return [TextContent(
            type="text",
            text=response
        )]
        
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"❌ Error getting untranslated strings: {str(e)}"
        )]


def _build_translation_table(strings_data: List[Dict]) -> str:
    """Build a markdown table showing translation status - ONLY table, no extras."""
    
    lines = []
    
    # If no strings, show empty table with info message
    if not strings_data:
        lines.append("| ID | Text | Identifier | Missing Languages |")
        lines.append("|----|------|------------|-------------------|")
        lines.append("| - | *All strings translated* | - | - |")
        return "\n".join(lines)
    
    # Table header
    lines.append("| ID | Text | Identifier | Missing Languages |")
    lines.append("|----|------|------------|-------------------|")
    
    # Table rows - ALL strings with ALL missing languages shown
    for string in strings_data:
        text = string['text']
        # Truncate text if too long for readability in table
        if len(text) > 50:
            text = text[:47] + "..."
        
        identifier = string['identifier']
        # Truncate identifier if too long
        if len(identifier) > 30:
            identifier = identifier[:27] + "..."
        
        # Show ALL missing languages without truncation or "and more..."
        missing = ', '.join(string['missing_languages'])
        
        lines.append(f"| {string['id']} | `{text}` | `{identifier}` | {missing} |")
    
    # Return ONLY the table - no headers, no instructions, no tips
    return "\n".join(lines)


async def handle_upload_translations(arguments: Dict[str, Any]) -> List[TextContent]:
    """Upload translations to Crowdin with detailed results."""
    try:
        translations = arguments.get("translations", [])
        
        if not translations:
            return [TextContent(
                type="text",
                text="❌ Error: No translations provided"
            )]
        
        # Upload translations in batch
        results = crowdin_client.add_translations_batch(translations)
        
        # Count successes and failures
        success_count = sum(1 for r in results if r.get("success"))
        failure_count = len(results) - success_count
        
        # Build response
        response_lines = []
        response_lines.append("# 📤 Translation Upload Results")
        response_lines.append("")
        response_lines.append(f"**Total translations:** {len(results)}")
        response_lines.append(f"**✅ Successful:** {success_count}")
        response_lines.append(f"**❌ Failed:** {failure_count}")
        response_lines.append("")
        
        if failure_count > 0:
            response_lines.append("## Failed Translations")
            response_lines.append("")
            failed_items = [r for r in results if not r.get("success")]
            for item in failed_items[:10]:  # Show first 10 failures
                response_lines.append(f"- **String ID {item['string_id']}** ({item['language_code']}): {item['error']}")
            if len(failed_items) > 10:
                response_lines.append(f"- ... and {len(failed_items) - 10} more failures")
            response_lines.append("")
        
        if success_count > 0:
            response_lines.append("## ✅ Successfully Uploaded")
            response_lines.append("")
            success_items = [r for r in results if r.get("success")]
            # Group by string_id
            by_string = {}
            for item in success_items:
                sid = item['string_id']
                if sid not in by_string:
                    by_string[sid] = []
                by_string[sid].append(item['language_code'])
            
            for string_id, langs in by_string.items():
                response_lines.append(f"- **String ID {string_id}:** {', '.join(langs)}")
            response_lines.append("")
        
        response_lines.append(f"**Status:** {'✅ All translations uploaded successfully!' if failure_count == 0 else '⚠️ Some translations failed'}")
        
        return [TextContent(
            type="text",
            text="\n".join(response_lines)
        )]
        
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"❌ Error uploading translations: {str(e)}"
        )]


async def handle_search_string(arguments: Dict[str, Any]) -> List[TextContent]:
    """Search for a string and display its translation status."""
    try:
        source_text = arguments.get("source_text", "")
        
        if not source_text:
            return [TextContent(
                type="text",
                text="❌ Error: No source text provided"
            )]
        
        # Search for the string
        result = crowdin_client.search_string(source_text)
        
        if not result:
            return [TextContent(
                type="text",
                text=f"❌ String not found: '{source_text}'"
            )]
        
        # Build beautiful response
        response_lines = []
        response_lines.append("# 🔍 String Search Results")
        response_lines.append("")
        response_lines.append(f"**String ID:** {result['id']}")
        response_lines.append(f"**Identifier:** `{result['identifier']}`")
        response_lines.append(f"**Source Text:** `{result['text']}`")
        
        if result.get('context'):
            response_lines.append(f"**Context:** {result['context']}")
        
        if result.get('labels'):
            response_lines.append(f"**Labels:** {', '.join(result['labels'])}")
        
        response_lines.append("")
        response_lines.append(f"**Translation Progress:** {result['translation_count']}/{result['total_languages']} languages")
        response_lines.append("")
        
        # Translation status table
        response_lines.append("## Translation Status")
        response_lines.append("")
        response_lines.append("| Language | Status | Translation |")
        response_lines.append("|----------|--------|-------------|")
        
        all_languages = crowdin_client.get_project_languages()
        for lang in all_languages:
            if lang in result['translations']:
                translation = result['translations'][lang]
                if len(translation) > 60:
                    translation = translation[:57] + "..."
                response_lines.append(f"| {lang} | ✅ Translated | {translation} |")
            else:
                response_lines.append(f"| {lang} | ❌ Missing | - |")
        
        response_lines.append("")
        
        if result['missing_languages']:
            response_lines.append(f"**Missing languages:** {', '.join(result['missing_languages'])}")
        else:
            response_lines.append("**✅ Fully translated in all languages!**")
        
        return [TextContent(
            type="text",
            text="\n".join(response_lines)
        )]
        
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"❌ Error searching string: {str(e)}"
        )]


async def handle_manage_labels(arguments: Dict[str, Any]) -> List[TextContent]:
    """Manage labels for strings in Crowdin."""
    try:
        action = arguments.get("action", "")
        
        if action == "list":
            # List all labels
            labels = crowdin_client.list_labels()
            
            response_lines = []
            response_lines.append("# 🏷️ Project Labels")
            response_lines.append("")
            
            if not labels:
                response_lines.append("**No labels found in project.**")
                response_lines.append("")
                response_lines.append("You can create labels by assigning them to strings:")
                response_lines.append('```')
                response_lines.append('manage_labels(action="assign", label_name="do-not-translate", string_ids=[123])')
                response_lines.append('```')
            else:
                response_lines.append("| ID | Label Name |")
                response_lines.append("|----|------------|")
                for label in labels:
                    response_lines.append(f"| {label['id']} | {label['title']} |")
                response_lines.append("")
                response_lines.append(f"**Total labels:** {len(labels)}")
            
            return [TextContent(
                type="text",
                text="\n".join(response_lines)
            )]
        
        elif action == "assign":
            # Assign label to strings
            label_name = arguments.get("label_name", "")
            string_ids = arguments.get("string_ids", [])
            
            if not label_name:
                return [TextContent(
                    type="text",
                    text="❌ Error: label_name is required for 'assign' action"
                )]
            
            if not string_ids:
                return [TextContent(
                    type="text",
                    text="❌ Error: string_ids is required for 'assign' action"
                )]
            
            # Get or create the label
            label = crowdin_client.get_or_create_label(label_name)
            
            # Assign label to strings
            crowdin_client.assign_label_to_strings(label['id'], string_ids)
            
            response_lines = []
            response_lines.append("# ✅ Label Assigned Successfully")
            response_lines.append("")
            response_lines.append(f"**Label:** `{label_name}` (ID: {label['id']})")
            response_lines.append(f"**Strings:** {len(string_ids)} strings marked")
            response_lines.append(f"**String IDs:** {', '.join(map(str, string_ids[:10]))}")
            if len(string_ids) > 10:
                response_lines.append(f"... and {len(string_ids) - 10} more")
            response_lines.append("")
            response_lines.append("**Next steps:**")
            response_lines.append("- These strings will now be filtered out by default in `get_untranslated_strings`")
            response_lines.append("- Run `get_untranslated_strings` again to see the updated list")
            
            return [TextContent(
                type="text",
                text="\n".join(response_lines)
            )]
        
        elif action == "unassign":
            # Remove label from strings
            label_name = arguments.get("label_name", "")
            string_ids = arguments.get("string_ids", [])
            
            if not label_name:
                return [TextContent(
                    type="text",
                    text="❌ Error: label_name is required for 'unassign' action"
                )]
            
            if not string_ids:
                return [TextContent(
                    type="text",
                    text="❌ Error: string_ids is required for 'unassign' action"
                )]
            
            # Find the label
            labels = crowdin_client.list_labels()
            label = next((l for l in labels if l['title'] == label_name), None)
            
            if not label:
                return [TextContent(
                    type="text",
                    text=f"❌ Error: Label '{label_name}' not found"
                )]
            
            # Remove label from strings
            crowdin_client.unassign_label_from_strings(label['id'], string_ids)
            
            response_lines = []
            response_lines.append("# ✅ Label Removed Successfully")
            response_lines.append("")
            response_lines.append(f"**Label:** `{label_name}` (ID: {label['id']})")
            response_lines.append(f"**Strings:** Label removed from {len(string_ids)} strings")
            response_lines.append(f"**String IDs:** {', '.join(map(str, string_ids[:10]))}")
            if len(string_ids) > 10:
                response_lines.append(f"... and {len(string_ids) - 10} more")
            
            return [TextContent(
                type="text",
                text="\n".join(response_lines)
            )]
        
        else:
            return [TextContent(
                type="text",
                text=f"❌ Error: Unknown action '{action}'. Use 'list', 'assign', or 'unassign'"
            )]
        
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"❌ Error managing labels: {str(e)}"
        )]


async def run_server():
    """Run the MCP server (async)."""
    # Initialize clients
    initialize_clients()
    
    # Run server with stdio transport
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


def main():
    """Entry point for the MCP server (sync wrapper)."""
    asyncio.run(run_server())


if __name__ == "__main__":
    main()