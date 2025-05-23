"""
Test MCP Client Agent

This script demonstrates how to run the MCP Client Agent and test it
with the provided SSE MCP server.
"""

import asyncio
import logging
import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from asi_mcp.agent import MCPClientAgent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# SSE MCP server URL
SSE_MCP_SERVER_URL = "https://cloud.activepieces.com/api/v1/mcp/RerVk5mI66ZTiq9Xc8aIu/sse"


async def test_agent():
    """Test the MCP Client Agent with the SSE MCP server."""
    # Create the agent
    agent = MCPClientAgent()
    
    try:
        # Connect to the SSE MCP server
        logger.info(f"Connecting to SSE MCP server at {SSE_MCP_SERVER_URL}...")
        response = await agent.process_message(f"!connect {SSE_MCP_SERVER_URL}")
        print(f"\nResponse:\n{response}\n")
        
        # List available tools
        logger.info("Listing available tools...")
        response = await agent.process_message("!list")
        print(f"\nResponse:\n{response}\n")
        
        # Check status
        logger.info("Checking status...")
        response = await agent.process_message("!status")
        print(f"\nResponse:\n{response}\n")
        
        # Get help
        logger.info("Getting help...")
        response = await agent.process_message("!help")
        print(f"\nResponse:\n{response}\n")
        
        # Try calling a tool with the open-router-ask-lmm tool
        logger.info("Trying to call the open-router-ask-lmm tool...")
        response = await agent.process_message('!call open-router-ask-lmm {"prompt": "Hello, how are you?"}')
        print(f"\nResponse:\n{response}\n")
        
    finally:
        # Disconnect from the server
        logger.info("Disconnecting from SSE MCP server...")
        response = await agent.process_message("!disconnect")
        print(f"\nResponse:\n{response}\n")


if __name__ == "__main__":
    # Run the test
    asyncio.run(test_agent())