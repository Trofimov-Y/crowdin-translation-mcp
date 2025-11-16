# Translation MCP Server

AI-powered translation workflow automation for Crowdin projects. Works with **any MCP-compatible AI client** (Claude Desktop, Cline, Zed, etc).

[![MCP](https://img.shields.io/badge/MCP-Compatible-blue)](https://modelcontextprotocol.io)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🎯 What It Does

This MCP server connects your AI assistant directly to Crowdin, enabling:
- 🔍 **Smart string filtering** with label-based organization
- 📊 **Table-based workflow** for easy translation review
- 🏷️ **Label management** to mark strings as do-not-translate
- 🔄 **Batch translations** with detailed upload feedback
- 🎯 **Precise string search** to check translation status

**No separate API keys needed** - uses your existing AI subscription for translation!

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or higher (or just install `uv`)
- Crowdin account with API token
- MCP-compatible AI client (Claude Desktop, Cline, Zed, etc)

### Installation

**Option 1: Using uvx (Recommended - No Setup Required)**

Just add to your AI client's config - `uvx` automatically handles installation:

```json
{
  "mcpServers": {
    "translation-mcp": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/Trofimov-Y/crowdin-translation-mcp",
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

**Benefits:**
- ✅ No repository cloning needed
- ✅ No virtual environment setup
- ✅ Automatic updates on restart
- ✅ Works out of the box

**Option 2: Local Development**

For developers who want to modify the code:

```bash
# Clone repository
git clone https://github.com/Trofimov-Y/crowdin-translation-mcp
cd translation-mcp

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
```

Then configure with absolute path:

```json
{
  "mcpServers": {
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
```

---

## 🔑 Getting Your Credentials

### Crowdin API Token

1. Go to: https://crowdin.com/settings#api-key
2. Click "New Token"
3. Name: "Translation MCP"
4. Required scopes:
   - `project.read` - Read project info
   - `string.read` - Read source strings
   - `translation.write` - Upload translations
   - `label.read` - Read labels
   - `label.write` - Manage labels
5. Copy the token

### Crowdin Project ID

1. Open your Crowdin project
2. Look at URL: `https://crowdin.com/project/your-project/12345`
3. The number `12345` is your Project ID

---

## 📝 Configuration

### Claude Desktop

Location: `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)  
Location: `%APPDATA%\Claude\claude_desktop_config.json` (Windows)

```json
{
  "mcpServers": {
    "translation-mcp": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/Trofimov-Y/crowdin-translation-mcp",
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

### Cline (VSCode Extension)

Add to Cline MCP settings:

```json
{
  "translation-mcp": {
    "command": "uvx",
    "args": [
      "--from",
      "git+https://github.com/Trofimov-Y/crowdin-translation-mcp",
      "translation-mcp"
    ],
    "env": {
      "CROWDIN_API_TOKEN": "your_token",
      "CROWDIN_PROJECT_ID": "your_project_id"
    }
  }
}
```

### Zed Editor

Add to Zed settings:

```json
{
  "context_servers": {
    "translation-mcp": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/Trofimov-Y/crowdin-translation-mcp",
        "translation-mcp"
      ],
      "env": {
        "CROWDIN_API_TOKEN": "your_token",
        "CROWDIN_PROJECT_ID": "your_project_id"
      }
    }
  }
}
```

---

## 💡 Usage Examples

Once configured, use natural language commands in your AI assistant:

```
"Show me untranslated strings"
"Get project languages"
"Mark strings 274, 284, 300 as do not translate"
"Search for string 'Welcome'"
"Translate the untranslated strings to French and German"
```

### Typical Workflow

1. **Check what needs translation:**
   ```
   "Show untranslated strings"
   ```
   
2. **Mark names/brands that shouldn't be translated:**
   ```
   "Mark strings 36, 38, 42 as do-not-translate"
   ```

3. **Get filtered list:**
   ```
   "Show untranslated strings again"
   ```

4. **Translate and upload:**
   ```
   "Translate these strings to all missing languages and upload"
   ```

---

## 🛠️ Available MCP Tools

### `get_project_info`

Get Crowdin project information and target languages.

**Use when:**
- Starting a new translation session
- Need to know what languages are in the project
- Want to verify project configuration

**Returns:**
```json
{
  "project_id": "12345",
  "target_languages": ["fr", "de", "es-ES", "it", "pt-BR"],
  "total_languages": 5,
  "message": "✅ Project loaded successfully"
}
```

---

### `get_untranslated_strings`

Get strings that need translation in a **table format**.

**Use when:**
- User asks "what needs to be translated?"
- Want to see translation progress
- Need to find strings missing in specific languages

**Parameters:**
- `limit` (optional): Max strings to return (default: 35, max: 500)
- `exclude_labels` (optional): Labels to filter out (default: `["do-not-translate"]`)

**Returns:**

A markdown table with ALL untranslated strings:

```
| ID  | Text                  | Identifier       | Missing Languages |
|-----|-----------------------|------------------|-------------------|
| 36  | `Routine`             | `routine`        | fr, de, it        |
| 38  | `{numMinutes} min`    | `numMinutes`     | fr, es-ES, it     |
| 42  | `Welcome to app`      | `app.welcome`    | fr, de            |
```

**Important:** This tool ALWAYS returns a table, even if empty.

**Label filtering:**
- By default, excludes strings with `do-not-translate` label
- Use `exclude_labels=[]` to see ALL strings including marked ones

**Examples:**
```
"Show untranslated strings"                    → Returns filtered table
"Get all untranslated including marked ones"   → Use exclude_labels=[]
"Show 100 untranslated strings"                → Use limit=100
```

---

### `manage_labels`

Manage labels for strings in Crowdin (mark as do-not-translate, organize strings).

**Use when:**
- Need to mark strings as "do not translate"
- Want to organize strings with custom labels
- Need to see available labels
- Want to remove labels from strings

**Actions:**

#### 1. List all labels

```json
{
  "action": "list"
}
```

Returns all labels in the project.

#### 2. Assign label to strings

```json
{
  "action": "assign",
  "label_name": "do-not-translate",
  "string_ids": [274, 284, 300]
}
```

Creates label if it doesn't exist and assigns it to specified strings.

#### 3. Remove label from strings

```json
{
  "action": "unassign",
  "label_name": "do-not-translate",
  "string_ids": [284]
}
```

**Common workflow:**
1. See untranslated strings
2. Notice some are brand names or proper nouns
3. Mark them: `"Mark strings 274, 284, 300 as do not translate"`
4. Next `get_untranslated_strings` call will filter them out automatically

---

### `upload_translations`

Upload translated strings to Crowdin in batch.

**Use when:**
- User provides translations ready to upload
- After translating strings from `get_untranslated_strings`
- Need to add multiple translations at once

**Important:**
- Only upload translations for languages shown as MISSING
- Don't upload for languages already translated
- Each translation needs: string_id, language_code, translation text

**Input format:**
```json
{
  "translations": [
    {
      "string_id": 36,
      "language_code": "fr",
      "translation": "Routine"
    },
    {
      "string_id": 36,
      "language_code": "de",
      "translation": "Routine"
    },
    {
      "string_id": 38,
      "language_code": "fr",
      "translation": "{numMinutes} min"
    }
  ]
}
```

**Returns:**
```
# 📤 Translation Upload Results

**Total translations:** 3
**✅ Successful:** 3
**❌ Failed:** 0

## ✅ Successfully Uploaded

- **String ID 36:** fr, de
- **String ID 38:** fr

**Status:** ✅ All translations uploaded successfully!
```

---

### `search_string`

Search for a specific string by text and see all its translations.

**Use when:**
- User asks "is X translated?"
- Need to check status of a specific string
- Want to see existing translations for reference
- Looking for a string's ID

**Input:**
```json
{
  "source_text": "Welcome"
}
```

**Returns:**
```
# 🔍 String Search Results

**String ID:** 123
**Identifier:** `app.welcome`
**Source Text:** `Welcome`
**Translation Progress:** 3/5 languages

## Translation Status

| Language | Status         | Translation |
|----------|----------------|-------------|
| fr       | ✅ Translated  | Bienvenue   |
| de       | ✅ Translated  | Willkommen  |
| es-ES    | ✅ Translated  | Bienvenido  |
| it       | ❌ Missing     | -           |
| pt-BR    | ❌ Missing     | -           |

**Missing languages:** it, pt-BR
```

---

## 🏷️ Label System

The label system helps organize and filter strings:

### Default Behavior

- `get_untranslated_strings` **automatically excludes** strings with `do-not-translate` label
- This filters out names, brands, technical terms you've already marked

### Workflow

1. **Get untranslated strings** (auto-filtered)
2. **Review the table**
3. **Mark names/brands:**
   ```
   "Mark strings 36, 42 as do-not-translate"
   ```
4. **Get updated list** (marked strings disappear)
5. **Translate remaining strings**

### Custom Labels

You can create any labels you want:
- `do-not-translate` - Skip these strings
- `reviewed` - Mark as reviewed
- `context-needed` - Needs more context
- `technical-term` - Technical terminology

---

## 📂 Project Structure

```
translation-mcp/
├── src/translation_mcp/
│   ├── __init__.py          # Package initialization
│   ├── server.py            # MCP server implementation
│   ├── crowdin_client.py    # Crowdin API client (using official SDK)
│   └── config.py            # Configuration management
├── pyproject.toml           # Project dependencies & metadata
├── README.md                # This file
├── .gitignore               # Git ignore rules
└── claude_desktop_config_uvx.json  # Example configuration
```

---

## 🔧 Troubleshooting

### MCP Server Not Appearing

1. **Check configuration file path:**
   - macOS Claude: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows Claude: `%APPDATA%\Claude\claude_desktop_config.json`

2. **Verify JSON syntax:**
   - Use https://jsonlint.com/ to validate
   - Ensure no trailing commas
   - Check all quotes are correct

3. **Restart AI client completely:**
   - Quit application (not just close window)
   - Restart application

### "Module not found: translation_mcp"

**For uvx users:**
- `uv` should automatically handle installation
- Try: `uvx --from git+https://github.com/Trofimov-Y/crowdin-translation-mcp translation-mcp --help`
- If fails, ensure `uv` is installed: `curl -LsSf https://astral.sh/uv/install.sh | sh`

**For local installation:**
```bash
# Verify virtual environment has packages
ls /path/to/translation-mcp/venv/lib/python*/site-packages/

# If missing, reinstall
pip install -e .
```

### "API Error: Invalid token"

- Verify token in configuration (no extra spaces)
- Check token hasn't expired in Crowdin settings
- Confirm token has all required scopes:
  - `project.read`
  - `string.read`
  - `translation.write`
  - `label.read`
  - `label.write`

### Table Not Showing

This should never happen now! The tool ALWAYS returns a table.

If you see text instead:
1. Check you're using the latest version
2. Report as bug with example

### "No untranslated strings found" (but there are)

- Verify correct Crowdin project ID
- Check if strings are marked as `do-not-translate`
- Try: `"Get all untranslated including marked ones"` to see everything

---

## 🧪 Development

### Setup Development Environment

```bash
git clone https://github.com/Trofimov-Y/crowdin-translation-mcp
cd translation-mcp

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install with dev dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
# Format code
black src/

# Check style
ruff check src/
```

### Manual Testing

```bash
# Test that MCP server starts
python -m translation_mcp.server

# Should show MCP initialization messages
```

---

## 🔐 Security

- **Tokens passed via environment variables** - never hardcoded
- **No tokens stored in files** - only in MCP config
- **MCP runs locally** - all processing on your machine
- **Direct API calls** - only to Crowdin, no intermediaries

---

## 💰 Cost

- **Crowdin API:** Free (within your Crowdin plan limits)
- **AI Translation:** Included in your AI client subscription
- **MCP Server:** Free and open source
- **Total additional cost:** $0

---

## 🤝 Contributing

Contributions welcome! Please feel free to submit a Pull Request.

### Areas for Contribution

- Additional language detection
- Bulk operations optimization
- UI for easier configuration
- Additional Crowdin features
- Better error messages

---

## 📄 License

MIT License - see LICENSE file for details

---

## 🐛 Support

Having issues?

1. Check this README first
2. Look at closed issues on GitHub
3. Open a new issue with:
   - Your AI client (Claude Desktop, Cline, etc)
   - Error messages (with tokens removed!)
   - Configuration (with tokens removed!)
   - Steps to reproduce

---

## 🙏 Acknowledgments

- Built with [Anthropic's MCP SDK](https://github.com/anthropics/mcp)
- Uses [official Crowdin API client](https://github.com/crowdin/crowdin-api-client-python)
- Inspired by the need for better translation workflows

---

## 📊 Version History

- **2.0.0** - Major refactor with official Crowdin SDK, label system, improved prompts
- **0.1.0** - Initial release

---

**Made with ❤️ for better translation workflows**
