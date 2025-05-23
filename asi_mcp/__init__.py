"""
MCP Client Agent Package

A uagents-based agent that connects to Model Context Protocol (MCP) servers
via SSE transport and provides a chat interface for interacting with these servers.
"""

from .agent import MCPClientAgent
from .command_parser import CommandParser, CommandType, ParsedCommand
from .session_manager import SessionManager, ServerSession
from .mcp_client import MCPClient
from .result_formatter import ResultFormatter
from .chat_handler import ChatHandler

__version__ = "0.1.0"