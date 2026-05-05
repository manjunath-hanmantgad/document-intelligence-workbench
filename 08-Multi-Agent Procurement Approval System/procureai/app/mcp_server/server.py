from typing import Dict, Any

from app.mcp_server.tools import TOOL_REGISTRY, execute_tool
from app.mcp_server.resources import list_resources
from app.mcp_server.prompts import list_prompts, get_prompt


class MCPServer:

    def __init__(self):
        self.name = "ProcureAI MCP Server"
        self.description = "Exposes procurement capabilities through MCP-compatible interface"

    def list_tools(self) -> list:
        return [
            {
                "name": v["name"],
                "description": v["description"],
                "inputSchema": v["input_schema"],
            }
            for v in TOOL_REGISTRY.values()
        ]

    def call_tool(self, name: str, arguments: dict) -> Any:
        return execute_tool(name, arguments)

    def list_resources(self) -> dict:
        return list_resources()

    def list_prompts(self) -> dict:
        return list_prompts()

    def get_prompt(self, name: str) -> dict:
        return get_prompt(name)
