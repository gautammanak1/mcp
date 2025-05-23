"""
Command Parser - Parse structured commands from chat messages

This module contains the CommandParser class that parses structured commands
from chat messages, validates command syntax, and extracts parameters.
"""

import json
import re
import shlex
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Union


class CommandType(Enum):
    """Enum for supported command types."""
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    LIST = "list"
    CALL = "call"
    SHORTHAND = "shorthand"
    STATUS = "status"
    HELP = "help"
    SCHEMA = "schema"
    UNKNOWN = "unknown"


class ParsedCommand:
    """Class representing a parsed command."""
    
    def __init__(
        self,
        command_type: CommandType,
        args: List[str] = None,
        kwargs: Dict[str, Any] = None,
        raw_command: str = ""
    ):
        """
        Initialize a parsed command.
        
        Args:
            command_type: Type of the command
            args: Positional arguments
            kwargs: Keyword arguments
            raw_command: Raw command string
        """
        self.command_type = command_type
        self.args = args or []
        self.kwargs = kwargs or {}
        self.raw_command = raw_command
    
    def __str__(self) -> str:
        """String representation of the parsed command."""
        return f"ParsedCommand(type={self.command_type.value}, args={self.args}, kwargs={self.kwargs})"


class CommandParser:
    """Parser for structured commands in chat messages."""
    
    COMMAND_PREFIX = "!"
    
    def __init__(self):
        """Initialize the command parser."""
        # Command syntax patterns
        self.command_patterns = {
            CommandType.CONNECT: r"^!connect\s+(.+)$",
            CommandType.DISCONNECT: r"^!disconnect$",
            CommandType.LIST: r"^!list$",
            CommandType.CALL: r"^!call\s+(\S+)\s+(.+)$",
            CommandType.SHORTHAND: r"^!shorthand\s+(\S+)\s+(.+)$",
            CommandType.STATUS: r"^!status$",
            CommandType.HELP: r"^!help(?:\s+(\S+))?$",
            CommandType.SCHEMA: r"^!schema\s+(\S+)$",
        }
    
    def is_command(self, message: str) -> bool:
        """
        Check if a message is a command.
        
        Args:
            message: The message to check
            
        Returns:
            True if the message is a command, False otherwise
        """
        return message.strip().startswith(self.COMMAND_PREFIX)
    
    def parse_command(self, message: str) -> ParsedCommand:
        """
        Parse a command from a message.
        
        Args:
            message: The message to parse
            
        Returns:
            A ParsedCommand object
        """
        message = message.strip()
        
        if not self.is_command(message):
            return ParsedCommand(CommandType.UNKNOWN, raw_command=message)
        
        # Extract command type
        parts = message.split(maxsplit=1)
        cmd = parts[0][1:]  # Remove the prefix
        
        try:
            command_type = CommandType(cmd)
        except ValueError:
            return ParsedCommand(CommandType.UNKNOWN, raw_command=message)
        
        # Parse based on command type
        if command_type == CommandType.CONNECT:
            return self._parse_connect_command(message)
        elif command_type == CommandType.CALL:
            return self._parse_call_command(message)
        elif command_type == CommandType.SHORTHAND:
            return self._parse_shorthand_command(message)
        elif command_type == CommandType.HELP:
            return self._parse_help_command(message)
        elif command_type == CommandType.SCHEMA:
            return self._parse_schema_command(message)
        elif command_type in [CommandType.DISCONNECT, CommandType.LIST, CommandType.STATUS]:
            return ParsedCommand(command_type, raw_command=message)
        else:
            return ParsedCommand(CommandType.UNKNOWN, raw_command=message)
    
    def _parse_connect_command(self, message: str) -> ParsedCommand:
        """
        Parse a connect command.
        
        Format: !connect [url] [--token TOKEN] [--token-env-var VAR_NAME]
        
        Args:
            message: The command message
            
        Returns:
            A ParsedCommand object
        """
        match = re.match(self.command_patterns[CommandType.CONNECT], message)
        if not match:
            return ParsedCommand(CommandType.UNKNOWN, raw_command=message)
        
        # Parse arguments using shlex to handle quoted strings
        try:
            args = shlex.split(match.group(1))
        except ValueError:
            return ParsedCommand(CommandType.UNKNOWN, raw_command=message)
        
        # Extract URL and options
        url = args[0] if args else ""
        kwargs = {}
        
        i = 1
        while i < len(args):
            if args[i] == "--token" and i + 1 < len(args):
                kwargs["token"] = args[i + 1]
                i += 2
            elif args[i] == "--token-env-var" and i + 1 < len(args):
                kwargs["token_env_var"] = args[i + 1]
                i += 2
            else:
                i += 1
        
        return ParsedCommand(
            CommandType.CONNECT,
            args=[url],
            kwargs=kwargs,
            raw_command=message
        )
    
    def _parse_call_command(self, message: str) -> ParsedCommand:
        """
        Parse a call command.
        
        Format: !call [tool_name] [json_args]
        
        Args:
            message: The command message
            
        Returns:
            A ParsedCommand object
        """
        match = re.match(self.command_patterns[CommandType.CALL], message)
        if not match:
            return ParsedCommand(CommandType.UNKNOWN, raw_command=message)
        
        tool_name = match.group(1)
        json_args_str = match.group(2)
        
        try:
            args_dict = json.loads(json_args_str)
            if not isinstance(args_dict, dict):
                raise ValueError("Arguments must be a JSON object")
        except json.JSONDecodeError:
            return ParsedCommand(
                CommandType.UNKNOWN,
                raw_command=message,
                kwargs={"error": "Invalid JSON arguments"}
            )
        
        return ParsedCommand(
            CommandType.CALL,
            args=[tool_name],
            kwargs={"args": args_dict},
            raw_command=message
        )
    
    def _parse_shorthand_command(self, message: str) -> ParsedCommand:
        """
        Parse a shorthand command.
        
        Format: !shorthand [tool_name] [arg1=value1] [arg2=value2] ...
        
        Args:
            message: The command message
            
        Returns:
            A ParsedCommand object
        """
        match = re.match(self.command_patterns[CommandType.SHORTHAND], message)
        if not match:
            return ParsedCommand(CommandType.UNKNOWN, raw_command=message)
        
        tool_name = match.group(1)
        args_str = match.group(2)
        
        # Parse key=value pairs
        args_dict = {}
        
        # Use regex to handle quoted values
        key_value_pattern = r'(\w+)=(?:"([^"]*)"|(\'[^\']*\')|([^\s]*))'
        
        for match in re.finditer(key_value_pattern, args_str):
            key = match.group(1)
            # Get the first non-None value from the capture groups
            value = next((g for g in match.groups()[1:] if g is not None), "")
            
            # Remove quotes if present
            if (value.startswith('"') and value.endswith('"')) or \
               (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            
            # Try to convert to appropriate type
            try:
                # Try as int
                if value.isdigit():
                    args_dict[key] = int(value)
                # Try as float
                elif re.match(r'^-?\d+\.\d+$', value):
                    args_dict[key] = float(value)
                # Try as boolean
                elif value.lower() in ['true', 'false']:
                    args_dict[key] = value.lower() == 'true'
                # Keep as string
                else:
                    args_dict[key] = value
            except (ValueError, TypeError):
                args_dict[key] = value
        
        return ParsedCommand(
            CommandType.SHORTHAND,
            args=[tool_name],
            kwargs={"args": args_dict},
            raw_command=message
        )
    
    def _parse_help_command(self, message: str) -> ParsedCommand:
        """
        Parse a help command.
        
        Format: !help [command_name]
        
        Args:
            message: The command message
            
        Returns:
            A ParsedCommand object
        """
        match = re.match(self.command_patterns[CommandType.HELP], message)
        if not match:
            return ParsedCommand(CommandType.UNKNOWN, raw_command=message)
        
        command_name = match.group(1) if match.groups()[0] else None
        
        return ParsedCommand(
            CommandType.HELP,
            args=[command_name] if command_name else [],
            raw_command=message
        )
    
    def _parse_schema_command(self, message: str) -> ParsedCommand:
        """
        Parse a schema command.
        
        Format: !schema [tool_name]
        
        Args:
            message: The command message
            
        Returns:
            A ParsedCommand object
        """
        match = re.match(self.command_patterns[CommandType.SCHEMA], message)
        if not match:
            return ParsedCommand(CommandType.UNKNOWN, raw_command=message)
        
        tool_name = match.group(1)
        
        return ParsedCommand(
            CommandType.SCHEMA,
            args=[tool_name],
            raw_command=message
        )
    
    def get_help_text(self, command: Optional[str] = None) -> str:
        """
        Get help text for commands.
        
        Args:
            command: Optional command name to get help for
            
        Returns:
            Help text
        """
        if command:
            # Help for specific command
            if command == "connect":
                return (
                    "**connect [url] [--token TOKEN] [--token-env-var VAR_NAME]**\n"
                    "Connect to an MCP server at the specified URL.\n\n"
                    "Examples:\n"
                    "```\n"
                    "connect http://localhost:8000\n"
                    "connect https://mcp-server.example.com --token your-auth-token\n"
                    "connect https://mcp-server.example.com --token-env-var MCP_TOKEN\n"
                    "```"
                )
            elif command == "disconnect":
                return "**disconnect**\nDisconnect from the current MCP server."
            elif command == "list":
                return "**list**\nList available tools on the connected MCP server."
            elif command == "call":
                return (
                    "**call [tool_name] [json_args]**\n"
                    "Call a tool with JSON arguments.\n\n"
                    "The agent will automatically validate your parameters against the tool's schema and:\n"
                    "- Check for required parameters\n"
                    "- Auto-fill optional parameters with default values\n"
                    "- Provide helpful error messages if validation fails\n\n"
                    "Example:\n"
                    "```\n"
                    "call search_models {\"query\": \"stable-diffusion\"}\n"
                    "```"
                )
            elif command == "shorthand":
                return (
                    "**shorthand [tool_name] [arg1=value1] [arg2=value2] ...**\n"
                    "Call a tool with shorthand syntax.\n\n"
                    "The agent will automatically validate your parameters against the tool's schema and:\n"
                    "- Check for required parameters\n"
                    "- Auto-fill optional parameters with default values\n"
                    "- Provide helpful error messages if validation fails\n\n"
                    "Example:\n"
                    "```\n"
                    "shorthand search_models query=\"stable-diffusion\"\n"
                    "```"
                )
            elif command == "status":
                return "**status**\nShow current connection status."
            elif command == "help":
                return "**help [command]**\nShow help for all commands or a specific command."
            elif command == "schema":
                return (
                    "**schema [tool_name]**\n"
                    "Get the schema for a specific tool.\n\n"
                    "This command returns the full schema for a tool, including all parameters, their types, descriptions, and default values.\n\n"
                    "Example:\n"
                    "```\n"
                    "schema stability-ai-text-to-image\n"
                    "```"
                )
            else:
                return f"Unknown command: {command}"
        else:
            # General help
            return (
                "**MCP Client Agent Commands**\n\n"
                "- **connect [url] [--token TOKEN] [--token-env-var VAR_NAME]**\n"
                "  Connect to an MCP server\n\n"
                "- **disconnect**\n"
                "  Disconnect from the current server\n\n"
                "- **list**\n"
                "  List available tools\n\n"
                "- **call [tool_name] [json_args]**\n"
                "  Call a tool with JSON arguments (with automatic parameter validation)\n\n"
                "- **shorthand [tool_name] [arg1=value1] [arg2=value2] ...**\n"
                "  Call a tool with shorthand syntax (with automatic parameter validation)\n\n"
                "- **schema [tool_name]**\n"
                "  Get the full schema for a specific tool\n\n"
                "- **status**\n"
                "  Show connection status\n\n"
                "- **help [command]**\n"
                "  Show help for commands\n\n"
                "Use `help [command]` for more details on a specific command."
            )