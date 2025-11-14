# Translation MCP Server

AI-powered translation automation for Crowdin projects. Works with **any AI client** (Claude Desktop, ChatGPT, Cursor, etc).

---

## Features

- 🤖 **Universal AI Client** - works with Claude Desktop, ChatGPT, Cursor, and any MCP-compatible AI
- 🌍 **Dynamic Language Support** - automatically detects target languages from your Crowdin project
- 🎯 **Smart Classification** - identifies proper nouns, brands, and language names to preserve
- ✅ **AI-Powered Translation** - uses your AI client's subscription (no separate API key needed)
- 📤 **Automated Upload** - directly uploads translations to Crowdin

---

## How It Works

```
1. You: "Translate untranslated strings"
   ↓
2. MCP: Fetches strings from Crowdin + provides classification
   ↓
3. AI Client: Translates strings (using YOUR subscription)
   ↓
4. MCP: Uploads translations back to Crowdin
```

**No separate API keys required!** Uses your existing AI client subscription.

---

## Installation

### Method 1: Direct from GitHub (Recommended for users)

**No cloning, no setup - just one configuration!**

This method uses `uvx` to automatically install and run from GitHub.

**Prerequisites:**
- Install `uv`: `brew install uv` (macOS) or `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Crowdin account with API token

**Configuration:** (see [Configuration](#configuration) section below)

### Method 2: Local Development

**For developers who want to modify the code.**

**Prerequisites:**
- Python 3.10 or higher
- Crowdin account with API token

**Setup:**

1. **Clone repository:**
```bash
git clone https://github.com/yourusername/translation-mcp
cd translation-mcp
```

2. **Create virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install mcp httpx pydantic
```

---

## Configuration

### Method 1: Using uvx (from GitHub)

**For Claude Desktop:**

Edit: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "translation-mcp": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/yourusername/translation-mcp",
        "translation-mcp"
      ],
      "env": {
        "CROWDIN_API_TOKEN": "your_crowdin_token_here",
        "CROWDIN_PROJECT_ID": "your_project_id_here"
      }
    }
  }
}
```

**For Cursor:**

```json
{
  "mcp": {
    "servers": {
      "translation-mcp": {
        "command": "uvx",
        "args": [
          "--from",
          "git+https://github.com/yourusername/translation-mcp",
          "translation-mcp"
        ],
        "env": {
          "CROWDIN_API_TOKEN": "your_token",
          "CROWDIN_PROJECT_ID": "your_project_id"
        }
      }
    }
  }
}
```

**Benefits:**
- ✅ No repository cloning needed
- ✅ Automatic updates on restart
- ✅ No virtual environment setup
- ✅ Python installed automatically by uv

---

### Method 2: Local Installation

**For Claude Desktop:**

Edit: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "translation-mcp": {
      "command": "/absolute/path/to/translation-mcp/venv/bin/python",
      "args": ["-m", "translation_mcp.server"],
      "env": {
        "CROWDIN_API_TOKEN": "your_crowdin_token_here",
        "CROWDIN_PROJECT_ID": "your_project_id_here"
      }
    }
  }
}
```

**For Cursor:**

Add to Cursor settings (similar format):

```json
{
  "mcp": {
    "servers": {
      "translation-mcp": {
        "command": "/absolute/path/to/translation-mcp/venv/bin/python",
        "args": ["-m", "translation_mcp.server"],
        "env": {
          "CROWDIN_API_TOKEN": "your_token",
          "CROWDIN_PROJECT_ID": "your_project_id"
        }
      }
    }
  }
}
```

**For ChatGPT (with MCP support):**

Similar configuration - check ChatGPT's MCP documentation.

---

## Getting Your Tokens

### Crowdin API Token

1. Go to: https://crowdin.com/settings#api-key
2. Click "New Token"
3. Name: "Translation MCP"
4. Scopes: `project.read`, `string.read`, `translation.write`
5. Copy the token

### Crowdin Project ID

1. Open your Crowdin project
2. Look at URL: `https://crowdin.com/project/your-project/12345`
3. The number `12345` is your Project ID

---

## Usage

Once configured, use natural language commands in your AI client:

### Basic Commands

```
"Get project info"
"Show untranslated strings"
"Translate all untranslated strings"
```

### Advanced Commands

```
"Translate strings for French and German only"
"Get 20 untranslated strings"
"Show me untranslated strings and translate them"
```

---

## How Translation Works

### 1. Fetching Strings

AI calls: `get_untranslated_strings()`

MCP returns:
- List of untranslated strings
- Target languages from your Crowdin project
- String classification (regular/name/brand/language)
- Translation instructions

### 2. AI Translates

Your AI client (Claude/ChatGPT/Cursor) translates the strings based on:
- String type (regular text vs names/brands)
- Context and identifier
- Target languages
- Professional tone for POS system

### 3. Uploading Translations

AI calls: `upload_translations(translations)`

MCP uploads translations to Crowdin.

---

## String Classification

MCP automatically classifies strings to ensure proper translation:

| Type | Example | Treatment |
|------|---------|-----------|
| **Regular** | "Welcome to app" | Translate naturally |
| **Language Name** | "English", "Español" | Keep original |
| **Proper Name** | "Steve Jobs" | Keep original |
| **Brand** | "iPhone", "Google" | Keep original |
| **Technical** | "API_KEY" | Evaluate context |

---

## Available MCP Tools

### `get_project_info`

Get Crowdin project information and target languages.

**Returns:**
```json
{
  "project_id": "12345",
  "target_languages": ["fr", "de", "es", "it", "pt", "zh-CN"],
  "total_languages": 6
}
```

### `get_untranslated_strings`

Get untranslated strings with classification and instructions.

**Parameters:**
- `languages` (optional): Specific language codes
- `limit` (optional): Max strings to fetch (default: 50)

**Returns:**
```json
{
  "strings": [
    {
      "id": 123,
      "text": "Welcome",
      "identifier": "app.welcome",
      "type": "regular",
      "translation_note": "Translate naturally"
    }
  ],
  "target_languages": ["fr", "de"],
  "instructions": "..."
}
```

### `upload_translations`

Upload translated strings to Crowdin.

**Parameters:**
```json
{
  "translations": [
    {
      "string_id": 123,
      "language_code": "fr",
      "translation": "Bienvenue"
    }
  ]
}
```

**Returns:**
```json
{
  "total": 10,
  "successful": 10,
  "failed": 0,
  "message": "Uploaded 10/10 translations successfully"
}
```

---

## Troubleshooting

### MCP Not Showing in AI Client

1. Check configuration file path
2. Verify JSON is valid (use https://jsonlint.com/)
3. Ensure absolute paths are used
4. Restart AI client completely

### "Module not found: translation_mcp"

Verify virtual environment:
```bash
ls /path/to/translation-mcp/venv/bin/
```

If missing, recreate:
```bash
python3 -m venv venv
source venv/bin/activate
pip install mcp httpx pydantic
```

### "API Error: Invalid token"

- Verify token in configuration (no extra spaces)
- Check token hasn't expired
- Confirm token has correct scopes in Crowdin

### No Untranslated Strings Found

- Verify you're checking the correct Crowdin project
- Check if strings actually need translation
- Try with specific language: `"Get untranslated strings for French"`

---

## Development

### Project Structure

```
translation-mcp/
├── src/translation_mcp/
│   ├── server.py           # MCP server
│   ├── crowdin_client.py   # Crowdin API client
│   ├── classifier.py       # String classifier
│   └── config.py           # Configuration
├── pyproject.toml          # Dependencies
└── README.md
```

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black src/
ruff check src/
```

---

## Why This Approach?

**Traditional approach** (what we DON'T do):
```
MCP → Anthropic API → Translation → MCP → Crowdin
           ↑
    Separate API key + billing
```

**Our approach** (what we DO):
```
AI Client (your subscription) → MCP → Crowdin
                ↑
    Uses YOUR existing subscription
```

**Benefits:**
- ✅ No separate API costs
- ✅ Works with any AI client
- ✅ Simpler configuration
- ✅ Uses your existing AI subscription

---

## Cost

- **Crowdin API**: Free (within your Crowdin plan)
- **AI Translation**: Included in your AI client subscription (Claude Pro, ChatGPT Plus, etc)
- **No additional costs!**

---

## Security

- Tokens passed via MCP environment variables
- No tokens stored in files
- MCP runs locally on your machine
- Direct API calls to Crowdin only

---

## License

MIT

---

## Contributing

Issues and pull requests welcome!

---

## Support

Having issues? Create an issue on GitHub with:
- Your AI client (Claude Desktop, Cursor, etc)
- Error messages
- Configuration (with tokens removed)
