import json
import logging
from typing import Dict, List, Any, Optional, Union

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BraveSearchResultFormatter:
    def __init__(self, max_json_depth: int = 3, indent_size: int = 2):
        self.max_json_depth = max_json_depth
        self.indent_size = indent_size
    
    def format_connect_result(self, result: Dict[str, Any]) -> str:
        if result.get("success", False):
            message = f"✅ {result.get('message', 'Connected to Brave Search MCP server successfully')}"
            if "tool_count" in result:
                message += f"\n\nFound {result['tool_count']} available tools. Use `list` to see them."
            return message
        else:
            return f"❌ {result.get('message', 'Connection to Brave Search MCP server failed')}"
    
    def format_disconnect_result(self, result: Dict[str, Any]) -> str:
        if result.get("success", False):
            return f"✅ {result.get('message', 'Disconnected from Brave Search MCP server successfully')}"
        else:
            return f"❌ {result.get('message', 'Disconnection from Brave Search MCP server failed')}"
    
    def format_tool_list(self, tools: List[Any]) -> str:
        if not tools:
            return "No tools available. Make sure you're connected to the Brave Search MCP server."
        result = f"📋 Available Brave Search Tools ({len(tools)}):\n\n"
        for tool in tools:
            name = tool.name if hasattr(tool, 'name') else (tool.get("name", "Unknown") if isinstance(tool, dict) else "Unknown")
            description = tool.description if hasattr(tool, 'description') else (tool.get("description", "No description available") if isinstance(tool, dict) else "No description available")
            result += f"**{name}**\n{description}\n\n"
            schema = None
            for attr in ['schema', 'parameters', 'parameter_schema', 'inputSchema']:
                if hasattr(tool, attr):
                    schema = getattr(tool, attr)
                    break
                elif isinstance(tool, dict) and attr in tool:
                    schema = tool[attr]
                    break
            if schema and hasattr(schema, 'get'):
                properties = schema.get("properties", {})
                required = schema.get("required", [])
                if properties:
                    result += "Arguments:\n"
                    for prop_name, prop_info in properties.items():
                        prop_type = prop_info.get("type", "any") if isinstance(prop_info, dict) else "any"
                        prop_desc = prop_info.get("description", "") if isinstance(prop_info, dict) else ""
                        is_required = prop_name in required
                        req_marker = "*" if is_required else ""
                        result += f"- `{prop_name}`{req_marker}: {prop_type}"
                        if prop_desc:
                            result += f" - {prop_desc}"
                        result += "\n"
                    result += "\n"
        result += "Use `call [tool_name] {\"arg\": \"value\"}` to call a tool.\n"
        result += "Or use the shorthand syntax: `shorthand [tool_name] arg=\"value\"`"
        return result
    
    def format_tool_call_result(self, result: Dict[str, Any]) -> str:
        if not result.get("success", False):
            return f"❌ {result.get('message', 'Brave Search tool call failed')}"
        tool_result = result.get("result")
        if isinstance(tool_result, dict) or isinstance(tool_result, list):
            formatted_result = self.format_json(tool_result)
        elif tool_result is None:
            formatted_result = "No result returned"
        else:
            formatted_result = str(tool_result)
        return f"✅ Brave Search tool call successful:\n\n```\n{formatted_result}\n```"
    
    def format_status(self, status: Dict[str, Any]) -> str:
        if not status.get("connected", False):
            return f"📡 Status: {status.get('message', 'Not connected to Brave Search MCP server')}"
        message = f"📡 Status: Connected to Brave Search MCP server"
        if "tool_count" in status:
            message += f"\nAvailable tools: {status['tool_count']}"
        if status.get("has_token", False):
            message += "\nAuthentication: Using token"
        else:
            message += "\nAuthentication: None"
        return message
    
    def format_error(self, message: str) -> str:
        return f"❌ Error: {message}"
    
    def format_parameter_validation_error(self, tool_name: str, message: str, schema: Optional[Dict[str, Any]] = None) -> str:
        result = f"❌ Parameter validation error for Brave Search tool '{tool_name}':\n{message}\n\n"
        if schema and isinstance(schema, dict):
            properties = schema.get("properties", {})
            required = schema.get("required", [])
            if properties:
                result += "Required parameters:\n"
                for prop_name in required:
                    prop_info = properties.get(prop_name, {})
                    prop_type = prop_info.get("type", "any")
                    prop_desc = prop_info.get("description", "")
                    result += f"- `{prop_name}`: {prop_type}"
                    if prop_desc:
                        result += f" - {prop_desc}"
                    result += "\n"
                result += "\nExample usage:\n"
                example = {}
                for prop_name in required:
                    prop_info = properties.get(prop_name, {})
                    prop_type = prop_info.get("type", "any")
                    if prop_type == "string":
                        example[prop_name] = "example_string"
                    elif prop_type == "number" or prop_type == "integer":
                        example[prop_name] = 42
                    elif prop_type == "boolean":
                        example[prop_name] = True
                    elif prop_type == "array":
                        example[prop_name] = []
                    elif prop_type == "object":
                        example[prop_name] = {}
                    else:
                        example[prop_name] = "value"
                result += f"```\ncall {tool_name} {json.dumps(example, indent=2)}\n```"
        return result
    
    def format_json(self, data: Union[Dict, List, Any], depth: int = 0) -> str:
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
            parts = []
            for key, value in data.items():
                formatted_value = self.format_json(value, depth + 1)
                parts.append(f"{next_indent}\"{key}\": {formatted_value}")
            return "{\n" + ",\n".join(parts) + f"\n{indent}}}"
        elif isinstance(data, list):
            if not data:
                return "[]"
            indent = " " * self.indent_size * depth
            next_indent = " " * self.indent_size * (depth + 1)
            parts = []
            for item in data:
                formatted_item = self.format_json(item, depth + 1)
                parts.append(f"{next_indent}{formatted_item}")
            return "[\n" + ",\n".join(parts) + f"\n{indent}]"
        elif isinstance(data, str):
            return f"\"{data}\""
        elif data is None:
            return "null"
        else:
            return str(data)
    
    def format_unknown_command(self, command: str) -> str:
        return (
            f"❓ Unknown command: `{command}`\n\n"
            "Use `help` to see available commands."
        )
    
    def format_not_connected_error(self) -> str:
        return (
            "❌ Not connected to the Brave Search MCP server.\n\n"
            "Use `connect <URL>` to connect to the Brave Search MCP server."
        )
    
    def format_schema_result(self, tool_name: str, schema: Dict[str, Any]) -> str:
        result = f"📝 Schema for Brave Search tool '{tool_name}':\n\n"
        if not schema:
            return f"❌ No schema available for Brave Search tool '{tool_name}'"
        if not isinstance(schema, dict):
            return f"❌ Invalid schema format for Brave Search tool '{tool_name}': {type(schema).__name__}"
        if "title" in schema:
            result += f"**Title**: {schema['title']}\n\n"
        if "description" in schema:
            result += f"**Description**: {schema['description']}\n\n"
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        if not properties:
            result += "**No parameters defined in schema**\n\n"
        else:
            req_count = sum(1 for p in properties if p in required)
            opt_count = len(properties) - req_count
            result += f"**Parameters** ({req_count} required, {opt_count} optional):\n\n"
            sorted_props = sorted(properties.items(), key=lambda x: (0 if x[0] in required else 1, x[0]))
            for prop_name, prop_info in sorted_props:
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
                    if len(enum_values) <= 5:
                        constraints.append(f"Allowed values: {', '.join([f'`{v}`' for v in enum_values])}")
                    else:
                        constraints.append(f"Allowed values: {len(enum_values)} options")
                if "default" in prop_info:
                    default_value = prop_info["default"]
                    if default_value is None:
                        constraints.append("Default: `null`")
                    elif isinstance(default_value, str):
                        constraints.append(f"Default: `\"{default_value}\"`")
                    else:
                        constraints.append(f"Default: `{default_value}`")
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
                if prop_type == "string" and "pattern" in prop_info:
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
        result += "**Example Usage**:\n\n"
        example = {}
        for prop_name in required:
            if prop_name not in properties:
                continue
            prop_info = properties.get(prop_name, {})
            prop_type = prop_info.get("type", "any")
            if "example" in prop_info:
                example[prop_name] = prop_info["example"]
            elif "default" in prop_info:
                example[prop_name] = prop_info["default"]
            elif "enum" in prop_info and prop_info["enum"]:
                example[prop_name] = prop_info["enum"][0]
            elif prop_type == "string":
                if "format" in prop_info:
                    if prop_info["format"] == "date":
                        example[prop_name] = "2023-01-01"
                    elif prop_info["format"] == "date-time":
                        example[prop_name] = "2023-01-01T12:00:00Z"
                    elif prop_info["format"] == "email":
                        example[prop_name] = "user@example.com"
                    elif prop_info["format"] == "uri":
                        example[prop_name] = "https://example.com"
                    else:
                        example[prop_name] = f"example_{prop_info['format']}"
                else:
                    example[prop_name] = f"example_{prop_name}"
            elif prop_type == "number":
                example[prop_name] = 42.0
            elif prop_type == "integer":
                example[prop_name] = 42
            elif prop_type == "boolean":
                example[prop_name] = True
            elif prop_type == "array":
                if "items" in prop_info and "type" in prop_info["items"]:
                    items_type = prop_info["items"]["type"]
                    if items_type == "string":
                        example[prop_name] = ["example"]
                    elif items_type == "number":
                        example[prop_name] = [42.0]
                    elif items_type == "integer":
                        example[prop_name] = [42]
                    elif items_type == "boolean":
                        example[prop_name] = [True]
                    else:
                        example[prop_name] = []
                else:
                    example[prop_name] = []
            elif prop_type == "object":
                example[prop_name] = {}
            else:
                example[prop_name] = None
        optional_count = 0
        for prop_name, prop_info in properties.items():
            if prop_name not in required and optional_count < 3:
                if "default" in prop_info:
                    example[prop_name] = prop_info["default"]
                    optional_count += 1
        try:
            example_json = json.dumps(example, indent=2)
        except Exception:
            example_json = "{}"
        result += f"```\n# Natural language command:\nschema {tool_name}\n\n"
        result += f"# Structured command:\n!schema {tool_name}\n\n"
        result += f"# Tool call example:\ncall {tool_name} {example_json}\n```\n\n"
        result += "**Raw Schema**:\n\n"
        try:
            schema_json = json.dumps(schema, indent=2)
            if len(schema_json) > 2000:
                schema_json = schema_json[:2000] + "\n... (truncated)"
            result += f"```json\n{schema_json}\n```"
        except Exception as e:
            result += f"```\nError formatting schema: {e}\n```"
        return result