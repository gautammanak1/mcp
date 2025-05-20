import asyncio
import logging
import os
from typing import Dict, Optional, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Note: BraveSearchClient is imported from the above code
from brave_client import BraveSearchClient


class BraveSearchServerSession:
    """Class representing a session with the Brave Search MCP server."""
    
    def __init__(self, client: BraveSearchClient, url: str, token: Optional[str] = None):
        """
        Initialize a Brave Search server session.
        
        Args:
            client: The Brave Search client instance
            url: The URL of the Brave Search MCP server
            token: Optional authentication token
        """
        self.url = url
        self.client = client
        self.token = token
        self.connected = False
        self.available_tools: List[Dict[str, Any]] = []
    
    async def connect(self) -> bool:
        """
        Connect to the Brave Search MCP server.
        
        Returns:
            True if connection was successful, False otherwise
        """
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
        """
        Disconnect from the Brave Search MCP server.
        
        Returns:
            True if disconnection was successful, False otherwise
        """
        try:
            success = await self.client.disconnect()
            self.connected = not success
            return success
        except Exception as e:
            logger.error(f"Error disconnecting from Brave Search MCP server at {self.url}: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the status of the Brave Search session.
        
        Returns:
            A dictionary with session status information
        """
        return {
            "url": self.url,
            "connected": self.connected,
            "tool_count": len(self.available_tools),
            "has_token": self.token is not None
        }


class BraveSearchSessionManager:
    """Manager for Brave Search MCP server sessions."""
    
    def __init__(self, brave_search_client: BraveSearchClient):
        """
        Initialize the Brave Search session manager.
        
        Args:
            brave_search_client: The Brave Search client instance
        """
        self._brave_search_client = brave_search_client
        self.current_session: Optional[BraveSearchServerSession] = None
        # Add mcp_client to match expected attribute
        self.mcp_client = brave_search_client  # Alias for compatibility
    
    @property
    def brave_search_client(self) -> BraveSearchClient:
        """
        Get the Brave Search client instance.
        
        Returns:
            The Brave Search client instance
        """
        return self._brave_search_client
    
    async def connect(self, url: str, token: Optional[str] = None, token_env_var: Optional[str] = None) -> Dict[str, Any]:
        """
        Connect to the Brave Search MCP server.
        
        Args:
            url: The URL of the Brave Search MCP server
            token: Optional authentication token
            token_env_var: Optional environment variable name for token
            
        Returns:
            A dictionary with connection result information
        """
        if not url:
            return {
                "success": False,
                "message": "No URL provided for Brave Search MCP server"
            }
        
        # Disconnect from any existing session
        if self.current_session and self.current_session.connected:
            await self.disconnect()
        
        # Get token from environment variable if specified
        actual_token = token
        if token_env_var:
            actual_token = os.environ.get(token_env_var)
            if not actual_token:
                return {
                    "success": False,
                    "message": f"Environment variable {token_env_var} not found or empty"
                }
        
        # Create a new session
        self.current_session = BraveSearchServerSession(self.brave_search_client, url, actual_token)
        
        # Connect to the server
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
                "message": f"Failed to connect to Brave Search MCP server at {url}"
            }
    
    async def disconnect(self) -> Dict[str, Any]:
        """
        Disconnect from the Brave Search MCP server.
        
        Returns:
            A dictionary with disconnection result information
        """
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
        """Disconnect from the Brave Search MCP server."""
        if self.current_session:
            await self.disconnect()
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current Brave Search connection status.
        
        Returns:
            A dictionary with connection status information
        """
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
        """
        Check if connected to the Brave Search MCP server.
        
        Returns:
            True if connected, False otherwise
        """
        return self.current_session is not None and self.current_session.connected
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        List available tools on the Brave Search MCP server.
        
        Returns:
            A list of available tools
        """
        if not self.is_connected():
            return []
        
        return self.current_session.available_tools
    
    async def call_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a tool on the Brave Search MCP server.
        
        Args:
            tool_name: The name of the tool to call
            args: The arguments to pass to the tool
            
        Returns:
            The result of the tool call
        """
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
        