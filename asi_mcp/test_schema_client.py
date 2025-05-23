#!/usr/bin/env python3
"""
Test Schema Command Client

This script tests the schema command functionality by connecting to the MCP Client Agent
and requesting the schema for a specific tool.
"""

import asyncio
import logging
import sys
import os
from uuid import uuid4
from datetime import datetime

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from uagents import Agent, Context, Protocol
from uagents.setup import fund_agent_if_low
from uagents_core.contrib.protocols.chat import (
    chat_protocol_spec,
    ChatMessage,
    TextContent,
    ChatAcknowledgement,
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
CLIENT_NAME = "schema_test_client"
CLIENT_SEED = "schema_test_client_seed"

# MCP Client Agent address - REPLACE THIS WITH YOUR AGENT ADDRESS
MCP_CLIENT_AGENT_ADDRESS = "agent1qfjyk5q9dq2m57uyqzctsmeruhy27v62vl53mjl35n6dvpjfwlwq2p5tmd2"

# Tool to request schema for
TOOL_NAME = "stability-ai-text-to-image"

# Initialize Agent
agent = Agent(
    name=CLIENT_NAME,
    seed=CLIENT_SEED,
    port=8001,  # Use a different port
    mailbox=True
)

# Create the protocol instance
chat_proto = Protocol(spec=chat_protocol_spec)

# Define message handlers for the protocol
@chat_proto.on_message(ChatMessage)
async def handle_chat_message(ctx: Context, sender: str, msg: ChatMessage):
    """Handles incoming chat messages."""
    logger.info(f"Received chat message from {sender}:")
    
    for item in msg.content:
        if hasattr(item, 'text'):
            logger.info(f"  -> Text: '{item.text}'")
        else:
            logger.info(f"  -> Received content of type: {type(item)}")
    
    # Acknowledge receipt
    try:
        await ctx.send(
            sender,
            ChatAcknowledgement(
                timestamp=datetime.utcnow(),
                acknowledged_msg_id=msg.msg_id
            )
        )
    except Exception as e:
        logger.error(f"Error sending chat acknowledgement: {e}")

@chat_proto.on_message(ChatAcknowledgement)
async def handle_chat_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    """Handles acknowledgements from the server."""
    logger.info(f"Received chat ACK from {sender} for message {msg.acknowledged_msg_id}")

# Include the protocol
agent.include(chat_proto)

# Test sequence
async def run_test_sequence(ctx: Context):
    """Run the test sequence."""
    # Step 1: Connect to the MCP server
    logger.info("Step 1: Connecting to MCP server...")
    connect_msg = ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=[TextContent(type="text", text="connect to https://cloud.activepieces.com/api/v1/mcp/RerVk5mI66ZTiq9Xc8aIu/sse")]
    )
    await ctx.send(MCP_CLIENT_AGENT_ADDRESS, connect_msg)
    
    # Wait for connection to establish
    await asyncio.sleep(5)
    
    # Step 2: Request schema for the tool
    logger.info(f"Step 2: Requesting schema for {TOOL_NAME}...")
    schema_msg = ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=[TextContent(type="text", text=f"schema {TOOL_NAME}")]
    )
    await ctx.send(MCP_CLIENT_AGENT_ADDRESS, schema_msg)
    
    # Wait for schema response
    await asyncio.sleep(5)
    
    # Step 3: Disconnect
    logger.info("Step 3: Disconnecting...")
    disconnect_msg = ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=[TextContent(type="text", text="disconnect")]
    )
    await ctx.send(MCP_CLIENT_AGENT_ADDRESS, disconnect_msg)
    
    # Wait for disconnection to complete
    await asyncio.sleep(2)
    
    logger.info("Test sequence completed.")

@agent.on_event("startup")
async def on_startup(ctx: Context):
    """Run the test sequence on startup."""
    logger.info(f"Schema Test Client starting. Address: {agent.address}")
    logger.info(f"Will send requests to: {MCP_CLIENT_AGENT_ADDRESS}")
    
    # Ensure the agent has funds
    fund_agent_if_low(agent.wallet.address())
    
    # Run the test sequence
    await run_test_sequence(ctx)

if __name__ == "__main__":
    # Run the agent
    agent.run()