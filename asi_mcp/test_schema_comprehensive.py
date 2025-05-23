#!/usr/bin/env python3
"""
Comprehensive Schema Command Test Client

This script tests both the structured and natural language schema commands
by connecting to the MCP Client Agent and requesting schemas for tools.
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
CLIENT_NAME = "schema_comprehensive_test"
CLIENT_SEED = "schema_comprehensive_test_seed"

# MCP Client Agent address - REPLACE THIS WITH YOUR AGENT ADDRESS
MCP_CLIENT_AGENT_ADDRESS = "agent1qfjyk5q9dq2m57uyqzctsmeruhy27v62vl53mjl35n6dvpjfwlwq2p5tmd2"

# Tools to request schemas for
TOOLS = ["stability-ai-text-to-image", "stability-ai-custom_api_call"]

# Initialize Agent
agent = Agent(
    name=CLIENT_NAME,
    seed=CLIENT_SEED,
    port=8002,  # Use a different port
    mailbox=True
)

# Create the protocol instance
chat_proto = Protocol(spec=chat_protocol_spec)

# Message counter for tracking responses
message_counter = 0
expected_messages = 5  # Connect + 2 schema requests + Disconnect + List

# Define message handlers for the protocol
@chat_proto.on_message(ChatMessage)
async def handle_chat_message(ctx: Context, sender: str, msg: ChatMessage):
    """Handles incoming chat messages."""
    global message_counter
    
    message_counter += 1
    logger.info(f"Received message {message_counter} from {sender}:")
    
    for item in msg.content:
        if hasattr(item, 'text'):
            # Log only the first 200 characters to keep logs readable
            text = item.text[:200] + "..." if len(item.text) > 200 else item.text
            logger.info(f"  -> Text: '{text}'")
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
    
    # Check if we've received all expected messages
    if message_counter >= expected_messages:
        logger.info("All expected messages received. Test completed successfully!")
        # Exit after a short delay to allow for final logging
        asyncio.create_task(delayed_exit())

async def delayed_exit():
    """Exit the program after a short delay."""
    await asyncio.sleep(2)
    os._exit(0)

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
    
    # Step 2: List available tools
    logger.info("Step 2: Listing available tools...")
    list_msg = ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=[TextContent(type="text", text="list tools")]
    )
    await ctx.send(MCP_CLIENT_AGENT_ADDRESS, list_msg)
    
    # Wait for list response
    await asyncio.sleep(3)
    
    # Step 3: Test natural language schema command
    logger.info(f"Step 3: Testing natural language schema command for {TOOLS[0]}...")
    nl_schema_msg = ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=[TextContent(type="text", text=f"schema {TOOLS[0]}")]
    )
    await ctx.send(MCP_CLIENT_AGENT_ADDRESS, nl_schema_msg)
    
    # Wait for schema response
    await asyncio.sleep(5)
    
    # Step 4: Test structured schema command
    if len(TOOLS) > 1:
        logger.info(f"Step 4: Testing structured schema command for {TOOLS[1]}...")
        struct_schema_msg = ChatMessage(
            timestamp=datetime.utcnow(),
            msg_id=uuid4(),
            content=[TextContent(type="text", text=f"!schema {TOOLS[1]}")]
        )
        await ctx.send(MCP_CLIENT_AGENT_ADDRESS, struct_schema_msg)
        
        # Wait for schema response
        await asyncio.sleep(5)
    
    # Step 5: Disconnect
    logger.info("Step 5: Disconnecting...")
    disconnect_msg = ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=[TextContent(type="text", text="disconnect")]
    )
    await ctx.send(MCP_CLIENT_AGENT_ADDRESS, disconnect_msg)
    
    # Wait for disconnection to complete
    await asyncio.sleep(2)
    
    logger.info("Test sequence completed. Waiting for all responses...")

@agent.on_event("startup")
async def on_startup(ctx: Context):
    """Run the test sequence on startup."""
    logger.info(f"Comprehensive Schema Test Client starting. Address: {agent.address}")
    logger.info(f"Will send requests to: {MCP_CLIENT_AGENT_ADDRESS}")
    
    # Ensure the agent has funds
    fund_agent_if_low(agent.wallet.address())
    
    # Run the test sequence
    await run_test_sequence(ctx)

if __name__ == "__main__":
    # Run the agent
    agent.run()