"""Test that MCP tool schemas are valid and consistent."""
import json
import subprocess
import os
from pathlib import Path


MCP_DIR = Path(__file__).parent.parent.parent / "home-assistant-mcp"


def get_tool_names_from_ts():
    """Extract tool names from tools.ts by parsing name fields."""
    tools_file = MCP_DIR / "src" / "tools.ts"
    if not tools_file.exists():
        return []
    
    names = []
    content = tools_file.read_text()
    for line in content.split("\n"):
        if "name: 'ha_" in line:
            name = line.split("'")[1]
            names.append(name)
    return names


def get_handler_names_from_ts():
    """Extract handler names from handlers.ts."""
    handlers_file = MCP_DIR / "src" / "handlers.ts"
    if not handlers_file.exists():
        return []
    
    names = []
    content = handlers_file.read_text()
    for line in content.split("\n"):
        if "'ha_" in line and "async" in line:
            parts = line.split("'")
            for i, part in enumerate(parts):
                if part.startswith("ha_"):
                    names.append(part)
                    break
    return names


class TestToolSchemaConsistency:
    """Test that tool definitions and handlers are in sync."""

    def test_tools_file_exists(self):
        assert (MCP_DIR / "src" / "tools.ts").exists()

    def test_handlers_file_exists(self):
        assert (MCP_DIR / "src" / "handlers.ts").exists()

    def test_all_tools_have_handlers(self):
        """Every tool defined in tools.ts should have a handler in handlers.ts."""
        tool_names = set(get_tool_names_from_ts())
        handler_names = set(get_handler_names_from_ts())
        
        missing_handlers = tool_names - handler_names
        assert len(missing_handlers) == 0, (
            f"Tools without handlers: {missing_handlers}"
        )

    def test_no_orphan_handlers(self):
        """Every handler should correspond to a tool definition."""
        tool_names = set(get_tool_names_from_ts())
        handler_names = set(get_handler_names_from_ts())
        
        orphan_handlers = handler_names - tool_names
        assert len(orphan_handlers) == 0, (
            f"Handlers without tool definitions: {orphan_handlers}"
        )

    def test_tool_names_follow_convention(self):
        """All tool names should start with 'ha_'."""
        tool_names = get_tool_names_from_ts()
        for name in tool_names:
            assert name.startswith("ha_"), f"Tool {name} doesn't follow ha_ convention"

    def test_minimum_tool_count(self):
        """We should have at least 78 tools."""
        tool_names = get_tool_names_from_ts()
        assert len(tool_names) >= 78, f"Only {len(tool_names)} tools found, expected 78+"
