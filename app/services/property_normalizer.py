"""
Property normalizer for Notion API
Converts user-friendly property formats to Notion API format
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
import structlog

logger = structlog.get_logger()


class PropertyNormalizer:
    """
    Normalizes properties between user-friendly format and Notion API format
    """
    
    @staticmethod
    def normalize_property_value(prop_type: str, value: Any) -> Dict[str, Any]:
        """
        Convert simplified property value to Notion API format
        
        Args:
            prop_type: Property type (title, rich_text, number, select, etc.)
            value: Simplified value
        
        Returns:
            Notion API formatted property value
        """
        if value is None:
            return {}
        
        # Title
        if prop_type == "title":
            if isinstance(value, str):
                return {
                    "title": [{"type": "text", "text": {"content": value}}]
                }
            return {"title": value}
        
        # Rich text
        if prop_type == "rich_text":
            if isinstance(value, str):
                return {
                    "rich_text": [{"type": "text", "text": {"content": value}}]
                }
            return {"rich_text": value}
        
        # Number
        if prop_type == "number":
            return {"number": float(value) if value is not None else None}
        
        # Select
        if prop_type == "select":
            if isinstance(value, str):
                return {"select": {"name": value}}
            return {"select": value}
        
        # Multi-select
        if prop_type == "multi_select":
            if isinstance(value, list):
                return {
                    "multi_select": [
                        {"name": v} if isinstance(v, str) else v
                        for v in value
                    ]
                }
            return {"multi_select": value}
        
        # Status
        if prop_type == "status":
            if isinstance(value, str):
                return {"status": {"name": value}}
            return {"status": value}
        
        # Date
        if prop_type == "date":
            if isinstance(value, str):
                return {"date": {"start": value}}
            elif isinstance(value, datetime):
                return {"date": {"start": value.isoformat()}}
            return {"date": value}
        
        # Checkbox
        if prop_type == "checkbox":
            return {"checkbox": bool(value)}
        
        # URL
        if prop_type == "url":
            return {"url": str(value) if value else None}
        
        # Email
        if prop_type == "email":
            return {"email": str(value) if value else None}
        
        # Phone
        if prop_type == "phone_number":
            return {"phone_number": str(value) if value else None}
        
        # People
        if prop_type == "people":
            if isinstance(value, list):
                return {
                    "people": [
                        {"id": v} if isinstance(v, str) else v
                        for v in value
                    ]
                }
            return {"people": value}
        
        # Files
        if prop_type == "files":
            if isinstance(value, list):
                return {"files": value}
            return {"files": [value]}
        
        # Relation
        if prop_type == "relation":
            if isinstance(value, list):
                return {
                    "relation": [
                        {"id": v} if isinstance(v, str) else v
                        for v in value
                    ]
                }
            elif isinstance(value, str):
                return {"relation": [{"id": value}]}
            return {"relation": value}
        
        # Default: return as-is
        return {prop_type: value}
    
    @staticmethod
    def normalize_properties(properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize a full properties object
        
        Accepts format:
        {
            "Name": {"type": "title", "value": "My Page"},
            "Status": {"type": "select", "value": "In Progress"},
            "Due": {"type": "date", "value": "2026-01-10"}
        }
        
        Or direct Notion API format
        """
        normalized = {}
        
        for key, value in properties.items():
            if isinstance(value, dict) and "type" in value and "value" in value:
                # User-friendly format
                prop_type = value["type"]
                prop_value = value["value"]
                normalized[key] = PropertyNormalizer.normalize_property_value(
                    prop_type, prop_value
                )
            else:
                # Already in Notion format or needs no conversion
                normalized[key] = value
        
        return normalized
    
    @staticmethod
    def create_property_schema(prop_type: str, **options) -> Dict[str, Any]:
        """
        Create property schema for database creation/update
        
        Args:
            prop_type: Property type
            **options: Type-specific options
        
        Returns:
            Property schema for Notion API
        """
        schema = {prop_type: {}}
        
        # Select/Multi-select options
        if prop_type in ("select", "multi_select") and "options" in options:
            schema[prop_type]["options"] = [
                {"name": opt} if isinstance(opt, str) else opt
                for opt in options["options"]
            ]
        
        # Status options
        if prop_type == "status" and "options" in options:
            schema[prop_type]["options"] = [
                {"name": opt, "color": "default"} if isinstance(opt, str) else opt
                for opt in options["options"]
            ]
        
        # Number format
        if prop_type == "number" and "format" in options:
            schema[prop_type]["format"] = options["format"]
        
        # Relation configuration
        if prop_type == "relation":
            if "database_id" in options:
                schema[prop_type]["database_id"] = options["database_id"]
            if "type" in options:
                schema[prop_type]["type"] = options["type"]  # single_property or dual_property
            if "synced_property_name" in options:
                schema[prop_type]["synced_property_name"] = options["synced_property_name"]
        
        # Rollup configuration
        if prop_type == "rollup":
            if "relation_property_name" in options:
                schema[prop_type]["relation_property_name"] = options["relation_property_name"]
            if "rollup_property_name" in options:
                schema[prop_type]["rollup_property_name"] = options["rollup_property_name"]
            if "function" in options:
                schema[prop_type]["function"] = options["function"]
        
        # Formula
        if prop_type == "formula" and "expression" in options:
            schema[prop_type]["expression"] = options["expression"]
        
        return schema
    
    @staticmethod
    def extract_plain_text(rich_text_array: List[Dict]) -> str:
        """
        Extract plain text from Notion rich text array
        """
        if not rich_text_array:
            return ""
        return "".join(item.get("plain_text", "") for item in rich_text_array)
    
    @staticmethod
    def simplify_property_value(notion_property: Dict[str, Any]) -> Any:
        """
        Convert Notion API property value to simple format
        """
        prop_type = notion_property.get("type")
        
        if prop_type == "title" and "title" in notion_property:
            return PropertyNormalizer.extract_plain_text(notion_property["title"])
        
        if prop_type == "rich_text" and "rich_text" in notion_property:
            return PropertyNormalizer.extract_plain_text(notion_property["rich_text"])
        
        if prop_type == "number":
            return notion_property.get("number")
        
        if prop_type == "select":
            select_val = notion_property.get("select")
            return select_val.get("name") if select_val else None
        
        if prop_type == "multi_select":
            return [item["name"] for item in notion_property.get("multi_select", [])]
        
        if prop_type == "status":
            status_val = notion_property.get("status")
            return status_val.get("name") if status_val else None
        
        if prop_type == "date":
            date_val = notion_property.get("date")
            return date_val.get("start") if date_val else None
        
        if prop_type == "checkbox":
            return notion_property.get("checkbox", False)
        
        if prop_type == "url":
            return notion_property.get("url")
        
        if prop_type == "email":
            return notion_property.get("email")
        
        if prop_type == "phone_number":
            return notion_property.get("phone_number")
        
        if prop_type == "relation":
            return [item["id"] for item in notion_property.get("relation", [])]
        
        # Default: return the property as-is
        return notion_property


# Global instance
property_normalizer = PropertyNormalizer()

