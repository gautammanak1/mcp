#!/usr/bin/env python3
"""
Run Brave Search Agent
"""

import logging
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from brave_agent.agent import BraveSearchAgent

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Starting Brave Search Agent with Chat Protocol support...")
    agent = BraveSearchAgent(
        name="brave_search_agent",
        seed="brave_search_agent",
        port=8000
        
    )
    agent_address = agent.agent.address
    logger.info("=" * 50)
    logger.info(f"AGENT ADDRESS: {agent_address}")
    logger.info("=" * 50)
    logger.info("Use this address in the test client when prompted.")
    logger.info("You can interact with this agent using both:")
    logger.info("1. Direct Brave Search commands (e.g., !connect <URL>, !list, etc.)")
    logger.info("2. Chat protocol (natural language commands, e.g., connect <URL>)")
    logger.info("Start by connecting with: connect https://cloud.activepieces.com/api/v1/mcp/LT7SBrTtl0ALyXWtpf9v4/sse")
    try:
        agent.start()
    except KeyboardInterrupt:
        logger.info("Stopping Brave Search Agent...")
        agent.stop()
        logger.info("Brave Search Agent stopped")