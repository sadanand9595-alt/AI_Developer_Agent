from pathlib import Path

from agents.chat_agent import ChatAgent
from memory.agent_memory import AgentMemory


def test_chat_agent_persists_history(tmp_path: Path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    memory = AgentMemory(workspace / "memory.json")
    agent = ChatAgent(workspace, memory=memory)

    response = agent.respond("Summarize this workspace")

    assert response
    assert agent.get_history()[0]["prompt"] == "Summarize this workspace"

    agent.clear_history()
    assert agent.get_history() == []
