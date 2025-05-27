"""
Chat Handler - Process incoming chat messages

This module contains the ChatHandler class that processes incoming chat messages,
extracts commands and parameters, and formats and sends responses.
"""

import asyncio
import logging
from typing import Dict, Optional, Any, List

from software_developer.command_parser import CommandParser, CommandType, ParsedCommand
from software_developer.session_manager import SessionManager
from software_developer.result_formatter import ResultFormatter
from software_developer.schema_utils import validate_schema_structure, extract_required_params, extract_optional_params_with_defaults

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ChatHandler:
    """Handler for chat messages and commands."""
    
    def __init__(
        self,
        command_parser: CommandParser,
        session_manager: SessionManager,
        result_formatter: ResultFormatter
    ):
        """
        Initialize the chat handler.
        
        Args:
            command_parser: The command parser instance
            session_manager: The session manager instance
            result_formatter: The result formatter instance
        """
        self.command_parser = command_parser
        self.session_manager = session_manager
        self.result_formatter = result_formatter
    
    async def process_message(self, message: str, sender: Optional[str] = None) -> str:
        """
        Process a chat message and return a response.
        
        Args:
            message: The message content
            sender: Optional sender identifier
            
        Returns:
            Response message
        """
        logger.info(f"Processing message from {sender or 'unknown'}: {message}")
        
        # Check if the message is a command
        if not self.command_parser.is_command(message):
            return self._handle_non_command_message(message)
        
        # Parse the command
        parsed_command = self.command_parser.parse_command(message)
        
        # Handle the command based on its type
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
        """
        Handle a non-command message.
        
        Args:
            message: The message content
            
        Returns:
            Response message
        """
        # For now, just provide help information
        return (
            "I'm an Software Developer Agent that can connect to Software Developer Team MCP servers and call tools.\n\n"
            "Use `help` to see available commands."
        )
    
    async def _handle_connect_command(self, command: ParsedCommand) -> str:
        """
        Handle a connect command.
        
        Args:
            command: The parsed command
            
        Returns:
            Response message
        """
        if not command.args:
            return self.result_formatter.format_error("URL is required for connect command")
        
        url = command.args[0]
        token = command.kwargs.get("token")
        token_env_var = command.kwargs.get("token_env_var")
        
        result = await self.session_manager.connect(url, token, token_env_var)
        return self.result_formatter.format_connect_result(result)
    
    async def _handle_disconnect_command(self, command: ParsedCommand) -> str:
        """
        Handle a disconnect command.
        
        Args:
            command: The parsed command
            
        Returns:
            Response message
        """
        result = await self.session_manager.disconnect()
        return self.result_formatter.format_disconnect_result(result)
    
    async def _handle_list_command(self, command: ParsedCommand) -> str:
        """
        Handle a list command.
        
        Args:
            command: The parsed command
            
        Returns:
            Response message
        """
        if not self.session_manager.is_connected():
            return self.result_formatter.format_not_connected_error()
        
        tools = await self.session_manager.list_tools()
        return self.result_formatter.format_tool_list(tools)
    
    async def _validate_and_fill_parameters(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and auto-fill parameters for a tool call based on its schema.
        
        Args:
            tool_name: The name of the tool
            args: The provided arguments
            
        Returns:
            A dictionary with validated and auto-filled arguments
        """
        try:
            # Get the tool schema
            schema = await self.session_manager.mcp_client.get_schema(tool_name)
            
            # Validate schema structure
            if not validate_schema_structure(schema):
                logger.warning(f"Invalid schema structure for tool {tool_name}, proceeding with provided args")
                return args
            
            # Extract required and optional parameters using utility functions
            required_params = extract_required_params(schema)
            optional_params = extract_optional_params_with_defaults(schema)
            
            # Check for missing required parameters
            missing_params = [param for param in required_params if param not in args]
            if missing_params:
                missing_list = ", ".join(missing_params)
                raise ValueError(f"Missing required parameters: {missing_list}")
            
            # Auto-fill optional parameters with defaults if not provided
            result_args = args.copy()
            for param, default_value in optional_params.items():
                if param not in result_args:
                    result_args[param] = default_value
                    logger.info(f"Auto-filled optional parameter {param} with default value: {default_value}")
            
            return result_args
        except Exception as e:
            logger.warning(f"Error validating parameters for {tool_name}: {e}")
            # If validation fails, return original args
            return args
    
    async def _handle_call_command(self, command: ParsedCommand) -> str:
        """
        Handle a call command.
        
        Args:
            command: The parsed command
            
        Returns:
            Response message
        """
        if not self.session_manager.is_connected():
            return self.result_formatter.format_not_connected_error()
        
        if not command.args:
            return self.result_formatter.format_error("Tool name is required for call command")
        
        tool_name = command.args[0]
        args = command.kwargs.get("args", {})
        
        try:
            # Get the tool schema
            schema = await self.session_manager.mcp_client.get_schema(tool_name)
            
            # Validate and auto-fill parameters
            validated_args = await self._validate_and_fill_parameters(tool_name, args)
            
            # Call the tool with validated arguments
            result = await self.session_manager.call_tool(tool_name, validated_args)
            return self.result_formatter.format_tool_call_result(result)
        except ValueError as e:
            # Handle parameter validation errors
            logger.error(f"Parameter validation error for {tool_name}: {e}")
            return self.result_formatter.format_parameter_validation_error(tool_name, str(e),
                await self.session_manager.mcp_client.get_schema(tool_name))
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            return self.result_formatter.format_error(f"Error calling tool {tool_name}: {str(e)}")
    
    async def _handle_shorthand_command(self, command: ParsedCommand) -> str:
        """
        Handle a shorthand command.
        
        Args:
            command: The parsed command
            
        Returns:
            Response message
        """
        if not self.session_manager.is_connected():
            return self.result_formatter.format_not_connected_error()
        
        if not command.args:
            return self.result_formatter.format_error("Tool name is required for shorthand command")
        
        tool_name = command.args[0]
        args = command.kwargs.get("args", {})
        
        try:
            # Get the tool schema
            schema = await self.session_manager.mcp_client.get_schema(tool_name)
            
            # Validate and auto-fill parameters
            validated_args = await self._validate_and_fill_parameters(tool_name, args)
            
            # Call the tool with validated arguments
            result = await self.session_manager.call_tool(tool_name, validated_args)
            return self.result_formatter.format_tool_call_result(result)
        except ValueError as e:
            # Handle parameter validation errors
            logger.error(f"Parameter validation error for {tool_name}: {e}")
            return self.result_formatter.format_parameter_validation_error(tool_name, str(e),
                await self.session_manager.mcp_client.get_schema(tool_name))
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            return self.result_formatter.format_error(f"Error calling tool {tool_name}: {str(e)}")
    
    async def _handle_status_command(self, command: ParsedCommand) -> str:
        """
        Handle a status command.
        
        Args:
            command: The parsed command
            
        Returns:
            Response message
        """
        status = self.session_manager.get_status()
        return self.result_formatter.format_status(status)
    
    async def _handle_help_command(self, command: ParsedCommand) -> str:
        """
        Handle a help command.
        
        Args:
            command: The parsed command
            
        Returns:
            Response message
        """
        command_name = command.args[0] if command.args else None
        return self.command_parser.get_help_text(command_name)
    
    async def _handle_schema_command(self, command: ParsedCommand) -> str:
        """
        Handle a schema command.
        
        Args:
            command: The parsed command
            
        Returns:
            Response message with the tool schema
        """
        if not self.session_manager.is_connected():
            return self.result_formatter.format_not_connected_error()
        
        if not command.args:
            return self.result_formatter.format_error("Tool name is required for schema command")
        
        tool_name = command.args[0]
        
        try:
            # Get the tool schema
            schema = await self.session_manager.mcp_client.get_schema(tool_name)
            
            if not schema:
                return self.result_formatter.format_error(f"No schema found for tool {tool_name}")
            
            # Format the schema result
            return self.result_formatter.format_schema_result(tool_name, schema)
        except Exception as e:
            logger.error(f"Error getting schema for tool {tool_name}: {e}")
            return self.result_formatter.format_error(f"Error getting schema for tool {tool_name}: {str(e)}")