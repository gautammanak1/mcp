# MCP Client Agent

A uagents-based agent that connects to Model Context Protocol (MCP) servers via SSE transport and provides a chat interface for interacting with these servers.

## Features

- Connect to any MCP server via SSE transport
- Chat interface for interacting with MCP servers
- Structured commands for clear interaction
- Maintains state between messages to remember server connections
- Support for authentication tokens

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd asi_mcp

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Starting the Agent

```python
from asi_mcp.agent import MCPClientAgent

# Create and start the agent
agent = MCPClientAgent()
agent.start()
```

### Supported Commands

The agent supports the following structured commands:

#### 1. Connect to an MCP Server

```
!connect [url] [--token TOKEN] [--token-env-var VAR_NAME]
```

Examples:
```
!connect http://localhost:8000
!connect https://mcp-server.example.com --token your-auth-token
!connect https://mcp-server.example.com --token-env-var MCP_TOKEN
```

#### 2. Disconnect from the Current Server

```
!disconnect
```

#### 3. List Available Tools

```
!list
```

#### 4. Call a Tool with JSON Arguments

```
!call [tool_name] [json_args]
```

Example:
```
!call search_models {"query": "stable-diffusion"}
```

#### 5. Call a Tool with Shorthand Syntax

```
!shorthand [tool_name] [arg1=value1] [arg2=value2] ...
```

Example:
```
!shorthand search_models query="stable-diffusion"
```

#### 6. Check Connection Status

```
!status
```

#### 7. Get Help

```
!help
```

## Examples

### Simple Chat Client

```python
from asi_mcp.agent import MCPClientAgent

agent = MCPClientAgent()

# Connect to an MCP server
agent.process_message("!connect http://localhost:8000")

# List available tools
agent.process_message("!list")

# Call a tool
agent.process_message("!call search_models {\"query\": \"stable-diffusion\"}")

# Use shorthand syntax
agent.process_message("!shorthand search_models query=\"stable-diffusion\"")

# Check status
agent.process_message("!status")

# Disconnect
agent.process_message("!disconnect")
```

## License

[MIT License](LICENSE)