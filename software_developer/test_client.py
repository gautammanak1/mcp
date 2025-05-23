#!/usr/bin/env python3
"""
Test Client for ASI MCP Client Agent

This script creates a test client that connects to the MCP Client Agent
using uagents and mailbox, and interacts with it using the chat protocol.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from uagents import Agent, Context, Protocol
from uagents.setup import fund_agent_if_low
from uagents_core.contrib.protocols.chat import ChatMessage, TextContent, ChatAcknowledgement, chat_protocol_spec

# Create the chat protocol instance
chat_proto = Protocol(spec=chat_protocol_spec)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
CLIENT_NAME = "mcp_test_client"
CLIENT_SEED = "mcp_test_client_seed_phrase_for_stable_address"
CLIENT_PORT = 8001  # Use a different port than the agent

# MCP Client Agent address - this is the address of the running agent
MCP_CLIENT_AGENT_ADDRESS = "agent1qfjyk5q9dq2m57uyqzctsmeruhy27v62vl53mjl35n6dvpjfwlwq2p5tmd2"

# SSE MCP server URL for testing
SSE_MCP_SERVER_URL = "https://cloud.activepieces.com/api/v1/mcp/RerVk5mI66ZTiq9Xc8aIu/sse"

# Initialize Agent
agent = Agent(
    name=CLIENT_NAME,
    seed=CLIENT_SEED,
    port=CLIENT_PORT,
    mailbox=True
)

print(f"MCP Test Client starting. Address: {agent.address}")
print(f"Will send requests to MCP Client Agent at: {MCP_CLIENT_AGENT_ADDRESS}")

@agent.on_event("startup")
async def startup(ctx: Context):
    """Send initial chat messages on startup."""
    ctx.logger.info("MCP Test Client started")
    
    # Wait a bit for the mailbox connection to establish
    await asyncio.sleep(5)
    
    # Send a series of commands with delays between them
    await send_command(ctx, "connect to " + SSE_MCP_SERVER_URL)
    await asyncio.sleep(5)
    
    await send_command(ctx, "list tools")
    await asyncio.sleep(5)
    
    await send_command(ctx, "status")
    await asyncio.sleep(5)
    
    await send_command(ctx, "help")
    await asyncio.sleep(5)
    
    # Try calling a tool (adjust parameters as needed)
    await send_command(ctx, 'call open-router-ask-lmm {"prompt": "Hello, how are you?"}')
    await asyncio.sleep(10)
    
    await send_command(ctx, "disconnect")
    await asyncio.sleep(5)
    
    ctx.logger.info("Test sequence completed")

async def send_command(ctx: Context, command: str):
    """Send a chat command to the MCP Client Agent."""
    ctx.logger.info(f"Sending command: {command}")
    
    chat_msg = ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid.uuid4(),
        content=[TextContent(type="text", text=command)]
    )
    
    try:
        await ctx.send(MCP_CLIENT_AGENT_ADDRESS, chat_msg)
        ctx.logger.info("Command sent successfully")
    except Exception as e:
        ctx.logger.error(f"Error sending command: {e}")

@chat_proto.on_message(ChatMessage)
async def handle_chat_response(ctx: Context, sender: str, msg: ChatMessage):
    """Handle incoming chat messages from the MCP Client Agent."""
    ctx.logger.info(f"Received chat message from {sender}:")
    
    for item in msg.content:
        if isinstance(item, TextContent):
            ctx.logger.info(f"Response text: {item.text}")
        else:
            ctx.logger.info(f"Received content of type: {type(item)}")
    
    # Send acknowledgement
    try:
        await ctx.send(sender, ChatAcknowledgement(
            timestamp=datetime.utcnow(),
            acknowledged_msg_id=msg.msg_id
        ))
    except Exception as e:
        ctx.logger.error(f"Error sending acknowledgement: {e}")

@chat_proto.on_message(ChatAcknowledgement)
async def handle_chat_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    """Handle acknowledgements from the MCP Client Agent."""
    ctx.logger.info(f"Received acknowledgement from {sender} for message {msg.acknowledged_msg_id}")

# Include the chat protocol
agent.include(chat_proto)

if __name__ == "__main__":
    # Ensure the agent has funds for network operations
    fund_agent_if_low(agent.wallet.address())
    
    # Run the agent
    agent.run()