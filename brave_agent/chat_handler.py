import asyncio
import logging
from typing import Dict, Optional, Any, List

from command_parser import CommandType, ParsedCommand
from schema_utils import validate_schema_structure, extract_required_params, extract_optional_params_with_defaults

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BraveSearchChatHandler:
    def __init__(self, command_parser, session_manager, result_formatter):
        self.command_parser = command_parser
        self.session_manager = session_manager
        self.result_formatter = result_formatter
    
    async def process_message(self, message: str, sender: Optional[str] = None) -> str:
        logger.info(f"Processing message from {sender or 'unknown'}: {message}")
        if not self.command_parser.is_command(message):
            return self._handle_non_command_message(message)
        parsed_command = self.command_parser.parse_command(message)
        if parsed_command.command_type == CommandType.CONNECT:
            return await self._handle_connect_command(parsed_command)
        elif parsed_command.command_type == CommandType.DISCONNECT:
            return await self._handle_disconnect_command(parsed_command)
        elif parsed_command.command_type == CommandType.LIST:
            return await self._handle_list_command(parsed_command)
        elif parsed_command.command_type == CommandType.CALL:
            return await self._handle_call_command(parsed_command)
        elif parsed_command.command_type == CommandType.SHORTHAND:
            return await self._handle_shorthand_command(parsed_command)
        elif parsed_command.command_type == CommandType.STATUS:
            return await self._handle_status_command(parsed_command)
        elif parsed_command.command_type == CommandType.HELP:
            return await self._handle_help_command(parsed_command)
        elif parsed_command.command_type == CommandType.SCHEMA:
            return await self._handle_schema_command(parsed_command)
        else:
            return self.result_formatter.format_unknown_command(message)
    
    def _handle_non_command_message(self, message: str) -> str:
        return (
            "I'm a Brave Search Agent that can connect to the Brave Search MCP server and call search tools.\n\n"
            "Use `help` to see available commands."
        )
    
    async def _handle_connect_command(self, command: ParsedCommand) -> str:
        url = command.kwargs.get("url")
        token = command.kwargs.get("token")
        token_env_var = command.kwargs.get("token_env_var")
        if not url:
            return self.result_formatter.format_error("URL is required for connect command. Example: !connect <URL>")
        # Log the URL to ensure case is preserved
        logger.info(f"Connecting with URL: {url}")
        result = await self.session_manager.connect(url, token, token_env_var)
        return self.result_formatter.format_connect_result(result)
    
    async def _handle_disconnect_command(self, command: ParsedCommand) -> str:
        result = await self.session_manager.disconnect()
        return self.result_formatter.format_disconnect_result(result)
    
    async def _handle_list_command(self, command: ParsedCommand) -> str:
        if not self.session_manager.is_connected():
            return self.result_formatter.format_not_connected_error()
        tools = await self.session_manager.list_tools()
        return self.result_formatter.format_tool_list(tools)
    
    async def _validate_and_fill_parameters(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        try:
            schema = await self.session_manager.mcp_client.get_schema(tool_name)
            if not validate_schema_structure(schema):
                logger.warning(f"Invalid schema structure for tool {tool_name}, proceeding with provided args")
                return args
            required_params = extract_required_params(schema)
            optional_params = extract_optional_params_with_defaults(schema)
            missing_params = [param for param in required_params if param not in args]
            if missing_params:
                missing_list = ", ".join(missing_params)
                raise ValueError(f"Missing required parameters: {missing_list}")
            result_args = args.copy()
            for param, default_value in optional_params.items():
                if param not in result_args:
                    result_args[param] = default_value
                    logger.info(f"Auto-filled optional parameter {param} with default value: {default_value}")
            return result_args
        except Exception as e:
            logger.warning(f"Error validating parameters for {tool_name}: {e}")
            return args
    
    async def _handle_call_command(self, command: ParsedCommand) -> str:
        if not self.session_manager.is_connected():
            return self.result_formatter.format_not_connected_error()
        if not command.args:
            return self.result_formatter.format_error("Tool name is required for call command")
        tool_name = command.args[0]
        args = command.kwargs.get("args", {})
        try:
            validated_args = await self._validate_and_fill_parameters(tool_name, args)
            result = await self.session_manager.call_tool(tool_name, validated_args)
            return self.result_formatter.format_tool_call_result(result)
        except ValueError as e:
            logger.error(f"Parameter validation error for {tool_name}: {e}")
            return self.result_formatter.format_parameter_validation_error(
                tool_name, str(e), await self.session_manager.mcp_client.get_schema(tool_name))
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            return self.result_formatter.format_error(f"Error calling tool {tool_name}: {str(e)}")
    
    async def _handle_shorthand_command(self, command: ParsedCommand) -> str:
        if not self.session_manager.is_connected():
            return self.result_formatter.format_not_connected_error()
        if not command.args:
            return self.result_formatter.format_error("Tool name is required for shorthand command")
        tool_name = command.args[0]
        args = command.kwargs.get("args", {})
        try:
            validated_args = await self._validate_and_fill_parameters(tool_name, args)
            result = await self.session_manager.call_tool(tool_name, validated_args)
            return self.result_formatter.format_tool_call_result(result)
        except ValueError as e:
            logger.error(f"Parameter validation error for {tool_name}: {e}")
            return self.result_formatter.format_parameter_validation_error(
                tool_name, str(e), await self.session_manager.mcp_client.get_schema(tool_name))
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            return self.result_formatter.format_error(f"Error calling tool {tool_name}: {str(e)}")
    
    async def _handle_status_command(self, command: ParsedCommand) -> str:
        status = self.session_manager.get_status()
        return self.result_formatter.format_status(status)
    
    async def _handle_help_command(self, command: ParsedCommand) -> str:
        command_name = command.args[0] if command.args else None
        return self.command_parser.get_help_text(command_name)
    
    async def _handle_schema_command(self, command: ParsedCommand) -> str:
        if not self.session_manager.is_connected():
            return self.result_formatter.format_not_connected_error()
        if not command.args:
            return self.result_formatter.format_error("Tool name is required for schema command")
        tool_name = command.args[0]
        try:
            schema = await self.session_manager.mcp_client.get_schema(tool_name)
            if not schema:
                return self.result_formatter.format_error(f"No schema found for tool {tool_name}")
            return self.result_formatter.format_schema_result(tool_name, schema)
        except Exception as e:
            logger.error(f"Error getting schema for tool {tool_name}: {e}")
            return self.result_formatter.format_error(f"Error getting schema for tool {tool_name}: {str(e)}")