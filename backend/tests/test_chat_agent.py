import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from agent_service import ChatAgent, StreamEvent

@pytest.fixture
def agent():
    # Patch the LLM and perform_translation for all tests
    with patch("agent_service.ChatOpenAI") as mock_llm, \
         patch("agent_service.perform_translation") as mock_translation:
        # Mock LLM agent's astream_events to yield a sequence of events
        mock_agent = MagicMock()
        # Simulate a tool start, tool end, and chat model stream event
        async def fake_astream_events(*args, **kwargs):
            yield {"event": "on_tool_start", "name": "resolve_solidity_imports"}
            yield {"event": "on_tool_end", "name": "resolve_solidity_imports", "data": {"output": "✓ Imports resolved"}}
            yield {"event": "on_tool_start", "name": "translate_evm_to_ralph"}
            yield {"event": "on_tool_end", "name": "translate_evm_to_ralph", "data": {"output": "Translated Ralph code: ..."}}
            yield {"event": "on_chat_model_stream", "data": {"chunk": MagicMock(content="Some chat content.")}}
            yield {"event": "on_chain_end", "data": {"output": "Final output."}}
        mock_agent.astream_events = fake_astream_events
        # Patch ChatOpenAI to return a dummy llm
        mock_llm.return_value = MagicMock()
        # Patch create_agent to return our mock agent
        with patch("agent_service.create_agent", return_value=mock_agent):
            # Patch perform_translation to be an async generator
            async def fake_perform_translation(request, stream=False):
                yield ("translated chunk", None, None, None)
            mock_translation.side_effect = fake_perform_translation
            yield ChatAgent()

def run_async(gen):
    # Helper to run async generator and collect results
    return asyncio.run(_collect_async(gen))

async def _collect_async(gen):
    results = []
    async for item in gen:
        results.append(item)
    return results

def test_chat_event_sequence(agent):
    # Test that the chat method yields the expected event sequence
    message = "import '@openzeppelin/contracts/token/ERC20/ERC20.sol';\ncontract Foo {}"
    events = run_async(agent.chat(message, session_id="test1", stream=True, options={"optimize": True}))
    # Check that at least one of each event type is present
    event_types = [e["type"] for e in events]
    assert "stage" in event_types
    assert "content" in event_types
    assert any(e["type"] == "tool_start" for e in events)
    assert any(e["type"] == "tool_end" for e in events)
    # Check that the first event is a stage event (thinking)
    assert events[0]["type"] == "stage"
    assert events[0]["data"]["stage"] == "thinking"
    # Check that the last event is a stage event (done)
    assert events[-1]["type"] == "stage"
    assert events[-1]["data"]["stage"] == "done"

def test_chat_error_event(agent):
    # Patch agent.agent.astream_events to raise an exception during async iteration
    async def error_gen(*args, **kwargs):
        raise Exception("fail")
        yield  # Makes this an async generator
    agent.agent.astream_events = error_gen
    message = "contract Foo {}"
    events = run_async(agent.chat(message, session_id="errtest", stream=True))
    # Should yield an error event
    assert any(e["type"] == "error" for e in events)
    error_event = next(e for e in events if e["type"] == "error")
    assert "fail" in error_event["data"]["message"]

def test_session_options_storage(agent):
    # Test that session options are stored and retrieved correctly
    opts = {"optimize": True, "include_comments": False}
    agent.set_session_options("abc", opts)
    retrieved = agent.get_session_options("abc")
    assert retrieved["optimize"] is True
    assert retrieved["include_comments"] is False
    # Default fallback
    default = agent.get_session_options("notset")
    assert default["optimize"] is False
    assert default["include_comments"] is True

def test_clear_session(agent):
    agent.sessions["foo"] = [1, 2]
    agent.session_options["foo"] = {"optimize": True}
    agent.clear_session("foo")
    assert "foo" not in agent.sessions
    assert "foo" not in agent.session_options
