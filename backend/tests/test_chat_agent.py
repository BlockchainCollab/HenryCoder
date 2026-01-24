import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from agent_service import ChatAgent, StreamEvent

@pytest.fixture
def agent():
    # Patch the LLM and base objects for all tests
    with patch("agent_service.ChatOpenAI") as mock_llm:
        # Mock LLM agent's astream_events to yield a sequence of events
        mock_agent = MagicMock()
        
        async def fake_astream_events(*args, **kwargs):
            yield {"event": "on_tool_start", "name": "createContract", "data": {"input": "{'name': 'MyContract'}"}, "run_id": "1"}
            yield {"event": "on_tool_end", "name": "createContract", "success": True, "run_id": "1"}
            yield {"event": "on_tool_start", "name": "translateFunctions", "data": {"input": "{'interfaceOrContractName': 'MyContract'}"}, "run_id": "2"}
            yield {"event": "on_tool_end", "name": "translateFunctions", "success": True, "run_id": "2"}
            yield {"event": "on_chat_model_stream", "data": {"chunk": MagicMock(content="Final thoughts from agent.")}}
        
        mock_agent.astream_events = fake_astream_events
        # Patch ChatOpenAI to return a dummy llm
        mock_llm.return_value = MagicMock()
        
        # Patch create_agent to return our mock agent
        with patch("agent_service.create_agent", return_value=mock_agent):
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
    message = "contract MyContract {}"
    # We need to set a session ID and source
    events = run_async(agent.chat(message, session_id="test1", stream=True, options={"smart": True}))
    
    # Check for expected event types
    event_types = [e["type"] for e in events]
    assert "stage" in event_types
    assert "tool_start" in event_types
    assert "tool_end" in event_types
    assert "code_snapshot" in event_types
    
    # Verify stages
    assert events[0]["type"] == "stage"
    assert events[0]["data"]["stage"] == "thinking"
    
    # Verify tool events
    tool_starts = [e for e in events if e["type"] == "tool_start"]
    assert any(t["data"]["tool"] == "createContract" for t in tool_starts)
    assert any(t["data"]["tool"] == "translateFunctions" for t in tool_starts)

def test_chat_error_handling(agent):
    # Patch agent.agent.astream_events to raise an exception
    async def error_gen(*args, **kwargs):
        raise Exception("Agent failed")
        yield
    agent.agent.astream_events = error_gen
    
    message = "contract Failed {}"
    events = run_async(agent.chat(message, session_id="errtest", stream=True))
    
    assert any(e["type"] == "error" for e in events)
    error_event = next(e for e in events if e["type"] == "error")
    assert "Agent failed" in error_event["data"]["message"]

def test_session_management(agent):
    opts = {"smart": True, "optimize": True}
    agent.set_session_options("sess1", opts)
    assert agent.get_session_options("sess1") == opts
    
    # Test clear_session
    agent.clear_session("sess1")
    assert agent.get_session_options("sess1") != opts # Should return defaults

@pytest.mark.asyncio
async def test_fix_code_success(agent):
    # Mock the fix_llm response
    mock_response = MagicMock()
    mock_response.content = "fixed Ralph code"
    agent.fix_llm.ainvoke = AsyncMock(return_value=mock_response)
    
    # Mock the compilation check
    with patch.object(agent, "_compile_ralph_code", return_value={"success": True}) as mock_compile:
        gen = agent.fix_code("broken code", "error message")
        events = []
        async for e in gen:
            events.append(e)
            
        assert any(e["type"] == "stage" and e["data"]["stage"] == "fixing" for e in events)
        assert any(e["type"] == "result" and e["data"]["success"] is True for e in events)
        result_event = next(e for e in events if e["type"] == "result")
        assert result_event["data"]["fixed_code"] == "fixed Ralph code"

@pytest.mark.asyncio
async def test_fix_code_failure(agent):
    # Mock the fix_llm response
    mock_response = MagicMock()
    mock_response.content = "still broken code"
    agent.fix_llm.ainvoke = AsyncMock(return_value=mock_response)
    
    # Mock the compilation check to always fail
    with patch.object(agent, "_compile_ralph_code", return_value={"success": False, "error": "still bad"}) as mock_compile:
        gen = agent.fix_code("broken code", "error message", max_iterations=2)
        events = []
        async for e in gen:
            events.append(e)
            
        assert any(e["type"] == "result" and e["data"]["success"] is False for e in events)
        result_event = next(e for e in events if e["type"] == "result")
        assert result_event["data"]["iterations"] == 2
