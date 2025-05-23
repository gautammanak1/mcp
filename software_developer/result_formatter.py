"""
Result Formatter - Format MCP responses for chat in Markdown

This module contains the ResultFormatter class that formats MCP responses
into readable, Markdown-formatted chat messages. It handles different result types,
creates structured output with headers, lists, code blocks, and ensures consistent
formatting across all methods.
"""

import json
import logging
from typing import Dict, List, Any, Optional, Union
from tabulate import tabulate

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ResultFormatter:
    """Formatter for MCP responses and other outputs in Markdown and JSON formats."""
    
    def __init__(self, max_json_depth: int = 3, indent_size: int = 2):
        """
        Initialize the result formatter.
        
        Args:
            max_json_depth: Maximum depth for JSON formatting
            indent_size: Number of spaces for indentation
        """
        self.max_json_depth = max_json_depth
        self.indent_size = indent_size
    
    def _markdown_code_block(self, content: str, lang: str = "json") -> str:
        """Wrap content in a Markdown code block."""
        return f"```{lang}\n{content}\n```"

    def _handle_text_content(self, data: Any) -> Any:
        """Convert TextContent objects or other non-serializable objects to a serializable format."""
        if hasattr(data, '__class__') and data.__class__.__name__ == 'TextContent':
            # Extract the text attribute from TextContent
            text_content = getattr(data, 'text', str(data))
            # Try to parse as JSON if possible
            try:
                return json.loads(text_content)
            except json.JSONDecodeError:
                return text_content
        elif isinstance(data, dict):
            return {key: self._handle_text_content(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._handle_text_content(item) for item in data]
        return data

    def _flatten_dict(self, d: Dict, parent_key: str = '', sep: str = '.') -> Dict:
        """Flatten a nested dictionary for table display."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    def json_to_markdown(self, json_data: Union[str, Dict, List]) -> str:
        """
        Converts a JSON string or dictionary to a Markdown table.
        
        Args:
            json_data: JSON string or parsed JSON data (dict or list)
        
        Returns:
            Markdown table as a string
        """
        try:
            if isinstance(json_data, str):
                json_data = json.loads(json_data)
            elif not isinstance(json_data, (dict, list)):
                return "Invalid JSON data."
            
            if isinstance(json_data, dict):
                # Flatten nested dictionary for table display
                json_data = self._flatten_dict(json_data)
                json_data = [json_data]
            elif not isinstance(json_data, list):
                json_data = [json_data]
            
            if not json_data:
                return "No data to display."
            
            table = []
            headers = []
            for item in json_data:
                if isinstance(item, dict):
                    if not headers:
                        headers = list(item.keys())
                    table.append([item.get(h, '') for h in headers])
                else:
                    table.append([str(item)])
                    headers = ['Value']
            
            markdown_table = tabulate(table, headers=headers, tablefmt="pipe")
            return markdown_table
        except Exception as e:
            logger.error(f"Error converting JSON to Markdown table: {e}")
            return f"Error generating table: {str(e)}"

    def _json_to_markdown(self, data: Union[Dict, List, Any], depth: int = 0, prefix: str = "") -> str:
        """
        Convert a JSON object or array into a readable Markdown format (bullet-list style).

        Args:
            data: The JSON data to convert
            depth: Current depth level for recursion
            prefix: Prefix for Markdown list items (e.g., "- " or "  - ")

        Returns:
            Markdown-formatted string
        """
        data = self._handle_text_content(data)
        if depth >= self.max_json_depth:
            return f"{prefix}*Truncated due to depth limit*"

        if isinstance(data, dict):
            markdown = ""
            for key, value in data.items():
                if key == "text" and isinstance(value, str):
                    truncated_value = value[:200] + "..." if len(value) > 200 else value
                    markdown += f"{prefix}**{key.capitalize()}:**\n{truncated_value}\n\n"
                elif key == "usedTools" and isinstance(value, list):
                    markdown += f"{prefix}**Tools Used:**\n"
                    for idx, tool in enumerate(value, 1):
                        if isinstance(tool, dict):
                            tool_name = tool.get("tool", "Unknown Tool")
                            tool_input = tool.get("toolInput", {})
                            tool_output = tool.get("toolOutput", "No output")
                            markdown += f"{prefix}- **Tool {idx}:** `{tool_name}`\n"
                            if isinstance(tool_input, dict):
                                markdown += f"{prefix}  - **Input:**\n{self._json_to_markdown(tool_input, depth + 1, prefix + '    ')}\n"
                            if isinstance(tool_output, str) and tool_output.startswith("["):
                                markdown += f"{prefix}  - **Output:** *Truncated list of search results*\n"
                            else:
                                markdown += f"{prefix}  - **Output:** {tool_output}\n"
                        else:
                            markdown += f"{prefix}- **Tool {idx}:** {tool}\n"
                elif key in ["status", "question", "chatId", "sessionId", "memoryType", "isStreamValid"]:
                    markdown += f"{prefix}**{key.capitalize()}:** `{value}`\n"
                elif isinstance(value, (dict, list)):
                    nested = self._json_to_markdown(value, depth + 1, prefix + "  - ")
                    markdown += f"{prefix}**{key.capitalize()}:**\n{nested}\n"
                else:
                    markdown += f"{prefix}**{key.capitalize()}:** `{value}`\n"
            return markdown.strip()
        
        elif isinstance(data, list):
            if not data:
                return f"{prefix}*Empty list*"
            markdown = ""
            for idx, item in enumerate(data, 1):
                if isinstance(item, (dict, list)):
                    nested = self._json_to_markdown(item, depth + 1, prefix + "  - ")
                    markdown += f"{prefix}**Item {idx}:**\n{nested}\n"
                else:
                    markdown += f"{prefix}- `{item}`\n"
            return markdown.strip()
        
        elif isinstance(data, str):
            return f"{prefix}`{data}`"
        
        elif data is None:
            return f"{prefix}*None*"
        
        else:
            return f"{prefix}`{str(data)}`"

    def format_connect_result(self, result: Dict[str, Any]) -> str:
        """
        Format a connection result in Markdown.

        Args:
            result: The connection result

        Returns:
            Markdown-formatted message
        """
        if result.get("success", False):
            message = f"# ✅ Connection Successful\n\n**Message:** {result.get('message', 'Connected successfully')}\n"
            if "tool_count" in result:
                message += f"\n**Tools Available:** `{result['tool_count']}`\n\nRun the following to list them:\n\n{self._markdown_code_block('list', 'bash')}"
            return message
        return f"# ❌ Connection Failed\n\n**Reason:** {result.get('message', 'Connection failed')}"

    def format_disconnect_result(self, result: Dict[str, Any]) -> str:
        """
        Format a disconnection result in Markdown.

        Args:
            result: The disconnection result

        Returns:
            Markdown-formatted message
        """
        if result.get("success", False):
            return f"# ✅ Disconnection Successful\n\n**Message:** {result.get('message', 'Disconnected successfully')}"
        return f"# ❌ Disconnection Failed\n\n**Reason:** {result.get('message', 'Disconnection failed')}"

    def format_tool_list(self, tools: List[Any]) -> str:
        """
        Format a list of tools in Markdown.

        Args:
            tools: The list of tools

        Returns:
            Markdown-formatted message
        """
        if not tools:
            return "# 📭 No Tools Available\n\nNo tools are available. Ensure you're connected to an MCP server with:\n\n" + self._markdown_code_block("connect [url]", "bash")

        result = f"# 🧰 Available Tools ({len(tools)})\n"
        for tool in tools:
            name = getattr(tool, 'name', tool.get("name", "Unknown") if isinstance(tool, dict) else "Unknown")
            description = getattr(tool, 'description', tool.get("description", "No description available") if isinstance(tool, dict) else "No description available")

            result += f"\n---\n\n## 🔧 `{name}`\n\n**Description:** {description}\n\n"
            schema = None
            for attr in ['schema', 'parameters', 'parameter_schema', 'inputSchema']:
                if hasattr(tool, attr):
                    schema = getattr(tool, attr)
                    break
                elif isinstance(tool, dict) and attr in tool:
                    schema = tool[attr]
                    break

            if schema and isinstance(schema, dict):
                properties = schema.get("properties", {})
                required = schema.get("required", [])
                if properties:
                    result += f"### 🧾 Parameters\n\n"
                    for prop_name, prop_info in properties.items():
                        prop_type = prop_info.get("type", "any") if isinstance(prop_info, dict) else "any"
                        prop_desc = prop_info.get("description", "") if isinstance(prop_info, dict) else ""
                        is_required = prop_name in required
                        req_marker = " *(required)*" if is_required else ""
                        result += f"- `{prop_name}` ({prop_type}){req_marker}: {prop_desc}\n"
                else:
                    result += "_No parameters required._\n"
            else:
                result += "_No parameters defined._\n"

        call_example = 'call [tool_name] {"arg": "value"}'
        shorthand_example = 'shorthand [tool_name] arg="value"'
        result += f"\n---\n\n## 💡 Usage\n\n**Call a tool:**\n{self._markdown_code_block(call_example, 'bash')}\n\n**Shorthand:**\n{self._markdown_code_block(shorthand_example, 'bash')}"
        return result

    def format_tool_call_result(self, result: Dict[str, Any]) -> Dict[str, str]:
        """
        Format a tool call result into JSON and Markdown representations.

        Args:
            result: The tool call result dictionary

        Returns:
            A dictionary with 'json' and 'markdown' keys containing formatted outputs
        """
        output = {"json": "", "markdown": ""}

        if not result.get("success", False):
            markdown = f"# ❌ Tool Call Failed\n\n**Reason:** {result.get('message', 'Tool call failed')}"
            json_output = {"status": "failed", "message": result.get("message", 'Tool call failed')}
            output["json"] = json.dumps(json_output, indent=self.indent_size)
            output["markdown"] = markdown
            return output

        tool_result = self._handle_text_content(result.get("result", {}))
        if isinstance(tool_result, (dict, list)):
            result_type = "JSON"
            formatted_json = self.format_json(tool_result)
            # Use json_to_markdown for the summary table
            markdown_summary = self.json_to_markdown(tool_result)
            result_display = self._markdown_code_block(formatted_json)
        elif tool_result is None:
            result_type = "None"
            markdown_summary = "No result returned"
            result_display = markdown_summary
        else:
            result_type = "Text"
            # markdown_summary = str(tool_result)
            # result_display = markdown_summary

        markdown = (
            f"# ✅ Tool Call Successful\n\n"
            f"**Result Type:** {result_type}\n\n"
            # f"**Summary:**\n{markdown_summary}\n\n"
            f"**Full Result:**\n{result_display}"
        )

        json_output = {
            "status": "success",
            "result_type": result_type,
            # "summary": markdown_summary,
            "full_result": tool_result
        }

        try:
            output["json"] = json.dumps(json_output, indent=self.indent_size)
        except TypeError as e:
            logger.error(f"JSON serialization error: {e}")
            output["json"] = json.dumps({"status": "error", "message": f"Serialization failed: {str(e)}"}, indent=self.indent_size)
            output["markdown"] = f"# ❌ Serialization Error\n\n**Message:** {str(e)}"

        output["markdown"] = markdown
        return output

    def format_tool_call_result_json(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format a tool call result and return as JSON.

        Args:
            result: The tool call result

        Returns:
            Dictionary with structured result
        """
        if not result.get("success", False):
            return {
                "status": "failed",
                "reason": result.get("message", "Tool call failed")
            }

        tool_result = self._handle_text_content(result.get("result", {}))
        if isinstance(tool_result, (dict, list)):
            result_type = "JSON"
            formatted_result = tool_result
        elif tool_result is None:
            result_type = "None"
            formatted_result = "No result returned"
        else:
            result_type = "Text"
            formatted_result = str(tool_result)

        return {
            "status": "success",
            "result_type": result_type,
            "summary": self.json_to_markdown(tool_result) if isinstance(tool_result, (dict, list)) else formatted_result,
            "result": formatted_result
        }

    def format_status(self, result: Dict[str, Any]) -> str:
        """
        Format a connection status in Markdown.

        Args:
            result: The connection status

        Returns:
            Markdown-formatted message
        """
        if not result.get("connected", False):
            return f"# 📡 Connection Status\n\n**Status:** Not connected\n\n**Message:** {result.get('message', 'Not connected')}"

        message = f"# 📡 Connection Status\n\n**Status:** Connected to `{result.get('url', 'unknown')}`\n"
        if "tool_count" in result:
            message += f"\n**Available Tools:** `{result['tool_count']}`\n"
        message += f"\n**Authentication:** {'Using token' if result.get('has_token', False) else 'None'}"
        return message

    def format_error(self, message: str) -> str:
        """
        Format an error message in Markdown.

        Args:
            message: The error message

        Returns:
            Markdown-formatted message
        """
        return f"# ❌ Error\n\n**Message:** {message}"

    def format_parameter_validation_error(self, tool_name: str, message: str, schema: Optional[Dict[str, Any]] = None) -> str:
        """
        Format a parameter validation error message in Markdown.

        Args:
            tool_name: The name of the tool
            message: The error message
            schema: Optional schema information for the tool

        Returns:
            Markdown-formatted message
        """
        result = f"# ⚠️ Parameter Validation Error\n\n**Tool:** `{tool_name}`\n\n**Message:** {message}\n"
        if schema and isinstance(schema, dict):
            properties = schema.get("properties", {})
            required = schema.get("required", [])
            if properties:
                result += f"\n### 🧾 Required Parameters\n\n"
                for prop_name in required:
                    prop_info = properties.get(prop_name, {})
                    prop_type = prop_info.get("type", "any")
                    prop_desc = prop_info.get("description", "")
                    result += f"- `{prop_name}` ({prop_type}): {prop_desc}\n"

                example = {}
                for prop_name in required:
                    prop_info = properties.get(prop_name, {})
                    prop_type = prop_info.get("type", "any")
                    example[prop_name] = {
                        "string": "example_string",
                        "number": 42,
                        "integer": 42,
                        "boolean": True,
                        "array": [],
                        "object": {}
                    }.get(prop_type, "value")

                result += f"\n### 🧪 Example Usage\n\n{self._markdown_code_block(f'call {tool_name} {json.dumps(example, indent=2)}', 'bash')}"
        return result

    def format_json(self, data: Union[Dict, List, Any], depth: int = 0) -> str:
        """
        Format JSON data with proper indentation and truncation.

        Args:
            data: The data to format
            depth: Current depth level

        Returns:
            Formatted JSON string
        """
        data = self._handle_text_content(data)
        if depth >= self.max_json_depth:
            if isinstance(data, dict) and data:
                return "{...}"
            elif isinstance(data, list) and data:
                return "[...]"
        
        if isinstance(data, dict):
            if not data:
                return "{}"
            indent = " " * self.indent_size * depth
            next_indent = " " * self.indent_size * (depth + 1)
            parts = [f"{next_indent}\"{key}\": {self.format_json(value, depth + 1)}" for key, value in data.items()]
            return "{\n" + ",\n".join(parts) + f"\n{indent}}}"
        
        elif isinstance(data, list):
            if not data:
                return "[]"
            indent = " " * self.indent_size * depth
            next_indent = " " * self.indent_size * (depth + 1)
            parts = [f"{next_indent}{self.format_json(item, depth + 1)}" for item in data]
            return "[\n" + ",\n".join(parts) + f"\n{indent}]"
        
        elif isinstance(data, str):
            return f"\"{data}\""
        
        elif data is None:
            return "null"
        
        else:
            return str(data)

    def format_unknown_command(self, command: str) -> str:
        """
        Format an unknown command message in Markdown.

        Args:
            command: The unknown command

        Returns:
            Markdown-formatted message
        """
        return f"# ❓ Unknown Command\n\n**Command:** `{command}`\n\nTry running:\n\n{self._markdown_code_block('help', 'bash')}"

    def format_not_connected_error(self) -> str:
        """
        Format a not connected error message in Markdown.

        Returns:
            Markdown-formatted message
        """
        return f"# 🔌 Not Connected\n\nYou are not connected to any MCP server.\n\nConnect using:\n\n{self._markdown_code_block('connect [url]', 'bash')}"

    def format_schema_result(self, tool_name: str, schema: Dict[str, Any]) -> str:
        """
        Format a schema result in Markdown.

        Args:
            tool_name: The name of the tool
            schema: The schema to format

        Returns:
            Markdown-formatted message
        """
        if not schema:
            return f"# ❌ No Schema Available\n\n**Tool:** `{tool_name}`\n\nNo schema information found."
        
        if not isinstance(schema, dict):
            return f"# ❌ Invalid Schema\n\n**Tool:** `{tool_name}`\n\n**Error:** Invalid schema format ({type(schema).__name__})"

        result = f"# 📝 Schema for `{tool_name}`\n"
        if "title" in schema:
            result += f"\n**Title:** {schema['title']}\n"
        if "description" in schema:
            result += f"\n**Description:** {schema['description']}\n"

        properties = schema.get("properties", {})
        required = schema.get("required", [])
        req_count = sum(1 for p in properties if p in required)
        opt_count = len(properties) - req_count

        result += f"\n## 🧾 Parameters ({req_count} required, {opt_count} optional)\n"
        if not properties:
            result += "_No parameters defined._\n"
        else:
            for prop_name, prop_info in sorted(properties.items(), key=lambda x: (0 if x[0] in required else 1, x[0])):
                if not isinstance(prop_info, dict):
                    continue
                is_required = prop_name in required
                req_marker = " (required)" if is_required else " (optional)"
                prop_type = prop_info.get("type", "any")
                prop_desc = prop_info.get("description", "")
                result += f"- **`{prop_name}`**{req_marker}: `{prop_type}`\n"
                if prop_desc:
                    result += f"  {prop_desc}\n"

                constraints = []
                if "enum" in prop_info:
                    enum_values = prop_info["enum"]
                    constraints.append(f"Allowed values: {', '.join([f'`{v}`' for v in enum_values][:5]) + ('...' if len(enum_values) > 5 else '')}")
                if "default" in prop_info:
                    default = prop_info["default"]
                    constraints.append(f"Default: `{default if default is not None else 'null'}`")
                if prop_type in ["number", "integer"]:
                    if "minimum" in prop_info:
                        constraints.append(f"Minimum: `{prop_info['minimum']}`")
                    if "maximum" in prop_info:
                        constraints.append(f"Maximum: `{prop_info['maximum']}`")
                if prop_type == "string":
                    if "minLength" in prop_info:
                        constraints.append(f"Minimum length: `{prop_info['minLength']}`")
                    if "maxLength" in prop_info:
                        constraints.append(f"Maximum length: `{prop_info['maxLength']}`")
                    if "format" in prop_info:
                        constraints.append(f"Format: `{prop_info['format']}`")
                    if "pattern" in prop_info:
                        constraints.append(f"Pattern: `{prop_info['pattern']}`")
                if prop_type == "array":
                    if "minItems" in prop_info:
                        constraints.append(f"Minimum items: `{prop_info['minItems']}`")
                    if "maxItems" in prop_info:
                        constraints.append(f"Maximum items: `{prop_info['maxItems']}`")
                    if "uniqueItems" in prop_info and prop_info["uniqueItems"]:
                        constraints.append("Items must be unique")
                if constraints:
                    result += "  " + "\n  ".join(constraints) + "\n"
                result += "\n"

        example = {}
        for prop_name in required:
            if prop_name not in properties:
                continue
            prop_info = properties.get(prop_name, {})
            prop_type = prop_info.get("type", "any")
            example[prop_name] = {
                "string": "example_string" if not prop_info.get("format") else {
                    "date": "2023-01-01",
                    "date-time": "2023-01-01T12:00:00Z",
                    "email": "user@example.com",
                    "uri": "https://example.com"
                }.get(prop_info.get("format"), f"example_{prop_name}"),
                "number": 42.0,
                "integer": 42,
                "boolean": True,
                "array": [],
                "object": {}
            }.get(prop_type, None)

        optional_count = 0
        for prop_name, prop_info in properties.items():
            if prop_name not in required and optional_count < 3:
                if "default" in prop_info:
                    example[prop_name] = prop_info["default"]
                    optional_count += 1

        result += f"## 🧪 Example Usage\n\n"
        result += self._markdown_code_block(f"# Natural language\nschema {tool_name}\n\n# Structured\n!schema {tool_name}\n\n# Tool call\ncall {tool_name} {json.dumps(example, indent=2)}", "bash")

        result += f"\n## 📄 Raw Schema\n\n"
        try:
            schema_json = json.dumps(schema, indent=2)
            if len(schema_json) > 2000:
                schema_json = schema_json[:2000] + "\n... (truncated)"
            result += self._markdown_code_block(schema_json)
        except Exception as e:
            result += self._markdown_code_block(f"Error formatting schema: {e}")

        return result