"""Giga-MCP: Unified local MCP server combining Microsoft Teams, APU Timetable, and APU Moodle.

Loads and mounts all tools from:
  - teams-mcp      (d:\\Ai project\\cool stuff\\teams-mcp\\windows\\server.py)
  - aptimetable-mcp (d:\\Ai project\\cool stuff\\aptimetable-mcp\\server.py)
  - Moodle-MCP     (d:\\Ai project\\Moodle-MCP\\moodle_mcp\\server.py)

Reuses each project's existing session/token/cache files without duplicating logic.

Usage:
    python server.py
"""

from __future__ import annotations

import importlib.util
import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from types import ModuleType

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass

try:
    from mcp.server.mcpserver import MCPServer as FastMCP
except ImportError:
    from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Paths (overridable via environment variables)
# ---------------------------------------------------------------------------
COOL_STUFF_DIR = Path(__file__).resolve().parent.parent
AI_PROJECT_DIR = COOL_STUFF_DIR.parent

TEAMS_SERVER_PATH = Path(
    os.environ.get(
        "GIGA_TEAMS_SERVER",
        str(COOL_STUFF_DIR / "teams-mcp" / "windows" / "server.py"),
    )
).resolve()

APTIMETABLE_SERVER_PATH = Path(
    os.environ.get(
        "GIGA_APTIMETABLE_SERVER",
        str(COOL_STUFF_DIR / "aptimetable-mcp" / "server.py"),
    )
).resolve()

MOODLE_ROOT_DIR = Path(
    os.environ.get(
        "GIGA_MOODLE_DIR",
        str(AI_PROJECT_DIR / "Moodle-MCP"),
    )
).resolve()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("giga-mcp")


def _load_module_from_path(module_name: str, file_path: Path) -> ModuleType:
    if not file_path.exists():
        raise FileNotFoundError(f"MCP module not found: {file_path}")
    spec = importlib.util.spec_from_file_location(module_name, str(file_path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load spec for {file_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _load_moodle_module(moodle_root: Path) -> ModuleType:
    if not moodle_root.exists():
        raise FileNotFoundError(f"Moodle-MCP directory not found: {moodle_root}")
    root_str = str(moodle_root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    import moodle_mcp.server as moodle_server  # type: ignore[import-not-found]
    return moodle_server


def _mount_tools(target: FastMCP, source: FastMCP, label: str) -> int:
    source_tools = getattr(getattr(source, "_tool_manager", None), "_tools", {})
    count = 0
    for tool in source_tools.values():
        target.add_tool(
            tool.fn,
            name=tool.name,
            title=getattr(tool, "title", None),
            description=tool.description,
            annotations=getattr(tool, "annotations", None),
        )
        count += 1
    log.info("Mounted %d tools from %s", count, label)
    return count


# ---------------------------------------------------------------------------
# Load sub-servers & build unified Giga-MCP instance
# ---------------------------------------------------------------------------
teams_mod = _load_module_from_path("giga_teams_server", TEAMS_SERVER_PATH)
timetable_mod = _load_module_from_path("giga_aptimetable_server", APTIMETABLE_SERVER_PATH)
moodle_mod = _load_moodle_module(MOODLE_ROOT_DIR)


@asynccontextmanager
async def giga_lifespan(server: FastMCP):
    teams_lifespan = getattr(teams_mod, "server_lifespan", None)
    if teams_lifespan is not None:
        async with teams_lifespan(server):
            yield
    else:
        yield


_student_ctx_parts = []
if os.environ.get("APU_STUDENT_NAME"):
    _student_ctx_parts.append(f"Student: {os.environ['APU_STUDENT_NAME']}")
if os.environ.get("APU_TP_NUMBER"):
    _student_ctx_parts.append(f"TP: {os.environ['APU_TP_NUMBER']}")
if os.environ.get("APU_INTAKE"):
    _student_ctx_parts.append(f"Intake: {os.environ['APU_INTAKE']}")
if os.environ.get("APU_GROUPING"):
    _student_ctx_parts.append(f"Group: {os.environ['APU_GROUPING']}")
_student_ctx = (" (" + ", ".join(_student_ctx_parts) + ")") if _student_ctx_parts else ""

mcp = FastMCP(
    "giga-mcp",
    instructions=(
        "Unified APU student assistant MCP combining Microsoft Teams, "
        "APU Timetable & Classroom Finder, and APU Moodle LMS."
        f"{_student_ctx} Call get_student_profile for configured student details."
    ),
    lifespan=giga_lifespan,
)

_mount_tools(mcp, teams_mod.mcp, "teams-mcp")
_mount_tools(mcp, timetable_mod.mcp, "aptimetable-mcp")
_mount_tools(mcp, moodle_mod.mcp, "moodle-mcp")


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
