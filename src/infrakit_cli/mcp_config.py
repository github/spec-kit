"""
MCP (Model Context Protocol) recipe definitions for infrakit-cli.
Each recipe describes a pre-configured MCP server installable into
a supported agent's config file.
"""

MCP_RECIPES = {
    "context7": {
        "display_name": "Context7 — Up-to-date library docs",
        "description": "Provides current library documentation via Upstash Context7",
        "type": "stdio",
        "command": "npx",
        "args": ["-y", "@upstash/context7-mcp@latest"],
        "tools": ["resolve-library-id", "get-library-docs"],
        "usage": "Ask agent to 'use context7' when looking up library/framework docs",
    },
    "deepwiki": {
        "display_name": "DeepWiki — GitHub repo deep research",
        "description": "Deep research into GitHub repositories via SSE transport",
        "type": "sse",
        "url": "https://mcp.deepwiki.com/mcp",
        "tools": ["ask_question", "read_wiki_structure", "read_wiki_contents"],
        "usage": "Ask agent to 'use deepwiki' to research a GitHub repo in depth",
    },
    "aws-best-practices": {
        "display_name": "AWS Best Practices — AWS docs & best practices",
        "description": "Access AWS documentation and best practices via awslabs server",
        "type": "stdio",
        "command": "uvx",
        "args": ["awslabs.aws-documentation-mcp-server@latest"],
        "tools": ["search_documentation", "read_documentation", "recommend"],
        "usage": "Agent will use automatically when generating AWS infrastructure",
    },
    "microsoft-learn": {
        "display_name": "Microsoft Learn — Microsoft & Azure docs",
        "description": "Access Microsoft and Azure documentation via Microsoft Learn MCP",
        "type": "stdio",
        "command": "npx",
        "args": ["-y", "@microsoft/mcp-microsoft-learn@latest"],
        "tools": ["microsoft_docs_search", "microsoft_docs_fetch", "microsoft_code_sample_search"],
        "usage": "Agent will use automatically when generating Azure infrastructure",
    },
}
