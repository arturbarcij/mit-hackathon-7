"""Audit orchestrator for Jani.

Read-only. Seats run in dependency order, check the app, and write kb/agent-runs.
Builder seats report gaps. They do not edit owned product paths.
The runner never prints API keys.
"""

__version__ = "1.1.0"
