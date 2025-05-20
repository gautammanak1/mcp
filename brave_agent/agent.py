import asyncio
import logging
from typing import Dict, Optional, Any, Callable

from uagents import Agent, Context, Protocol, Model
from uagents.setup import fund_agent_if_low

from brave_client import BraveSearchClient
from chat_proto import chat_proto, set_agent_instance
from command_parser import BraveSearchCommandParser
from result_formatter import BraveSearchResultFormatter
from session_manager import BraveSearchSessionManager
from chat_handler import BraveSearchChatHandler

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ChatMessage(Model):
    content: str
    sender: Optional[str] = None

class ChatResponse(Model):
    content: str
    recipient: Optional[str] = None

class BraveSearchAgent:
    def __init__(self, name: str = "brave_search_agent", seed: Optional[str] = None, port: int = 8000):
        self.name = name
        self.seed = seed
        self.port = port
        self.agent = Agent(
            name=name,
            seed=seed,
            port=port,
            mailbox=True,
        )
        fund_agent_if_low(self.agent.wallet.address())
        self.result_formatter = BraveSearchResultFormatter()
        self.brave_client = BraveSearchClient()
        self.session_manager = BraveSearchSessionManager(self.brave_client)
        self.command_parser = BraveSearchCommandParser()
        self.chat_handler = BraveSearchChatHandler(
            command_parser=self.command_parser,
            session_manager=self.session_manager,
            result_formatter=self.result_formatter
        )
        self.chat_protocol = Protocol("chat")
        
        @self.chat_protocol.on_message(model=ChatMessage)
        async def handle_chat_message(ctx: Context, sender: str, msg: ChatMessage):
            logger.info(f"Received message from {sender}: {msg.content}")
            response = await self.chat_handler.process_message(msg.content, sender)
            await ctx.send(sender, ChatResponse(content=response, recipient=sender))
            logger.info(f"Sent response to {sender}")
        
        self.agent.include(self.chat_protocol)
        set_agent_instance(self)
        self.agent.include(chat_proto, publish_manifest=True)
    
    async def connect(self, url: str, token: Optional[str] = None) -> Dict[str, Any]:
        logger.info(f"Connecting to Brave Search MCP server at {url}")
        result = await self.session_manager.connect(url, token)
        if result.get("success"):
            logger.info(f"Successfully connected to Brave Search MCP server at {url}")
        else:
            logger.warning(f"Failed to connect to Brave Search MCP server: {result.get('message')}")
        return result
    
    async def auto_connect(self):
        logger.info("Auto-connect skipped; waiting for user to provide URL via connect command")
        return {
            "success": False,
            "message": "Auto-connect disabled; use 'connect <URL>' to connect to the Brave Search MCP server"
        }
    
    def start(self):
        logger.info(f"Starting Brave Search Agent on port {self.port}")
        self.agent.run()
    
    def stop(self):
        logger.info("Stopping Brave Search Agent")
        asyncio.create_task(self.session_manager.disconnect_all())
    
    async def process_message(self, message: str, sender: Optional[str] = None) -> str:
        return await self.chat_handler.process_message(message, sender)