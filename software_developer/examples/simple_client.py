"""
Simple Chat Client Example

This example demonstrates how to use the MCP Client Agent directly
without going through the uagents protocol.
"""

import asyncio
import logging
from asi_mcp.agent import MCPClientAgent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def main():
    """Run the simple client example."""
    # Create the agent without starting the uagents server
    agent = MCPClientAgent()
    
    # Process commands directly
    
    # Connect to an MCP server
    logger.info("Connecting to MCP server...")
    response = await agent.process_message("!connect https://cloud.activepieces.com/api/v1/mcp/RerVk5mI66ZTiq9Xc8aIu/sse")
    print(f"\nResponse:\n{response}\n")
    
    # List available tools
    logger.info("Listing available tools...")
    response = await agent.process_message("!list")
    print(f"\nResponse:\n{response}\n")
    
    # Check status
    logger.info("Checking status...")
    response = await agent.process_message("!status")
    print(f"\nResponse:\n{response}\n")
    
    # Call a tool using JSON syntax
    logger.info("Calling a tool with JSON syntax...")
    response = await agent.process_message('!call example_tool {"param1": "value1", "param2": 42}')
    print(f"\nResponse:\n{response}\n")
    
    # Call a tool using shorthand syntax
    logger.info("Calling a tool with shorthand syntax...")
    response = await agent.process_message('!shorthand example_tool param1="value1" param2=42')
    print(f"\nResponse:\n{response}\n")
    
    # Disconnect
    logger.info("Disconnecting from MCP server...")
    response = await agent.process_message("!disconnect")
    print(f"\nResponse:\n{response}\n")


if __name__ == "__main__":
    # Run the example
    asyncio.run(main())