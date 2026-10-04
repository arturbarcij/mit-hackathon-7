"""Jani orchestrator: runs the agent lanes described in kb/ (briefs, STATUS board, OWNERSHIP table).

The files in kb/ stay the source of truth. This package reads them, decides which tasks are ready,
runs one agent per task with a tool sandbox that enforces path ownership, gates every change on the
lane's tests, and writes the outcome back to the agent's own STATUS row. Humans stay in charge:
tasks owned by Arthur are never dispatched, and nothing is committed or pushed.
"""
__version__ = "0.1.0"
