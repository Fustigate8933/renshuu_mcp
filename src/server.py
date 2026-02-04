import json
import logging
import asyncio
from typing import Any
from mcp.types import Tool, TextContent
from mcp.server import Server
from mcp.server.stdio import stdio_server
from .client import RenshuuClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("renshuu-mcp-logger")

server = Server("renshuu-mcp")

client: RenshuuClient | None = None

def _format_response(data: Any) -> list[TextContent]:
    """Format renshuu API response as MCP TextContent."""
    return [TextContent(type="text", text=json.dumps(data, indent=2, ensure_ascii=False))]


@server.list_tools()
async def list_tools() -> list[Tool]:
    """
    Endpoint that provides the list of tools for the MCP client.
    """
    return [
        Tool(
            name="get_profile",
            description="Get the current user's Renshuu profile including study statistics, streaks, and level progress.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_schedules",
            description="Get all of the user's study schedules. Returns schedule names, IDs, and study counts.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_schedule",
            description="Get details of a specific schedule by ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "schedule_id": {
                        "type": "string",
                        "description": "The schedule ID"
                    }
                },
                "required": ["schedule_id"]
            }
        ),
        Tool(
            name="get_schedule_terms",
            description="Get the terms (vocabulary, kanji, etc.) in a specific schedule.",
            inputSchema={
                "type": "object",
                "properties": {
                    "schedule_id": {
                        "type": "string",
                        "description": "The schedule ID"
                    },
                    "page": {
                        "type": "integer",
                        "description": "Page number (default: 1)",
                        "default": 1
                    },
                    "group": {
                        "type": "string",
                        "description": "Filter group: all, studied, notyetstudied, review_today, etc.",
                        "default": "all"
                    }
                },
                "required": ["schedule_id"]
            }
        ),
        Tool(
            name="get_lists",
            description="Get all user-created vocabulary/kanji/grammar lists.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_list",
            description="Get contents of a specific user list by ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "list_id": {
                        "type": "string",
                        "description": "The list ID"
                    },
                    "page": {
                        "type": "integer",
                        "description": "Page number (default: 1)",
                        "default": 1
                    }
                },
                "required": ["list_id"]
            }
        ),
        Tool(
            name="get_all_studied_terms",
            description="Get all terms of a specified type (vocab, grammar, kanji, sent) that the user has studied.",
            inputSchema={
                "type": "object",
                "properties": {
                    "termtype": {
                        "type": "string",
                        "description": "Type of terms: vocab, grammar, kanji, or sent"
                    },
                    "page": {
                        "type": "integer",
                        "description": "Page number (default: 1)",
                        "default": 1
                    }
                },
                "required": ["termtype"]
            }
        ),
        
        # ===== Vocab =====
        Tool(
            name="search_words",
            description="Search the Renshuu vocabulary dictionary. You can search in Japanese (kanji, hiragana) or English.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (Japanese or English)"
                    },
                    "page": {
                        "type": "integer",
                        "description": "Page number (default: 1)",
                        "default": 1
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_word",
            description="Get detailed information about a specific vocabulary word by its ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "word_id": {
                        "type": "string",
                        "description": "The word ID"
                    }
                },
                "required": ["word_id"]
            }
        ),
        Tool(
            name="add_word_to_schedule",
            description="Add a vocabulary word to a study schedule. First search for the word to get its ID, then use this tool.",
            inputSchema={
                "type": "object",
                "properties": {
                    "word_id": {
                        "type": "string",
                        "description": "The word ID to add"
                    },
                    "schedule_id": {
                        "type": "string",
                        "description": "The schedule ID to add the word to"
                    }
                },
                "required": ["word_id", "schedule_id"]
            }
        ),
        Tool(
            name="add_word_to_list",
            description="Add a vocabulary word to a user list.",
            inputSchema={
                "type": "object",
                "properties": {
                    "word_id": {
                        "type": "string",
                        "description": "The word ID to add"
                    },
                    "list_id": {
                        "type": "string",
                        "description": "The list ID to add the word to"
                    }
                },
                "required": ["word_id", "list_id"]
            }
        ),
        Tool(
            name="remove_word_from_schedule",
            description="Remove a vocabulary word from a study schedule.",
            inputSchema={
                "type": "object",
                "properties": {
                    "word_id": {
                        "type": "string",
                        "description": "The word ID to remove"
                    },
                    "schedule_id": {
                        "type": "string",
                        "description": "The schedule ID to remove the word from"
                    }
                },
                "required": ["word_id", "schedule_id"]
            }
        ),
        Tool(
            name="remove_word_from_list",
            description="Remove a vocabulary word from a user list.",
            inputSchema={
                "type": "object",
                "properties": {
                    "word_id": {
                        "type": "string",
                        "description": "The word ID to remove"
                    },
                    "list_id": {
                        "type": "string",
                        "description": "The list ID to remove the word from"
                    }
                },
                "required": ["word_id", "list_id"]
            }
        ),
        Tool(
            name="add_word_by_schedule_name",
            description="Add a word to a schedule by schedule name. This is a convenience tool that searches for the schedule by name, searches for the word, and adds it in a single operation. This endpoint MUST be used for add-word requests.",
            inputSchema={
                "type": "object",
                "properties": {
                    "schedule_name": {
                        "type": "string",
                        "description": "The name of the schedule to add the word to"
                    },
                    "word": {
                        "type": "string",
                        "description": "The word to search for and add (Japanese or English)"
                    }
                },
                "required": ["schedule_name", "word"]
            }
        ),
        
        # ===== Kanji =====
        Tool(
            name="search_kanji",
            description="Search for kanji by character or meaning.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (kanji character or English meaning)"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_kanji",
            description="Get detailed information about a specific kanji character.",
            inputSchema={
                "type": "object",
                "properties": {
                    "kanji": {
                        "type": "string",
                        "description": "The kanji character"
                    }
                },
                "required": ["kanji"]
            }
        ),
        Tool(
            name="add_kanji_to_schedule",
            description="Add a kanji to a study schedule.",
            inputSchema={
                "type": "object",
                "properties": {
                    "kanji": {
                        "type": "string",
                        "description": "The kanji character to add"
                    },
                    "schedule_id": {
                        "type": "string",
                        "description": "The schedule ID"
                    }
                },
                "required": ["kanji", "schedule_id"]
            }
        ),
        Tool(
            name="add_kanji_to_list",
            description="Add a kanji to a user list.",
            inputSchema={
                "type": "object",
                "properties": {
                    "kanji": {
                        "type": "string",
                        "description": "The kanji character to add"
                    },
                    "list_id": {
                        "type": "string",
                        "description": "The list ID"
                    }
                },
                "required": ["kanji", "list_id"]
            }
        ),
        Tool(
            name="remove_kanji_from_schedule",
            description="Remove a kanji from a study schedule.",
            inputSchema={
                "type": "object",
                "properties": {
                    "kanji": {
                        "type": "string",
                        "description": "The kanji character to remove"
                    },
                    "schedule_id": {
                        "type": "string",
                        "description": "The schedule ID"
                    }
                },
                "required": ["kanji", "schedule_id"]
            }
        ),
        Tool(
            name="remove_kanji_from_list",
            description="Remove a kanji from a user list.",
            inputSchema={
                "type": "object",
                "properties": {
                    "kanji": {
                        "type": "string",
                        "description": "The kanji character to remove"
                    },
                    "list_id": {
                        "type": "string",
                        "description": "The list ID"
                    }
                },
                "required": ["kanji", "list_id"]
            }
        ),
        
        # ====== Grammar ======
        
        Tool(
            name="add_grammar_to_list",
            description="Add a grammar point to a user list.",
            inputSchema={
                "type": "object",
                "properties": {
                    "grammar_id": {
                        "type": "string",
                        "description": "The grammar ID to add"
                    },
                    "list_id": {
                        "type": "string",
                        "description": "The list ID"
                    }
                },
                "required": ["grammar_id", "list_id"]
            }
        ),
        Tool(
            name="remove_grammar_from_schedule",
            description="Remove a grammar point from a study schedule.",
            inputSchema={
                "type": "object",
                "properties": {
                    "grammar_id": {
                        "type": "string",
                        "description": "The grammar ID to remove"
                    },
                    "schedule_id": {
                        "type": "string",
                        "description": "The schedule ID"
                    }
                },
                "required": ["grammar_id", "schedule_id"]
            }
        ),
        Tool(
            name="remove_grammar_from_list",
            description="Remove a grammar point from a user list.",
            inputSchema={
                "type": "object",
                "properties": {
                    "grammar_id": {
                        "type": "string",
                        "description": "The grammar ID to remove"
                    },
                    "list_id": {
                        "type": "string",
                        "description": "The list ID"
                    }
                },
                "required": ["grammar_id", "list_id"]
            }
        ),
        Tool(
            name="search_grammar",
            description="Search the grammar dictionary.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (Japanese or English)"
                    },
                    "page": {
                        "type": "integer",
                        "description": "Page number (default: 1)",
                        "default": 1
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_grammar",
            description="Get detailed information about a specific grammar point.",
            inputSchema={
                "type": "object",
                "properties": {
                    "grammar_id": {
                        "type": "string",
                        "description": "The grammar ID"
                    }
                },
                "required": ["grammar_id"]
            }
        ),
        Tool(
            name="add_grammar_to_schedule",
            description="Add a grammar point to a study schedule.",
            inputSchema={
                "type": "object",
                "properties": {
                    "grammar_id": {
                        "type": "string",
                        "description": "The grammar ID to add"
                    },
                    "schedule_id": {
                        "type": "string",
                        "description": "The schedule ID"
                    }
                },
                "required": ["grammar_id", "schedule_id"]
            }
        ),
        
        # ===== Sentences =====
        Tool(
            name="search_sentences",
            description="Search for example sentences in Japanese or English.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_sentences_for_word",
            description="Get example sentences that use a specific vocabulary word.",
            inputSchema={
                "type": "object",
                "properties": {
                    "word_id": {
                        "type": "string",
                        "description": "The word ID"
                    }
                },
                "required": ["word_id"]
            }
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """
    Function that executes the tool calls
    """
    global client

    if client is None:
        return _format_response({"error": "Client not initialized."})
    
    try:
        # ===== User & Lists =====
        if name == "get_profile":
            result = await client.get_profile()
        elif name == "get_schedules":
            result = await client.get_schedules()
        elif name == "get_schedule":
            result = await client.get_schedule(arguments["schedule_id"])
        elif name == "get_schedule_terms":
            result = await client.get_schedule_terms(
                arguments["schedule_id"],
                pg=arguments.get("page", 1),
                group=arguments.get("group", "all")
            )
        elif name == "get_lists":
            result = await client.get_lists()
        elif name == "get_list":
            result = await client.get_list(
                arguments["list_id"],
                pg=arguments.get("page", 1)
            )
        elif name == "get_all_studied_terms":
            result = await client.get_all_studied_terms(
                arguments["termtype"],
                pg=arguments.get("page", 1)
            )

        # ===== Vocab =====
        elif name == "search_words":
            result = await client.search_words(
                arguments["query"],
                pg=arguments.get("page", 1)
            )
        elif name == "get_word":
            result = await client.get_word(arguments["word_id"])
        elif name == "add_word_to_schedule":
            result = await client.add_word_to_schedule(
                arguments["word_id"],
                arguments["schedule_id"]
            )
        elif name == "add_word_to_list":
            result = await client.add_word_to_list(
                arguments["word_id"],
                arguments["list_id"]
            )
        elif name == "remove_word_from_schedule":
            result = await client.remove_word_from_schedule(
                arguments["word_id"],
                arguments["schedule_id"]
            )
        elif name == "remove_word_from_list":
            result = await client.remove_word_from_list(
                arguments["word_id"],
                arguments["list_id"]
            )
        elif name == "add_word_by_schedule_name":
            result = await client.add_word_by_schedule_name(
                arguments["schedule_name"],
                arguments["word"]
            )
        elif name == "add_word_by_list_name":
            result = await client.add_word_by_list_name(
                arguments["list_name"],
                arguments["word"]
            )

        # ===== Kanji =====
        elif name == "search_kanji":
            result = await client.search_kanji(arguments["query"])
        elif name == "get_kanji":
            result = await client.get_kanji(arguments["kanji"])
        elif name == "add_kanji_to_schedule":
            result = await client.add_kanji_to_schedule(
                arguments["kanji"],
                arguments["schedule_id"]
            )
        elif name == "add_kanji_to_list":
            result = await client.add_kanji_to_list(
                arguments["kanji"],
                arguments["list_id"]
            )
        elif name == "remove_kanji_from_schedule":
            result = await client.remove_kanji_from_schedule(
                arguments["kanji"],
                arguments["schedule_id"]
            )
        elif name == "remove_kanji_from_list":
            result = await client.remove_kanji_from_list(
                arguments["kanji"],
                arguments["list_id"]
            )

        # ===== Grammar =====
        elif name == "search_grammar":
            result = await client.search_grammar(
                arguments["query"],
                pg=arguments.get("page", 1)
            )
        elif name == "get_grammar":
            result = await client.get_grammar(arguments["grammar_id"])
        elif name == "add_grammar_to_schedule":
            result = await client.add_grammar_to_schedule(
                arguments["grammar_id"],
                arguments["schedule_id"]
            )
        elif name == "add_grammar_to_list":
            result = await client.add_grammar_to_list(
                arguments["grammar_id"],
                arguments["list_id"]
            )
        elif name == "remove_grammar_from_schedule":
            result = await client.remove_grammar_from_schedule(
                arguments["grammar_id"],
                arguments["schedule_id"]
            )
        elif name == "remove_grammar_from_list":
            result = await client.remove_grammar_from_list(
                arguments["grammar_id"],
                arguments["list_id"]
            )

        # ===== Sentences =====
        elif name == "search_sentences":
            result = await client.search_sentences(arguments["query"])
        elif name == "get_sentences_for_word":
            result = await client.get_sentences_for_word(arguments["word_id"])
        else:
            result = {"error": f"Unknown tool: {name}"}

        return _format_response(result)
    except Exception as exc:
        logger.exception(f"Error calling tool {name}")
        return _format_response({"error": str(exc)})


async def main() -> None:
    """
    Entrypoint for the MCP server.
    """
    global client

    logger.info("Starting renshuu MCP server")
    async with RenshuuClient() as c:
        client = c
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(),
            )

if __name__ == "__main__":
    asyncio.run(main())
