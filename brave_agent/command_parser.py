import json
import re
import shlex
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Union

class CommandType(Enum):
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
    def __init__(self, command_type: CommandType, args: List[str] = None, kwargs: Dict[str, Any] = None, raw_command: str = ""):
        self.command_type = command_type
        self.args = args or []
        self.kwargs = kwargs or {}
        self.raw_command = raw_command
    
    def __str__(self) -> str:
        return f"ParsedCommand(type={self.command_type.value}, args={self.args}, kwargs={self.kwargs})"

class BraveSearchCommandParser:
    COMMAND_PREFIX = "!"
    
    def __init__(self):
        self.command_patterns = {
            CommandType.CONNECT: r"^!connect\s+(https?://[^\s]+)(?:\s+--token\s+(\S+))?(?:\s+--token-env-var\s+(\S+))?$",
            CommandType.DISCONNECT: r"^!disconnect$",
            CommandType.LIST: r"^!list$",
            CommandType.CALL: r"^!call\s+(\S+)\s+(.+)$",
            CommandType.SHORTHAND: r"^!shorthand\s+(\S+)\s+(.+)$",
            CommandType.STATUS: r"^!status$",
            CommandType.HELP: r"^!help(?:\s+(\S+))?$",
            CommandType.SCHEMA: r"^!schema\s+(\S+)$",
        }
    
    def is_command(self, message: str) -> bool:
        return message.strip().startswith(self.COMMAND_PREFIX)
    
    def parse_command(self, message: str) -> ParsedCommand:
        message = message.strip()
        if not self.is_command(message):
            return ParsedCommand(CommandType.UNKNOWN, raw_command=message)
        parts = message.split(maxsplit=1)
        cmd = parts[0][1:]
        try:
            command_type = CommandType(cmd)
        except ValueError:
            return ParsedCommand(CommandType.UNKNOWN, raw_command=message)
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
        match = re.match(self.command_patterns[CommandType.CONNECT], message)
        if not match:
            return ParsedCommand(CommandType.UNKNOWN, raw_command=message)
        kwargs = {"url": match.group(1)}
        if match.group(2):
            kwargs["token"] = match.group(2)
        if match.group(3):
            kwargs["token_env_var"] = match.group(3)
        return ParsedCommand(
            CommandType.CONNECT,
            args=[],
            kwargs=kwargs,
            raw_command=message
        )
    
    def _parse_call_command(self, message: str) -> ParsedCommand:
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
        match = re.match(self.command_patterns[CommandType.SHORTHAND], message)
        if not match:
            return ParsedCommand(CommandType.UNKNOWN, raw_command=message)
        tool_name = match.group(1)
        args_str = match.group(2)
        args_dict = {}
        key_value_pattern = r'(\w+)=(?:"([^"]*)"|(\'[^\']*\')|([^\s]*))'
        for match in re.finditer(key_value_pattern, args_str):
            key = match.group(1)
            value = next((g for g in match.groups()[1:] if g is not None), "")
            if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            try:
                if value.isdigit():
                    args_dict[key] = int(value)
                elif re.match(r'^-?\d+\.\d+$', value):
                    args_dict[key] = float(value)
                elif value.lower() in ['true', 'false']:
                    args_dict[key] = value.lower() == 'true'
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
        if command:
            if command == "connect":
                return (
                    "**connect <URL> [--token TOKEN] [--token-env-var VAR_NAME]**\n"
                    "Connect to the Brave Search MCP server at the specified URL.\n\n"
                    "Examples:\n"
                    "```\n"
                    "!connect https://cloud.activepieces.com/api/v1/mcp/...\n"
                    "!connect https://cloud.activepieces.com/api/v1/mcp/... --token your-auth-token\n"
                    "!connect https://cloud.activepieces.com/api/v1/mcp/... --token-env-var BRAVE_API_KEY\n"
                    "```"
                )
            elif command == "disconnect":
                return "**disconnect**\nDisconnect from the Brave Search MCP server."
            elif command == "list":
                return "**list**\nList available tools on the Brave Search MCP server."
            elif command == "call":
                return (
                    "**call [tool_name] [json_args]**\n"
                    "Call a Brave Search tool with JSON arguments.\n\n"
                    "The agent will automatically validate your parameters against the tool's schema and:\n"
                    "- Check for required parameters\n"
                    "- Auto-fill optional parameters with default values\n"
                    "- Provide helpful error messages if validation fails\n\n"
                    "Example:\n"
                    "```\n"
                    "!call brave_web_search {\"query\": \"AI news\"}\n"
                    "```"
                )
            elif command == "shorthand":
                return (
                    "**shorthand [tool_name] [arg1=value1] [arg2=value2] ...**\n"
                    "Call a Brave Search tool with shorthand syntax.\n\n"
                    "The agent will automatically validate your parameters against the tool's schema and:\n"
                    "- Check for required parameters\n"
                    "- Auto-fill optional parameters with default values\n"
                    "- Provide helpful error messages if validation fails\n\n"
                    "Example:\n"
                    "```\n"
                    "!shorthand brave_web_search query=\"AI news\"\n"
                    "```"
                )
            elif command == "status":
                return "**status**\nShow current connection status to the Brave Search MCP server."
            elif command == "help":
                return "**help [command]**\nShow help for all commands or a specific command."
            elif command == "schema":
                return (
                    "**schema [tool_name]**\n"
                    "Get the schema for a specific Brave Search tool.\n\n"
                    "This command returns the full schema for a tool, including all parameters, their types, descriptions, and default values.\n\n"
                    "Example:\n"
                    "```\n"
                    "!schema brave_web_search\n"
                    "```"
                )
            else:
                return f"Unknown command: {command}"
        else:
            return (
                "**Brave Search Agent Commands**\n\n"
                "- **connect <URL> [--token TOKEN] [--token-env-var VAR_NAME]**\n"
                "  Connect to the Brave Search MCP server at the specified URL\n\n"
                "- **disconnect**\n"
                "  Disconnect from the Brave Search MCP server\n\n"
                "- **list**\n"
                "  List available Brave Search tools\n\n"
                "- **call [tool_name] [json_args]**\n"
                "  Call a Brave Search tool with JSON arguments (with automatic parameter validation)\n\n"
                "- **shorthand [tool_name] [arg1=value1] [arg2=value2] ...**\n"
                "  Call a Brave Search tool with shorthand syntax (with automatic parameter validation)\n\n"
                "- **schema [tool_name]**\n"
                "  Get the full schema for a specific Brave Search tool\n\n"
                "- **status**\n"
                "  Show connection status to the Brave Search MCP server\n\n"
                "- **help [command]**\n"
                "  Show help for commands\n\n"
                "Use `help [command]` for more details on a specific command."
            )