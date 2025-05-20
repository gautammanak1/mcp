"""
MCP Client Agent Package

A uagents-based agent that connects to Model Context Protocol (MCP) servers
via SSE transport and provides a chat interface for interacting with these servers.
"""

from .agent import BraveSearchAgent
from .command_parser import BraveSearchCommandParser, CommandType, ParsedCommand
from .session_manager import BraveSearchSessionManager, BraveSearchServerSession
from .brave_client import BraveSearchClient
from .result_formatter import BraveSearchResultFormatter
from .chat_handler import BraveSearchChatHandler

__version__ = "0.1.0"