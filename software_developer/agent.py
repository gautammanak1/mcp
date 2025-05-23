"""
Software Developer Agent - Main agent class

This module contains the main agent class that initializes the uagents framework,
handles chat protocol, and manages startup and shutdown.
"""

import asyncio
import logging
from typing import Dict, Optional, Any, Callable

from uagents import Agent, Context, Protocol, Model
from uagents.setup import fund_agent_if_low

from software_developer.chat_handler import ChatHandler
from software_developer.command_parser import CommandParser
from software_developer.session_manager import SessionManager
from software_developer.mcp_client import MCPClient
from software_developer.result_formatter import ResultFormatter
from software_developer.chat_proto import chat_proto, set_agent_instance

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define message models
class ChatMessage(Model):
    """Model for chat messages."""
    content: str
    sender: Optional[str] = None

class ChatResponse(Model):
    """Model for chat responses."""
    content: str
    recipient: Optional[str] = None

class MCPClientAgent:
    """
    Software Developer Agent that connects to Software Developer Team MCP servers via SSE transport
    and provides a chat interface for interacting with these servers.
    """
    
    def __init__(self, name: str = "software_developer_agent", seed: Optional[str] = None, port: int = 8000):
        """
        Initialize the Software Developer Agent.
        
        Args:
            name: Name of the agent
            seed: Seed for agent identity (if None, a random one will be generated)
            port: Port for the agent's HTTP endpoint
        """
        self.name = name
        self.seed = seed
        self.port = port
        
        # Create the uagents Agent with mailbox enabled
        self.agent = Agent(
            name=name,
            seed=seed,
            port=port,
            mailbox=True,
        )
        
        # Fund the agent if needed
        fund_agent_if_low(self.agent.wallet.address())
        
        # Initialize components
        self.result_formatter = ResultFormatter()
        self.mcp_client = MCPClient()
        self.session_manager = SessionManager(self.mcp_client)
        self.command_parser = CommandParser()
        self.chat_handler = ChatHandler(
            command_parser=self.command_parser,
            session_manager=self.session_manager,
            result_formatter=self.result_formatter
        )
        
        # Set up chat protocol
        self.chat_protocol = Protocol("chat")
        
        @self.chat_protocol.on_message(model=ChatMessage)
        async def handle_chat_message(ctx: Context, sender: str, msg: ChatMessage):
            """Handle incoming chat messages."""
            logger.info(f"Received message from {sender}: {msg.content}")
            
            # Process the message
            response = await self.chat_handler.process_message(msg.content, sender)
            
            # Send response
            await ctx.send(sender, ChatResponse(content=response, recipient=sender))
            logger.info(f"Sent response to {sender}")
        
        # Register the protocols with the agent
        self.agent.include(self.chat_protocol)
        
        # Set the agent instance in the chat_proto module and include the protocol
        set_agent_instance(self)
        self.agent.include(chat_proto, publish_manifest=True)
    
    def start(self):
        """Start the agent."""
        logger.info(f"Starting Software Developer Agent on port {self.port}")
        self.agent.run()
    
    def stop(self):
        """Stop the agent."""
        logger.info("Stopping Software Developer Agent")
        # Cleanup resources
        asyncio.create_task(self.session_manager.disconnect_all())
    
    async def process_message(self, message: str, sender: Optional[str] = None) -> str:
        """
        Process a chat message and return a response.
        
        This method can be used directly without going through the agent protocol,
        which is useful for testing or direct integration.
        
        Args:
            message: The message content
            sender: Optional sender identifier
            
        Returns:
            Response message
        """
        return await self.chat_handler.process_message(message, sender)

if __name__ == "__main__":
    # Example usage
    agent = MCPClientAgent()
    agent.start()