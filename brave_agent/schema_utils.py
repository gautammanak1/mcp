import logging
from typing import Dict, Any, Optional, Union, Callable

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_schema_from_tool(tool: Any, tool_name: str) -> Dict[str, Any]:
    schema = tool.get("schema", {})
    if not schema:
        logger.warning(f"Tool '{tool_name}' has no schema information")
    return _clean_schema(schema)

def _clean_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(schema, dict):
        logger.warning(f"Schema is not a dictionary: {type(schema).__name__}")
        return {}
    cleaned_schema = schema.copy()
    if 'required' in cleaned_schema and not isinstance(cleaned_schema['required'], list):
        cleaned_schema['required'] = []
    if 'properties' not in cleaned_schema:
        cleaned_schema['properties'] = {}
    elif not isinstance(cleaned_schema['properties'], dict):
        cleaned_schema['properties'] = {}
    return cleaned_schema

def validate_schema_structure(schema: Dict[str, Any]) -> bool:
    if not isinstance(schema, dict):
        return False
    if 'properties' not in schema:
        return False
    if not isinstance(schema['properties'], dict):
        return False
    if 'required' in schema and not isinstance(schema['required'], list):
        return False
    return True

def extract_required_params(schema: Dict[str, Any]) -> list:
    if not validate_schema_structure(schema):
        return []
    return schema.get('required', [])

def extract_optional_params_with_defaults(schema: Dict[str, Any]) -> Dict[str, Any]:
    if not validate_schema_structure(schema):
        return {}
    result = {}
    properties = schema.get('properties', {})
    required = schema.get('required', [])
    for param_name, param_info in properties.items():
        if param_name not in required and isinstance(param_info, dict) and 'default' in param_info:
            result[param_name] = param_info['default']
    return result