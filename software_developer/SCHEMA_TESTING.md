# Testing the Schema Command

This document provides instructions for testing the schema command functionality in the MCP Client Agent.

## Overview

The schema command allows clients to request detailed schema information for any tool available on a connected MCP server. This is useful for understanding how to use tools correctly, exploring available options, and seeing the full schema details.

## Test Clients

We've provided two test clients to verify the schema command functionality:

1. **Basic Test Client** (`test_schema_client.py`): Tests the natural language schema command for a single tool.
2. **Comprehensive Test Client** (`test_schema_comprehensive.py`): Tests both natural language and structured schema commands for multiple tools.

## Prerequisites

Before running the tests, ensure:

1. The MCP Client Agent is running:
   ```bash
   python asi_mcp/run_agent.py
   ```

2. Note the agent address printed in the logs. It should look like:
   ```
   AGENT ADDRESS: agent1qfjyk5q9dq2m57uyqzctsmeruhy27v62vl53mjl35n6dvpjfwlwq2p5tmd2
   ```

3. Update the `MCP_CLIENT_AGENT_ADDRESS` variable in the test scripts with your agent's address.

## Running the Tests

### Basic Test

The basic test connects to the MCP server, requests the schema for the `stability-ai-text-to-image` tool using the natural language command, and then disconnects.

```bash
python asi_mcp/test_schema_client.py
```

### Comprehensive Test

The comprehensive test:
1. Connects to the MCP server
2. Lists available tools
3. Tests the natural language schema command for the first tool
4. Tests the structured schema command for the second tool
5. Disconnects

```bash
python asi_mcp/test_schema_comprehensive.py
```

## Expected Results

When running the tests, you should see:

1. Successful connection to the MCP server
2. Schema information returned for the requested tools
3. No validation errors in the logs
4. Proper formatting of the schema information

The schema information should include:
- Parameter details (names, types, descriptions)
- Required vs. optional parameters
- Default values for optional parameters
- Constraints (min/max values, formats, etc.)
- Example usage
- Raw schema

## Troubleshooting

If you encounter issues:

1. **Connection Errors**: Ensure the MCP Client Agent is running and the agent address is correct.
2. **Validation Errors**: Check the logs for validation errors. If you see errors like `Missing required parameters: name, inputSchema`, the schema cleaning may not be working correctly.
3. **Empty Schema**: If the schema is empty, the tool may not provide schema information or the schema extraction may be failing.

## Manual Testing

You can also test the schema command manually using the chat interface:

1. Connect to the MCP server:
   ```
   connect to https://cloud.activepieces.com/api/v1/mcp/RerVk5mI66ZTiq9Xc8aIu/sse
   ```

2. List available tools:
   ```
   list tools
   ```

3. Request the schema for a tool:
   ```
   schema stability-ai-text-to-image
   ```

4. Disconnect:
   ```
   disconnect