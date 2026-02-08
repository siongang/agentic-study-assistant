"""ADK entrypoint: exposes root_agent for adk web/run/api_server."""
from app.agents.root_agent import root_agent

__all__ = ["root_agent"]
