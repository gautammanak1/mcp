"""
Chat Protocol for Software Developer Agent

This module implements a chat protocol for the Software Developer Agent, allowing
users to interact with MCP servers via natural language commands.
"""

from uuid import uuid4
from datetime import datetime
from typing import Dict, Any, Optional
import re
import logging

from uagents import Context, Protocol, Model
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    StartSessionContent,
    TextContent,
    chat_protocol_spec,
)

# Global reference to the agent instance
# This will be set in agent.py when including the protocol
mcp_agent_instance = None

def set_agent_instance(agent_instance):
    """Set the global agent instance reference."""
    global mcp_agent_instance
    mcp_agent_instance = agent_instance

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Command patterns for MCP operations
CONNECT_PATTERN = r"^connect to\s+(.+?)(?:\s+with token\s+(.+))?$"
DISCONNECT_PATTERN = r"^disconnect$"
LIST_PATTERN = r"^list tools$"
CALL_PATTERN = r"^call\s+(\S+)\s+(.+)$"
STATUS_PATTERN = r"^status$"
HELP_PATTERN = r"^help(?:\s+(\S+))?$"
SCHEMA_PATTERN = r"^schema\s+(\S+)$"

# Helper function to create a simple text response message
def create_text_chat(text: str, end_session: bool = False) -> ChatMessage:
    """
    Create a chat message with text content.
    
    Args:
        text: The text content
        end_session: Whether to end the session
        
    Returns:
        A ChatMessage object
    """
    content = [TextContent(type="text", text=text)]
    if end_session:
        content.append(EndSessionContent(type="end-session"))
    
    return ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=content,
    )

# Create the protocol instance using the standard spec
chat_proto = Protocol(spec=chat_protocol_spec)

# Define message handlers for the protocol
@chat_proto.on_message(ChatMessage)
async def handle_chat_message(ctx: Context, sender: str, msg: ChatMessage):
    """Handles incoming chat messages."""
    # Send acknowledgement
    await ctx.send(
        sender,
        ChatAcknowledgement(
            timestamp=datetime.utcnow(), acknowledged_msg_id=msg.msg_id
        ),
    )
    
    # Process different content types within the chat message
    for item in msg.content:
        if isinstance(item, StartSessionContent):
            logger.info(f"Chat session started with {sender}")
            # Send a welcome message
            await ctx.send(sender, create_text_chat(
                "Welcome to the Software Developer Agent! You can interact with Software Developer Team MCP servers using natural language commands.\n\n"
                "Examples:\n"
                "- connect to https://example.com/mcp/sse\n"
                "- connect to https://example.com/mcp/sse with token YOUR_TOKEN\n"
                "- list tools\n"
                "- call tool_name {\"param\": \"value\"}\n"
                "- schema tool_name\n"
                "- status\n"
                "- help\n"
                "- disconnect"
            ))
        elif isinstance(item, TextContent):
            logger.info(f"Received chat message from {sender}: {item.text}")
            
            # Process the text command
            text_lower = item.text.strip().lower()
            text = item.text.strip()  # Keep original case for URLs
            
            # Check for connect command
            connect_match = re.match(CONNECT_PATTERN, text_lower, re.IGNORECASE)
            if connect_match:
                # Find the same pattern in the original text to preserve case
                original_match = re.match(CONNECT_PATTERN, text, re.IGNORECASE)
                url = original_match.group(1).strip() if original_match else connect_match.group(1).strip()
                token = original_match.group(2).strip() if original_match and original_match.group(2) else None
                
                # Create the connect command
                if token:
                    command = f"!connect {url} --token {token}"
                else:
                    command = f"!connect {url}"
                
                # Process the command
                if mcp_agent_instance:
                    response = await mcp_agent_instance.process_message(command, sender)
                    # Extract Markdown string if response is a dictionary
                    response_text = response.get("markdown", str(response)) if isinstance(response, dict) else str(response)
                    await ctx.send(sender, create_text_chat(response_text))
                else:
                    await ctx.send(sender, create_text_chat("Error: Agent instance not available"))
                continue
            
            # Check for disconnect command
            if re.match(DISCONNECT_PATTERN, text_lower, re.IGNORECASE):
                if mcp_agent_instance:
                    response = await mcp_agent_instance.process_message("!disconnect", sender)
                    response_text = response.get("markdown", str(response)) if isinstance(response, dict) else str(response)
                    await ctx.send(sender, create_text_chat(response_text))
                else:
                    await ctx.send(sender, create_text_chat("Error: Agent instance not available"))
                continue
            
            # Check for list tools command
            if re.match(LIST_PATTERN, text_lower, re.IGNORECASE):
                if mcp_agent_instance:
                    response = await mcp_agent_instance.process_message("!list", sender)
                    response_text = response.get("markdown", str(response)) if isinstance(response, dict) else str(response)
                    await ctx.send(sender, create_text_chat(response_text))
                else:
                    await ctx.send(sender, create_text_chat("Error: Agent instance not available"))
                continue
            
            # Check for call command
            call_match = re.match(CALL_PATTERN, text_lower, re.IGNORECASE)
            if call_match:
                # Find the same pattern in the original text to preserve case
                original_match = re.match(CALL_PATTERN, text, re.IGNORECASE)
                tool_name = original_match.group(1).strip() if original_match else call_match.group(1).strip()
                args_text = original_match.group(2).strip() if original_match else call_match.group(2).strip()
                
                # Create the call command
                command = f"!call {tool_name} {args_text}"
                
                if mcp_agent_instance:
                    response = await mcp_agent_instance.process_message(command, sender)
                    response_text = response.get("markdown", str(response)) if isinstance(response, dict) else str(response)
                    await ctx.send(sender, create_text_chat(response_text))
                else:
                    await ctx.send(sender, create_text_chat("Error: Agent instance not available"))
                continue
            
            # Check for status command
            if re.match(STATUS_PATTERN, text_lower, re.IGNORECASE):
                if mcp_agent_instance:
                    response = await mcp_agent_instance.process_message("!status", sender)
                    response_text = response.get("markdown", str(response)) if isinstance(response, dict) else str(response)
                    await ctx.send(sender, create_text_chat(response_text))
                else:
                    await ctx.send(sender, create_text_chat("Error: Agent instance not available"))
                continue
            
            # Check for help command
            help_match = re.match(HELP_PATTERN, text_lower, re.IGNORECASE)
            if help_match:
                command_name = help_match.group(1) if help_match.groups()[0] else None
                
                # Create the help command
                if command_name:
                    command = f"!help {command_name}"
                else:
                    command = "!help"
                
                if mcp_agent_instance:
                    response = await mcp_agent_instance.process_message(command, sender)
                    response_text = response.get("markdown", str(response)) if isinstance(response, dict) else str(response)
                    await ctx.send(sender, create_text_chat(response_text))
                else:
                    await ctx.send(sender, create_text_chat("Error: Agent instance not available"))
                continue
            
            # Check for schema command
            schema_match = re.match(SCHEMA_PATTERN, text_lower, re.IGNORECASE)
            if schema_match:
                # Find the same pattern in the original text to preserve case
                original_match = re.match(SCHEMA_PATTERN, text, re.IGNORECASE)
                tool_name = original_match.group(1).strip() if original_match else schema_match.group(1).strip()
                
                # Create the schema command
                command = f"!schema {tool_name}"
                
                if mcp_agent_instance:
                    response = await mcp_agent_instance.process_message(command, sender)
                    response_text = response.get("markdown", str(response)) if isinstance(response, dict) else str(response)
                    await ctx.send(sender, create_text_chat(response_text))
                else:
                    await ctx.send(sender, create_text_chat("Error: Agent instance not available"))
                continue
            
            # If no command matched, send help message
            await ctx.send(sender, create_text_chat(
                "I didn't understand that command. Here are some examples of what you can say:\n\n"
                "- connect to https://example.com/mcp/sse\n"
                "- connect to https://example.com/mcp/sse with token YOUR_TOKEN\n"
                "- list tools\n"
                "- call tool_name {\"param\": \"value\"}\n"
                "- schema tool_name\n"
                "- status\n"
                "- help\n"
                "- disconnect"
            ))
        
        elif isinstance(item, EndSessionContent):
            logger.info(f"Chat session ended with {sender}")
        else:
            logger.info(f"Received unexpected chat content type from {sender}: {type(item)}")

@chat_proto.on_message(ChatAcknowledgement)
async def handle_chat_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    """Handles incoming chat acknowledgements."""
    logger.info(
        f"Received chat acknowledgement from {sender} for message {msg.acknowledged_msg_id}"
    )