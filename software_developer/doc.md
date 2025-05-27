# MCP Client Agent Documentation

## Overview

The MCP Client Agent is a **uagents-based agent** that connects to Model Context Protocol (MCP) servers via SSE transport and provides a chat interface for interacting with these servers. **Fetch.ai has made it incredibly easy to convert any MCP server into a uagent**, enabling seamless integration between MCP protocols and the uagents ecosystem.


This codebase demonstrates how ** existing MCP server can be converted into a uagent** with minimal code changes. The main conversion happens in the `agent.py` file where:

1.  A standard uagents `Agent` is created with mailbox enabled
2.  MCP-specific components are initialized (client, session manager, etc.)
3.  Chat protocol handlers are set up to process MCP commands
4.  The agent includes both custom and standard chat protocols


## File Structure and Core Functions

### 📁 `__init__.py`

**Purpose**: Package initialization and exports

```python
# Lines 1-8: Package exports
from .agent import MCPClientAgent
from .command_parser import CommandParser, CommandType, ParsedCommand
from .session_manager import SessionManager, ServerSession
from .mcp_client import MCPClient
from .result_formatter import ResultFormatter
from .chat_handler import ChatHandler

__version__ = "0.1.0"
```

### 📁 `agent.py`

**Main Agent Class - The Heart of MCP to uAgent Conversion**

#### `class MCPClientAgent`

**Purpose**: Main agent class that bridges MCP servers with uagents framework

**Key Functions**:

- **`__init__()`** 

```python
def __init__(self, name: str = "software_developer_agent", seed: Optional[str] = None, port: int = 8000):
    """Initialize the Software Developer Agent."""
    self.name = name
    self.seed = seed
    self.port = port
    
    # Lines 29-34: Create the uagents Agent with mailbox enabled
    self.agent = Agent(
        name=name,
        seed=seed,
        port=port,
        mailbox=True,
    )
    
    # Line 37: Fund the agent if needed
    fund_agent_if_low(self.agent.wallet.address())
    
    # Lines 39-47: Initialize MCP components
    self.result_formatter = ResultFormatter()
    self.mcp_client = MCPClient()
    self.session_manager = SessionManager(self.mcp_client)
    self.command_parser = CommandParser()
    self.chat_handler = ChatHandler(
        command_parser=self.command_parser,
        session_manager=self.session_manager,
        result_formatter=self.result_formatter
    )
```


- **`start()`** 

```python
def start(self):
    """Start the agent."""
    logger.info(f"Starting Software Developer Agent on port {self.port}")
    self.agent.run()
```


- **`process_message()`** 

```python
async def process_message(self, message: str, sender: Optional[str] = None) -> str:
    """Process a chat message and return a response."""
    return await self.chat_handler.process_message(message, sender)
```




### 📁 `chat_handler.py`

**Message Processing Engine**

#### `class ChatHandler`

**Purpose**: Processes incoming chat messages and converts them to MCP operations

**Key Functions**:

- **`process_message()`** 

```python
async def process_message(self, message: str, sender: Optional[str] = None) -> str:
    """Process a chat message and return a response."""
    logger.info(f"Processing message from {sender or 'unknown'}: {message}")
    
    # Line 42: Check if the message is a command
    if not self.command_parser.is_command(message):
        return self._handle_non_command_message(message)
    
    # Line 45: Parse the command
    parsed_command = self.command_parser.parse_command(message)
    
    # Lines 47-60: Handle the command based on its type
    if parsed_command.command_type == CommandType.CONNECT:
        return await self._handle_connect_command(parsed_command)
    elif parsed_command.command_type == CommandType.DISCONNECT:
        return await self._handle_disconnect_command(parsed_command)
    elif parsed_command.command_type == CommandType.LIST:
        return await self._handle_list_command(parsed_command)
    elif parsed_command.command_type == CommandType.CALL:
        return await self._handle_call_command(parsed_command)
```


- **`_handle_connect_command()`** 

```python
async def _handle_connect_command(self, command: ParsedCommand) -> str:
    """Handle a connect command."""
    if not command.args:
        return self.result_formatter.format_error("URL is required for connect command")
    
    # Lines 91-93: Extract connection parameters
    url = command.args[0]
    token = command.kwargs.get("token")
    token_env_var = command.kwargs.get("token_env_var")
    
    # Lines 95-97: Execute connection
    result = await self.session_manager.connect(url, token, token_env_var)
    return self.result_formatter.format_connect_result(result)
```


- **`_handle_call_command()`** 

```python
async def _handle_call_command(self, command: ParsedCommand) -> str:
    """Handle a call command."""
    if not self.session_manager.is_connected():
        return self.result_formatter.format_not_connected_error()
    
    if not command.args:
        return self.result_formatter.format_error("Tool name is required for call command")
    
    # Lines 149-150: Extract tool parameters
    tool_name = command.args[0]
    args = command.kwargs.get("args", {})
    
    try:
        # Line 153: Get the tool schema
        schema = await self.session_manager.mcp_client.get_schema(tool_name)
        
        # Line 155: Validate and auto-fill parameters
        validated_args = await self._validate_and_fill_parameters(tool_name, args)
        
        # Line 158: Call the tool with validated arguments
        result = await self.session_manager.call_tool(tool_name, validated_args)
        return self.result_formatter.format_tool_call_result(result)
    except ValueError as e:
        # Lines 161-164: Handle parameter validation errors
        logger.error(f"Parameter validation error for {tool_name}: {e}")
        return self.result_formatter.format_parameter_validation_error(tool_name, str(e),
            await self.session_manager.mcp_client.get_schema(tool_name))
```




### 📁 `chat_proto.py`

**Natural Language Interface**

#### Chat Protocol Implementation

**Purpose**: Enables natural language interaction with MCP servers

**Key Pattern Definitions** 

```python
# Command patterns for MCP operations
CONNECT_PATTERN = r"^connect to\s+(.+?)(?:\s+with token\s+(.+))?$"
DISCONNECT_PATTERN = r"^disconnect$"
LIST_PATTERN = r"^list tools$"
CALL_PATTERN = r"^call\s+(\S+)\s+(.+)$"
STATUS_PATTERN = r"^status$"
HELP_PATTERN = r"^help(?:\s+(\S+))?$"
SCHEMA_PATTERN = r"^schema\s+(\S+)$"
```

**Key Functions**:

- **`handle_chat_message()`** 

```python
@chat_proto.on_message(ChatMessage)
async def handle_chat_message(ctx: Context, sender: str, msg: ChatMessage):
    """Handles incoming chat messages."""
    # Line 48: Send acknowledgement
    await ctx.send(
        sender,
        ChatAcknowledgement(
            timestamp=datetime.utcnow(), acknowledged_msg_id=msg.msg_id
        ),
    )
    
    # Lines 55-70: Process different content types
    for item in msg.content:
        if isinstance(item, StartSessionContent):
            logger.info(f"Chat session started with {sender}")
            # Send welcome message
        elif isinstance(item, TextContent):
            logger.info(f"Received chat message from {sender}: {item.text}")
            
            # Lines 75-85: Check for connect command
            connect_match = re.match(CONNECT_PATTERN, text_lower, re.IGNORECASE)
            if connect_match:
                # Find the same pattern in the original text to preserve case
                original_match = re.match(CONNECT_PATTERN, text, re.IGNORECASE)
                url = original_match.group(1).strip() if original_match else connect_match.group(1).strip()
                token = original_match.group(2).strip() if original_match and original_match.group(2) else None
```




### 📁 `command_parser.py`

**Structured Command Processing**

#### `class CommandParser`

**Purpose**: Parses structured commands from chat messages

**Key Functions**:

- **`is_command()`** 

```python
def is_command(self, message: str) -> bool:
    """Check if a message is a command."""
    return message.strip().startswith(self.COMMAND_PREFIX)
```


- **`parse_command()`** 

```python
def parse_command(self, message: str) -> ParsedCommand:
    """Parse a command from a message."""
    message = message.strip()
    
    if not self.is_command(message):
        return ParsedCommand(CommandType.UNKNOWN, raw_command=message)
    
    # Lines 68-70: Extract command type
    parts = message.split(maxsplit=1)
    cmd = parts[0][1:]  # Remove the prefix
    
    try:
        command_type = CommandType(cmd)
    except ValueError:
        return ParsedCommand(CommandType.UNKNOWN, raw_command=message)
```


- **`_parse_connect_command()`** 

```python
def _parse_connect_command(self, message: str) -> ParsedCommand:
    """Parse a connect command. Format: !connect [url] [--token TOKEN] [--token-env-var VAR_NAME]"""
    match = re.match(self.command_patterns[CommandType.CONNECT], message)
    if not match:
        return ParsedCommand(CommandType.UNKNOWN, raw_command=message)
    
    # Lines 102-105: Parse arguments using shlex to handle quoted strings
    try:
        args = shlex.split(match.group(1))
    except ValueError:
        return ParsedCommand(CommandType.UNKNOWN, raw_command=message)
    
    # Lines 107-118: Extract URL and options
    url = args[0] if args else ""
    kwargs = {}
    
    i = 1
    while i < len(args):
        if args[i] == "--token" and i + 1 < len(args):
            kwargs["token"] = args[i + 1]
            i += 2
        elif args[i] == "--token-env-var" and i + 1 < len(args):
            kwargs["token_env_var"] = args[i + 1]
            i += 2
```




### 📁 `mcp_client.py`

**MCP Server Communication**

#### `class MCPClient`

**Purpose**: Wrapper for fastmcp Client to handle MCP server communication

**Key Functions**:

- **`connect()`** 

```python
async def connect(self, url: str, token: Optional[str] = None) -> bool:
    """Connect to an MCP server."""
    try:
        logger.info(f"Connecting to MCP server at {url}")
        
        # Lines 36-37: Use SSETransport explicitly for SSE connections
        transport = SSETransport(url)
        self.client = Client(transport)
        
        # Line 40: Store the URL for later use
        self.server_url = url
        
        # Line 43: Initialize the client using the async context manager
        await self.client.__aenter__()
        
        # Lines 45-46: Test the connection by listing tools
        tools = await self.client.list_tools()
        self.tools = tools
        
        self.connected = True
        logger.info(f"Connected to MCP server at {url}")
        return True
```


- **`call_tool()`** 

```python
async def call_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Call a tool on the connected MCP server."""
    if not self.connected or not self.client:
        raise ConnectionError("Not connected to any MCP server")
    
    try:
        logger.info(f"Calling tool '{tool_name}' with arguments: {args}")
        result = await self.client.call_tool(tool_name, args)
        return result
    except Exception as e:
        logger.error(f"Failed to call tool {tool_name}: {e}")
        if hasattr(e, '__dict__'):
            logger.error(f"Error details: {e.__dict__}")
        raise
```


- **`list_tools()`** 
```python
async def list_tools(self) -> List[Dict[str, Any]]:
    """List available tools on the connected MCP server."""
    if not self.connected or not self.client:
        logger.warning("Not connected to any MCP server")
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
```




### 📁 `session_manager.py`

**Connection State Management**

#### `class SessionManager`

**Purpose**: Maintains connection state with MCP servers

**Key Functions**:

- **`connect()`** 

```python
async def connect(self, url: str, token: Optional[str] = None, token_env_var: Optional[str] = None) -> Dict[str, Any]:
    """Connect to an MCP server."""
    # Lines 75-77: Disconnect from any existing session
    if self.current_session and self.current_session.connected:
        await self.disconnect()
    
    # Lines 79-85: Get token from environment variable if specified
    actual_token = token
    if token_env_var:
        actual_token = os.environ.get(token_env_var)
        if not actual_token:
            return {
                "success": False,
                "message": f"Environment variable {token_env_var} not found or empty"
            }
    
    # Lines 87-88: Create a new session
    self.current_session = ServerSession(url, self.mcp_client, actual_token)
    
    # Lines 90-91: Connect to the server
    success = await self.current_session.connect()
```


- **`disconnect()`** 

```python
async def disconnect(self) -> Dict[str, Any]:
    """Disconnect from the current MCP server."""
    if not self.current_session:
        return {
            "success": False,
            "message": "Not connected to any server"
        }
    
    # Lines 115-116: Execute disconnection
    url = self.current_session.url
    success = await self.current_session.disconnect()
    
    if success:
        self.current_session = None
        return {
            "success": True,
            "message": f"Disconnected from {url}"
        }
```




### 📁 `result_formatter.py`

**Response Formatting**

#### `class ResultFormatter`

**Purpose**: Formats MCP responses into readable Markdown And Json

**Key Functions**:

- **`format_tool_call_result()`** 

```python
def format_tool_call_result(self, result: Dict[str, Any]) -> Dict[str, str]:
    """Format a tool call result into JSON and Markdown representations."""
    output = {"json": "", "markdown": ""}

    if not result.get("success", False):
        markdown = f"# ❌ Tool Call Failed\n\n**Reason:** {result.get('message', 'Tool call failed')}"
        json_output = {"status": "failed", "message": result.get("message", 'Tool call failed')}
        output["json"] = json.dumps(json_output, indent=self.indent_size)
        output["markdown"] = markdown
        return output

    # Lines 160-170: Process successful results
    tool_result = self._handle_text_content(result.get("result", {}))
    if isinstance(tool_result, (dict, list)):
        result_type = "JSON"
        formatted_json = self.format_json(tool_result)
        markdown_summary = self.json_to_markdown(tool_result)
        result_display = self._markdown_code_block(formatted_json)
```


- **`json_to_markdown()`** 

```python
def json_to_markdown(self, json_data: Union[str, Dict, List]) -> str:
    """Converts a JSON string or dictionary to a Markdown table."""
    try:
        if isinstance(json_data, str):
            json_data = json.loads(json_data)
        elif not isinstance(json_data, (dict, list)):
            return "Invalid JSON data."
        
        #  Process data structure
        if isinstance(json_data, dict):
            json_data = self._flatten_dict(json_data)
            json_data = [json_data]
        elif not isinstance(json_data, list):
            json_data = [json_data]
        
        #  Generate table
        table = []
        headers = []
        for item in json_data:
            if isinstance(item, dict):
                if not headers:
                    headers = list(item.keys())
                table.append([item.get(h, '') for h in headers])
```




### 📁 `schema_utils.py`

**Schema Handling Utilities**

#### Schema Processing Functions

**Purpose**: Handle MCP tool schemas for parameter validation

**Key Functions**:

- **`get_schema_from_tool()`** 

```python
def get_schema_from_tool(tool: Any, tool_name: str) -> Dict[str, Any]:
    """Extract schema information from a tool object."""
    # Lines 20-30: Try different attribute names for schema
    if hasattr(tool, 'schema'):
        schema = _extract_schema_value(tool.schema, tool_name, 'schema')
        return _clean_schema(schema)
    elif hasattr(tool, 'parameters'):
        schema = _extract_schema_value(tool.parameters, tool_name, 'parameters')
        return _clean_schema(schema)
    elif hasattr(tool, 'parameter_schema'):
        schema = _extract_schema_value(tool.parameter_schema, tool_name, 'parameter_schema')
        return _clean_schema(schema)
    elif hasattr(tool, 'inputSchema'):
        schema = _extract_schema_value(tool.inputSchema, tool_name, 'inputSchema')
        return _clean_schema(schema)
```


- **`validate_schema_structure()`** 

```python
def validate_schema_structure(schema: Dict[str, Any]) -> bool:
    """Validate that a schema has the expected structure."""
    if not isinstance(schema, dict):
        return False
    
    # Line 127: Check for properties field (required for JSON Schema)
    if 'properties' not in schema:
        return False
    
    # Line 131: Ensure properties is a dictionary
    if not isinstance(schema['properties'], dict):
        return False
    
    # Lines 135-136: If required field exists, ensure it's a list
    if 'required' in schema and not isinstance(schema['required'], list):
        return False
```




### 📁 `run.py`

**Agent Startup Script**

#### Main Execution

**Purpose**: Starts the MCP Client Agent

```python
# Lines 10-20: Main execution block
if __name__ == "__main__":
    logger.info("Starting Software Developer Agent with Chat Protocol support...")
    
    # Lines 13-17: Create and start the agent with a specific seed phrase
    agent = MCPClientAgent(
        name="Software Developer Agent",
        seed="Software Developer",
        port=8000
    )
    
    # Lines 19-25: Log agent information
    agent_address = agent.agent.address
    logger.info("=" * 50)
    logger.info(f"AGENT ADDRESS: {agent_address}")
    logger.info("=" * 50)
    logger.info("Use this address in the test client when prompted.")
    
    try:
        # Line 30: This will block until the agent is stopped
        agent.start()
    except KeyboardInterrupt:
        logger.info("Stopping MCP Client Agent...")
        agent.stop()
        logger.info("MCP Client Agent stopped")
```

## How to Convert Any MCP to uAgent

### Required Changes (Minimal):

1. **In `agent.py` **:

```python
# Replace with your MCP server details
self.agent = Agent(
    name="your_mcp_agent_name",      # Line 30: Change agent name
    seed="your_seed",                # Line 31: Change seed
    port=your_port,                  # Line 32: Change port
    mailbox=True,                    # Line 33: Keep mailbox enabled
)
```


2. **In `mcp_client.py` **:

```python
# Update connection URL for your MCP server
transport = SSETransport(url)        # Line 36: Your MCP server URL
self.client = Client(transport)      # Line 37: Create client
```


3. **In `run.py` **:

```python
# Configure for your specific MCP
agent = MCPClientAgent(
    name="Your MCP Agent Name",      # Line 15: Your agent name
    seed="your_unique_seed",         # Line 16: Your unique seed
    port=8000                        # Line 17: Your preferred port
)
```






## Key Benefits of This Approach

1. **Universal Compatibility**:  MCP server can become a uagent with just 3 line changes
2. **Natural Language Interface**: Users can interact conversationally via `chat_proto.py`
3. **Automatic Parameter Validation**: Schema-based validation with auto-fill ( `chat_handler.py`)
4. **Rich Formatting**: Markdown responses with tables and code blocks (`result_formatter.py`)
5. **Session Management**: Persistent connections with state tracking (`session_manager.py`)


