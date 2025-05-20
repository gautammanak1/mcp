import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
import os
from urllib.parse import urlparse

try:
    from fastmcp import Client
    from fastmcp.client.transports import SSETransport
except ImportError:
    raise ImportError("fastmcp package is required. Install it with 'pip install fastmcp'")

from schema_utils import get_schema_from_tool

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BraveSearchClient:
    """Wrapper for fastmcp Client to handle communication with the Brave Search MCP server."""
    
    def __init__(self):
        self.client = None
        self.connected = False
        self.server_url = None
        self.tools = []
        self.token = None
    
    async def connect(self, url: str, token: Optional[str] = None) -> bool:
        if not url:
            logger.error("No URL provided for Brave Search MCP server")
            return False
        
        # Log original URL
        logger.info(f"Received URL: {url}")
        # Validate and normalize URL
        url = url.strip()
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            logger.error(f"Invalid URL format: {url}")
            return False
        if parsed_url.scheme not in ('http', 'https'):
            logger.warning(f"Unexpected URL scheme: {parsed_url.scheme}. Expected http or https")
        
        try:
            logger.info(f"Connecting to Brave Search MCP server at {url}")
            transport = SSETransport(url)
            # Pass token as Authorization header if provided
            if token:
                transport.headers = {'Authorization': f'Bearer {token}'}
                logger.info("Using token in Authorization header")
            self.client = Client(transport)
            self.server_url = url
            await self.client.__aenter__()
            tools = await self.client.list_tools()
            self.tools = tools
            self.connected = True
            self.token = token
            tool_names = [tool.name for tool in tools if hasattr(tool, 'name')]
            logger.info(f"Connected to Brave Search MCP server at {url}. Available tools: {tool_names}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Brave Search MCP server at {url}: {str(e)}")
            if hasattr(e, '__dict__'):
                logger.error(f"Error details: {e.__dict__}")
            else:
                logger.error(f"Error type: {type(e).__name__}")
            if '404' in str(e):
                logger.error("Server returned 404 Not Found. Verify the URL is correct and the endpoint exists.")
            self.client = None
            self.connected = False
            self.server_url = None
            self.token = None
            return False
    
    async def disconnect(self) -> bool:
        if not self.connected or not self.client:
            logger.warning("Not connected to the Brave Search MCP server")
            return True
        
        try:
            await self.client.__aexit__(None, None, None)
            self.client = None
            self.connected = False
            logger.info(f"Disconnected from Brave Search MCP server at {self.server_url}")
            self.server_url = None
            self.token = None
            return True
        except Exception as e:
            logger.error(f"Failed to disconnect from Brave Search MCP server: {e}")
            return False
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        if not self.connected or not self.client:
            logger.warning("Not connected to the Brave Search MCP server")
            return []
        
        try:
            tools = await self.client.list_tools()
            self.tools = tools
            tool_names = [tool.name for tool in tools if hasattr(tool, 'name')]
            logger.info(f"Available tools: {', '.join(tool_names)}")
            return tools
        except Exception as e:
            logger.error(f"Failed to list tools: {e}")
            return []
    
    async def call_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        if not self.connected or not self.client:
            raise ConnectionError("Not connected to the Brave Search MCP server")
        
        try:
            logger.info(f"Calling tool '{tool_name}' with arguments: {args}")
            if self.token:
                args['headers'] = args.get('headers', {})
                args['headers']['Authorization'] = f'Bearer {self.token}'
                logger.info("Added token to tool call headers")
            result = await self.client.call_tool(tool_name, args)
            return result
        except Exception as e:
            logger.error(f"Failed to call tool {tool_name}: {e}")
            if hasattr(e, '__dict__'):
                logger.error(f"Error details: {e.__dict__}")
            raise
    
    async def get_schema(self, tool_name: str) -> Dict[str, Any]:
        if not self.connected or not self.client:
            raise ConnectionError("Not connected to the Brave Search MCP server")
        
        try:
            tools = await self.list_tools()
            for tool in tools:
                if hasattr(tool, 'name') and tool.name == tool_name:
                    return get_schema_from_tool(tool, tool_name)
            raise ValueError(f"Tool {tool_name} not found")
        except Exception as e:
            logger.error(f"Failed to get schema for tool {tool_name}: {e}")
            raise
    
    def is_connected(self) -> bool:
        return self.connected and self.client is not None
    
    def get_server_url(self) -> Optional[str]:
        return self.server_url if self.connected else None


class BraveSearchServerSession:
    """Class representing a session with the Brave Search MCP server."""
    
    def __init__(self, client: BraveSearchClient, url: str, token: Optional[str] = None):
        self.url = url
        self.client = client
        self.token = token
        self.connected = False
        self.available_tools: List[Dict[str, Any]] = []
    
    async def connect(self) -> bool:
        try:
            success = await self.client.connect(self.url, self.token)
            if success:
                self.connected = True
                self.available_tools = await self.client.list_tools()
            return success
        except Exception as e:
            logger.error(f"Error connecting to Brave Search MCP server at {self.url}: {e}")
            self.connected = False
            return False
    
    async def disconnect(self) -> bool:
        try:
            success = await self.client.disconnect()
            self.connected = not success
            return success
        except Exception as e:
            logger.error(f"Error disconnecting from Brave Search MCP server at {self.url}: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "connected": self.connected,
            "tool_count": len(self.available_tools),
            "has_token": self.token is not None
        }


class BraveSearchSessionManager:
    """Manager for Brave Search MCP server sessions."""
    
    def __init__(self, brave_search_client: BraveSearchClient):
        self._brave_search_client = brave_search_client
        self.current_session: Optional[BraveSearchServerSession] = None
        self.mcp_client = brave_search_client  # Alias for compatibility
    
    @property
    def brave_search_client(self) -> BraveSearchClient:
        return self._brave_search_client
    
    async def connect(self, url: str, token: Optional[str] = None, token_env_var: Optional[str] = None) -> Dict[str, Any]:
        if not url:
            return {
                "success": False,
                "message": "No URL provided for Brave Search MCP server"
            }
        
        if self.current_session and self.current_session.connected:
            await self.disconnect()
        
        actual_token = token
        if token_env_var:
            actual_token = os.environ.get(token_env_var)
            if not actual_token:
                return {
                    "success": False,
                    "message": f"Environment variable {token_env_var} not found or empty"
                }
        
        self.current_session = BraveSearchServerSession(self.brave_search_client, url, actual_token)
        success = await self.current_session.connect()
        
        if success:
            return {
                "success": True,
                "message": f"Connected to Brave Search MCP server at {self.current_session.url}",
                "tool_count": len(self.current_session.available_tools)
            }
        else:
            self.current_session = None
            return {
                "success": False,
                "message": f"Failed to connect to Brave Search MCP server at {url}. Verify the URL and authentication."
            }
    
    async def disconnect(self) -> Dict[str, Any]:
        if not self.current_session:
            return {
                "success": False,
                "message": "Not connected to Brave Search MCP server"
            }
        
        url = self.current_session.url
        success = await self.current_session.disconnect()
        
        if success:
            self.current_session = None
            return {
                "success": True,
                "message": f"Disconnected from Brave Search MCP server at {url}"
            }
        else:
            return {
                "success": False,
                "message": f"Failed to disconnect from Brave Search MCP server at {url}"
            }
    
    async def disconnect_all(self) -> None:
        if self.current_session:
            await self.disconnect()
    
    def get_status(self) -> Dict[str, Any]:
        if not self.current_session:
            return {
                "connected": False,
                "message": "Not connected to Brave Search MCP server"
            }
        
        session_status = self.current_session.get_status()
        return {
            "connected": session_status["connected"],
            "url": session_status["url"],
            "tool_count": session_status["tool_count"],
            "has_token": session_status["has_token"]
        }
    
    def is_connected(self) -> bool:
        return self.current_session is not None and self.current_session.connected
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        if not self.is_connected():
            return []
        return self.current_session.available_tools
    
    async def call_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        if not self.is_connected():
            return {
                "success": False,
                "message": "Not connected to Brave Search MCP server"
            }
        
        try:
            result = await self.brave_search_client.call_tool(tool_name, args)
            return {
                "success": True,
                "result": result
            }
        except Exception as e:
            logger.error(f"Error calling Brave Search tool {tool_name}: {e}")
            if hasattr(e, '__dict__'):
                logger.error(f"Error details: {e.__dict__}")
            return {
                "success": False,
                "message": f"Error calling Brave Search tool {tool_name}: {str(e)}"
            }