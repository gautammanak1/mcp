"""
Session Manager - Maintain connection state with MCP servers

This module contains the SessionManager class that maintains connection state
with MCP servers, handles connection/disconnection, and stores active sessions.
"""

import asyncio
import logging
import os
from typing import Dict, Optional, Any, List

from asi_mcp.mcp_client import MCPClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ServerSession:
    """Class representing a session with an MCP server."""
    
    def __init__(self, url: str, client: MCPClient, token: Optional[str] = None):
        """
        Initialize a server session.
        
        Args:
            url: The URL of the MCP server
            client: The MCP client instance
            token: Optional authentication token
        """
        self.url = url
        self.client = client
        self.token = token
        self.connected = False
        self.available_tools: List[Dict[str, Any]] = []
    
    async def connect(self) -> bool:
        """
        Connect to the MCP server.
        
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
            logger.error(f"Error connecting to {self.url}: {e}")
            self.connected = False
            return False
    
    async def disconnect(self) -> bool:
        """
        Disconnect from the MCP server.
        
        Returns:
            True if disconnection was successful, False otherwise
        """
        try:
            success = await self.client.disconnect()
            self.connected = not success
            return success
        except Exception as e:
            logger.error(f"Error disconnecting from {self.url}: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the status of the session.
        
        Returns:
            A dictionary with session status information
        """
        return {
            "url": self.url,
            "connected": self.connected,
            "tool_count": len(self.available_tools),
            "has_token": self.token is not None
        }


class SessionManager:
    """Manager for MCP server sessions."""
    
    def __init__(self, mcp_client: MCPClient):
        """
        Initialize the session manager.
        
        Args:
            mcp_client: The MCP client instance
        """
        self._mcp_client = mcp_client
        self.current_session: Optional[ServerSession] = None
    
    @property
    def mcp_client(self) -> MCPClient:
        """
        Get the MCP client instance.
        
        Returns:
            The MCP client instance
        """
        return self._mcp_client
    
    async def connect(self, url: str, token: Optional[str] = None, token_env_var: Optional[str] = None) -> Dict[str, Any]:
        """
        Connect to an MCP server.
        
        Args:
            url: The URL of the MCP server
            token: Optional authentication token
            token_env_var: Optional environment variable name for token
            
        Returns:
            A dictionary with connection result information
        """
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
        self.current_session = ServerSession(url, self.mcp_client, actual_token)
        
        # Connect to the server
        success = await self.current_session.connect()
        
        if success:
            return {
                "success": True,
                "message": f"Connected to {url}",
                "tool_count": len(self.current_session.available_tools)
            }
        else:
            self.current_session = None
            return {
                "success": False,
                "message": f"Failed to connect to {url}"
            }
    
    async def disconnect(self) -> Dict[str, Any]:
        """
        Disconnect from the current MCP server.
        
        Returns:
            A dictionary with disconnection result information
        """
        if not self.current_session:
            return {
                "success": False,
                "message": "Not connected to any server"
            }
        
        url = self.current_session.url
        success = await self.current_session.disconnect()
        
        if success:
            self.current_session = None
            return {
                "success": True,
                "message": f"Disconnected from {url}"
            }
        else:
            return {
                "success": False,
                "message": f"Failed to disconnect from {url}"
            }
    
    async def disconnect_all(self) -> None:
        """Disconnect from all MCP servers."""
        if self.current_session:
            await self.disconnect()
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current connection status.
        
        Returns:
            A dictionary with connection status information
        """
        if not self.current_session:
            return {
                "connected": False,
                "message": "Not connected to any server"
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
        Check if connected to an MCP server.
        
        Returns:
            True if connected, False otherwise
        """
        return self.current_session is not None and self.current_session.connected
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        List available tools on the connected MCP server.
        
        Returns:
            A list of available tools
        """
        if not self.is_connected():
            return []
        
        return self.current_session.available_tools
    
    async def call_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a tool on the connected MCP server.
        
        Args:
            tool_name: The name of the tool to call
            args: The arguments to pass to the tool
            
        Returns:
            The result of the tool call
        """
        if not self.is_connected():
            return {
                "success": False,
                "message": "Not connected to any server"
            }
        
        try:
            result = await self._mcp_client.call_tool(tool_name, args)
            return {
                "success": True,
                "result": result
            }
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            return {
                "success": False,
                "message": f"Error calling tool {tool_name}: {str(e)}"
            }