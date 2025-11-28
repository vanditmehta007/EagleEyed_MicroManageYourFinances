
from typing import Dict, Any, Callable, List
import inspect

from backend.services.agent_engine.tools.transaction_tools import TRANSACTION_TOOLS
from backend.services.agent_engine.tools.compliance_tools import COMPLIANCE_TOOLS
from backend.services.agent_engine.tools.report_tools import REPORT_TOOLS
from backend.services.agent_engine.tools.document_tools import DOCUMENT_TOOLS
from backend.services.agent_engine.tools.query_tools import QUERY_TOOLS

# Merge all tools into a single registry
TOOL_REGISTRY: Dict[str, Callable] = {}
TOOL_REGISTRY.update(TRANSACTION_TOOLS)
TOOL_REGISTRY.update(COMPLIANCE_TOOLS)
TOOL_REGISTRY.update(REPORT_TOOLS)
TOOL_REGISTRY.update(DOCUMENT_TOOLS)
TOOL_REGISTRY.update(QUERY_TOOLS)

class ToolRegistry:
    """
    Registry for all tools available to the agent.
    Wraps the TOOL_REGISTRY dictionary and provides methods for tool management.
    """
    def __init__(self):
        self.tools = TOOL_REGISTRY

    def get_tool(self, name: str) -> Callable:
        """
        Get a tool by name.
        """
        return self.tools.get(name)

    def list_tools(self) -> Dict[str, str]:
        """
        List all available tools and their docstrings.
        This format is useful for simple prompt engineering.
        """
        return {name: func.__doc__.strip() if func.__doc__ else "No description" for name, func in self.tools.items()}

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """
        Generate JSON schemas for all tools, compatible with Gemini function calling.
        This uses introspection to build the schema from type hints and docstrings.
        """
        schemas = []
        for name, func in self.tools.items():
            schema = self._generate_function_schema(name, func)
            schemas.append(schema)
        return schemas

    def get_tools_list(self) -> List[Callable]:
        """
        Get a list of all tool functions.
        Useful for SDKs that accept callable objects directly (like google-genai).
        """
        return list(self.tools.values())

    def execute_tool(self, name: str, **kwargs) -> Any:
        """
        Execute a tool by name with provided arguments.
        """
        tool = self.get_tool(name)
        if not tool:
            raise ValueError(f"Tool '{name}' not found.")
        
        # In a real async app, we might need to handle async tools here.
        # For now, we assume the controller handles await if needed, 
        # or we inspect and await if it's a coroutine.
        if inspect.iscoroutinefunction(tool):
            # This method itself isn't async, so we can't await here without changing the signature.
            # The caller (agent_controller) should handle this or this method should be async.
            # For this skeleton, we'll return the coroutine object to be awaited.
            return tool(**kwargs)
        
        return tool(**kwargs)

    def _generate_function_schema(self, name: str, func: Callable) -> Dict[str, Any]:
        """
        Helper to generate a JSON schema for a function.
        """
        sig = inspect.signature(func)
        doc = func.__doc__.strip() if func.__doc__ else ""
        
        parameters = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        for param_name, param in sig.parameters.items():
            param_type = "string" # Default
            if param.annotation == int:
                param_type = "integer"
            elif param.annotation == float:
                param_type = "number"
            elif param.annotation == bool:
                param_type = "boolean"
            elif param.annotation == list or getattr(param.annotation, "__origin__", None) == list:
                param_type = "array"
            elif param.annotation == dict or getattr(param.annotation, "__origin__", None) == dict:
                param_type = "object"
            
            parameters["properties"][param_name] = {
                "type": param_type,
                "description": f"Parameter {param_name}" # Could parse docstring for better desc
            }
            
            if param.default == inspect.Parameter.empty:
                parameters["required"].append(param_name)
                
        return {
            "name": name,
            "description": doc,
            "parameters": parameters
        }
