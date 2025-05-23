"""
Weather Example

This example demonstrates how to use the MCP Client Agent to connect to
a weather MCP server and retrieve weather information.
"""

import asyncio
import logging
import os
from dotenv import load_dotenv
from asi_mcp.agent import MCPClientAgent

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Weather server URL
WEATHER_SERVER_URL = os.getenv("WEATHER_SERVER_URL", "https://cloud.activepieces.com/api/v1/mcp/RerVk5mI66ZTiq9Xc8aIu/sse")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")


async def main():
    """Run the weather example."""
    # Create the agent
    agent = MCPClientAgent()
    
    # Connect to the weather MCP server
    logger.info(f"Connecting to weather MCP server at {WEATHER_SERVER_URL}...")
    
    connect_command = f"!connect {WEATHER_SERVER_URL}"
    if WEATHER_API_KEY:
        connect_command += f" --token {WEATHER_API_KEY}"
    
    response = await agent.process_message(connect_command)
    print(f"\nResponse:\n{response}\n")
    
    # List available weather tools
    logger.info("Listing available weather tools...")
    response = await agent.process_message("!list")
    print(f"\nResponse:\n{response}\n")
    
    # Get current weather for a location using JSON syntax
    logger.info("Getting current weather for New York...")
    response = await agent.process_message('!call get_current_weather {"city": "New York"}')
    print(f"\nResponse:\n{response}\n")
    
    # Get weather forecast using shorthand syntax
    logger.info("Getting weather forecast for London...")
    response = await agent.process_message('!shorthand get_forecast city="London" days=5')
    print(f"\nResponse:\n{response}\n")
    
    # Get weather alerts for a state
    logger.info("Getting weather alerts for California...")
    response = await agent.process_message('!shorthand get_alerts state="CA"')
    print(f"\nResponse:\n{response}\n")
    
    # Disconnect from the server
    logger.info("Disconnecting from weather MCP server...")
    response = await agent.process_message("!disconnect")
    print(f"\nResponse:\n{response}\n")


if __name__ == "__main__":
    # Run the example
    asyncio.run(main())