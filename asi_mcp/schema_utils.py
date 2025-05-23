"""
Schema Utilities - Helper functions for handling MCP tool schemas

This module contains utility functions for handling MCP tool schemas,
including extracting schema information from tool objects and validating
schema structures.
"""

import logging
from typing import Dict, Any, Optional, Union, Callable

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_schema_from_tool(tool: Any, tool_name: str) -> Dict[str, Any]:
    """
    Extract schema information from a tool object.
    
    This function handles various schema attribute names and formats,
    including cases where the schema is a method rather than a dictionary.
    
    Args:
        tool: The tool object
        tool_name: The name of the tool (for logging)
        
    Returns:
        A dictionary containing the schema information, or an empty dict if not found
    """
    # Try different attribute names for schema
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
    else:
        logger.warning(f"Tool '{tool_name}' has no schema information")
        return {}

def _clean_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean a schema by removing internal attributes that shouldn't be exposed as parameters.
    
    Args:
        schema: The schema to clean
        
    Returns:
        A cleaned schema
    """
    # Handle None or empty schema
    if schema is None:
        logger.warning("Received None schema")
        return {}
    
    # Handle non-dict schema
    if not isinstance(schema, dict):
        logger.warning(f"Schema is not a dictionary: {type(schema).__name__}")
        return {}
    
    # Create a copy to avoid modifying the original
    try:
        cleaned_schema = schema.copy()
    except Exception as e:
        logger.error(f"Error copying schema: {e}")
        return {}
    
    # Remove internal attributes from required list
    if 'required' in cleaned_schema:
        if isinstance(cleaned_schema['required'], list):
            # List of internal attributes that shouldn't be treated as required parameters
            internal_attrs = ['name', 'inputSchema', 'description', 'schema', 'annotations']
            cleaned_schema['required'] = [param for param in cleaned_schema['required']
                                         if param not in internal_attrs]
        else:
            logger.warning(f"'required' field is not a list: {type(cleaned_schema['required']).__name__}")
            cleaned_schema['required'] = []
    
    # Ensure properties exists
    if 'properties' not in cleaned_schema:
        logger.warning("Schema missing 'properties' field")
        cleaned_schema['properties'] = {}
    elif not isinstance(cleaned_schema['properties'], dict):
        logger.warning(f"'properties' field is not a dictionary: {type(cleaned_schema['properties']).__name__}")
        cleaned_schema['properties'] = {}
    
    return cleaned_schema

def _extract_schema_value(schema_value: Union[Dict[str, Any], Callable],
                         tool_name: str,
                         attr_name: str) -> Dict[str, Any]:
    """
    Extract the actual schema value, handling the case where it's a callable.
    
    Args:
        schema_value: The schema value (might be a dict or a callable)
        tool_name: The name of the tool (for logging)
        attr_name: The name of the attribute being accessed
        
    Returns:
        A dictionary containing the schema information
    """
    # Handle None value
    if schema_value is None:
        logger.warning(f"{attr_name.capitalize()} for tool '{tool_name}' is None")
        return {}
    
    # Check if schema is a method/callable and call it if so
    if callable(schema_value):
        logger.info(f"{attr_name.capitalize()} for tool '{tool_name}' is callable, invoking it")
        try:
            # Call the method with a timeout to prevent hanging
            result = schema_value()
            
            # Handle None result
            if result is None:
                logger.warning(f"Callable {attr_name} for tool '{tool_name}' returned None")
                return {}
                
            # Handle non-dict result
            if not isinstance(result, dict):
                logger.warning(f"Callable {attr_name} for tool '{tool_name}' returned non-dict type: {type(result).__name__}")
                # Try to convert to dict if possible
                try:
                    if hasattr(result, '__dict__'):
                        logger.info(f"Converting {type(result).__name__} to dict using __dict__")
                        return result.__dict__
                    elif hasattr(result, 'to_dict'):
                        logger.info(f"Converting {type(result).__name__} to dict using to_dict()")
                        return result.to_dict()
                    else:
                        return {}
                except Exception as e:
                    logger.error(f"Error converting {type(result).__name__} to dict: {e}")
                    return {}
            
            return result
        except Exception as e:
            logger.error(f"Error calling {attr_name} method for tool {tool_name}: {e}")
            if hasattr(e, '__dict__'):
                logger.error(f"Error details: {e.__dict__}")
            return {}
    
    # If it's not callable, ensure it's a dictionary
    if not isinstance(schema_value, dict):
        logger.warning(f"{attr_name.capitalize()} for tool '{tool_name}' is not a dictionary: {type(schema_value).__name__}")
        # Try to convert to dict if possible
        try:
            if hasattr(schema_value, '__dict__'):
                logger.info(f"Converting {type(schema_value).__name__} to dict using __dict__")
                return schema_value.__dict__
            elif hasattr(schema_value, 'to_dict'):
                logger.info(f"Converting {type(schema_value).__name__} to dict using to_dict()")
                return schema_value.to_dict()
            else:
                return {}
        except Exception as e:
            logger.error(f"Error converting {type(schema_value).__name__} to dict: {e}")
            return {}
    
    return schema_value

def validate_schema_structure(schema: Dict[str, Any]) -> bool:
    """
    Validate that a schema has the expected structure.
    
    Args:
        schema: The schema to validate
        
    Returns:
        True if the schema has a valid structure, False otherwise
    """
    if not isinstance(schema, dict):
        return False
    
    # Check for properties field (required for JSON Schema)
    if 'properties' not in schema:
        return False
    
    # Ensure properties is a dictionary
    if not isinstance(schema['properties'], dict):
        return False
    
    # If required field exists, ensure it's a list
    if 'required' in schema and not isinstance(schema['required'], list):
        return False
    
    return True

def extract_required_params(schema: Dict[str, Any]) -> list:
    """
    Extract required parameters from a schema.
    
    Args:
        schema: The schema to extract from
        
    Returns:
        A list of required parameter names
    """
    if not validate_schema_structure(schema):
        return []
    
    return schema.get('required', [])

def extract_optional_params_with_defaults(schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract optional parameters with their default values from a schema.
    
    Args:
        schema: The schema to extract from
        
    Returns:
        A dictionary mapping parameter names to their default values
    """
    if not validate_schema_structure(schema):
        return {}
    
    result = {}
    properties = schema.get('properties', {})
    required = schema.get('required', [])
    
    for param_name, param_info in properties.items():
        if param_name not in required and isinstance(param_info, dict) and 'default' in param_info:
            result[param_name] = param_info['default']
    
    return result