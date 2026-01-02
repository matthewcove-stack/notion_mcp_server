"""
Property normalizer - converts assistant-friendly property format to Notion API format
"""
from typing import Dict, Any, Optional
import structlog

logger = structlog.get_logger()


def normalize_property(prop_type: str, value: Any) -> Dict[str, Any]:
    """
    Normalize a single property value to Notion API format
    
    Args:
        prop_type: Property type (date, number, checkbox, select, etc.)
        value: Property value (can be string, number, bool, dict, etc.)
    
    Returns:
        Normalized property value dict for Notion API
    """
    if prop_type == "date":
        if isinstance(value, str):
            return {"start": value}
        elif isinstance(value, dict):
            return value  # Already in Notion format
        else:
            raise ValueError(f"Invalid date value: {value}")
    
    elif prop_type == "number":
        return {"number": float(value) if value is not None else None}
    
    elif prop_type == "checkbox":
        return {"checkbox": bool(value)}
    
    elif prop_type == "select":
        if isinstance(value, str):
            return {"name": value}
        elif isinstance(value, dict):
            return value  # Already in Notion format
        else:
            raise ValueError(f"Invalid select value: {value}")
    
    elif prop_type == "multi_select":
        if isinstance(value, list):
            return [{"name": v} if isinstance(v, str) else v for v in value]
        elif isinstance(value, str):
            return [{"name": value}]
        else:
            raise ValueError(f"Invalid multi_select value: {value}")
    
    elif prop_type == "status":
        if isinstance(value, str):
            return {"name": value}
        elif isinstance(value, dict):
            return value
        else:
            raise ValueError(f"Invalid status value: {value}")
    
    elif prop_type == "title":
        if isinstance(value, str):
            return [{"type": "text", "text": {"content": value}}]
        elif isinstance(value, list):
            return value  # Already in Notion format
        else:
            raise ValueError(f"Invalid title value: {value}")
    
    elif prop_type == "rich_text":
        if isinstance(value, str):
            return [{"type": "text", "text": {"content": value}}]
        elif isinstance(value, list):
            return value  # Already in Notion format
        else:
            raise ValueError(f"Invalid rich_text value: {value}")
    
    elif prop_type == "url":
        return {"url": str(value) if value else None}
    
    elif prop_type == "email":
        return {"email": str(value) if value else None}
    
    elif prop_type == "phone_number":
        return {"phone_number": str(value) if value else None}
    
    elif prop_type == "relation":
        if isinstance(value, list):
            # List of page IDs
            return [{"id": v} if isinstance(v, str) else v for v in value]
        elif isinstance(value, str):
            return [{"id": value}]
        else:
            raise ValueError(f"Invalid relation value: {value}")
    
    elif prop_type == "people":
        if isinstance(value, list):
            # List of user IDs
            return [{"id": v} if isinstance(v, str) else v for v in value]
        elif isinstance(value, str):
            return [{"id": value}]
        else:
            raise ValueError(f"Invalid people value: {value}")
    
    else:
        # For unknown types, return as-is (might be rollup, formula, etc.)
        logger.warning("unknown_property_type", prop_type=prop_type)
        return value if isinstance(value, dict) else {"content": value}


def normalize_properties(properties: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Normalize a properties dict from assistant-friendly format to Notion API format
    
    Input format:
    {
        "Due": {"type": "date", "value": "2026-01-10"},
        "Status": {"type": "select", "value": "In Progress"},
        "Done": {"type": "checkbox", "value": true}
    }
    
    Output format (Notion API):
    {
        "Due": {"date": {"start": "2026-01-10"}},
        "Status": {"select": {"name": "In Progress"}},
        "Done": {"checkbox": true}
    }
    """
    normalized = {}
    
    for prop_name, prop_data in properties.items():
        if not isinstance(prop_data, dict):
            # Already in Notion format, use as-is
            normalized[prop_name] = prop_data
            continue
        
        prop_type = prop_data.get("type")
        prop_value = prop_data.get("value")
        
        if prop_type and prop_value is not None:
            # Normalize the value
            normalized_value = normalize_property(prop_type, prop_value)
            normalized[prop_name] = {prop_type: normalized_value}
        else:
            # Already in Notion format
            normalized[prop_name] = prop_data
    
    return normalized

