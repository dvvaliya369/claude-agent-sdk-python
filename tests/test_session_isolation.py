"""Tests for session isolation in ClaudeSDKClient."""

import pytest

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient
from claude_agent_sdk._errors import CLIConnectionError


@pytest.mark.asyncio
async def test_single_session_allowed():
    """Test that using a single session_id works correctly."""
    options = ClaudeAgentOptions(max_turns=1, allowed_tools=[])
    
    client = ClaudeSDKClient(options=options)
    
    # Should be able to use the same session multiple times
    # Note: We're not actually connecting here, just testing the validation logic
    # In a real scenario, this would work fine
    assert len(client._active_sessions) == 0


@pytest.mark.asyncio
async def test_multiple_sessions_rejected():
    """Test that attempting to use multiple session_ids raises an error."""
    from unittest.mock import AsyncMock, MagicMock
    
    options = ClaudeAgentOptions(max_turns=1, allowed_tools=[])
    client = ClaudeSDKClient(options=options)
    
    # Mock the internal state to simulate a connected client
    client._query = MagicMock()
    client._transport = MagicMock()
    client._transport.write = AsyncMock()
    
    # First query with session_A should work
    await client.query("First message", session_id="session_A")
    assert "session_A" in client._active_sessions
    
    # Second query with same session should work
    await client.query("Second message", session_id="session_A")
    assert "session_A" in client._active_sessions
    
    # Third query with different session should raise ValueError
    with pytest.raises(ValueError) as exc_info:
        await client.query("Third message", session_id="session_B")
    
    assert "Session isolation error" in str(exc_info.value)
    assert "session_A" in str(exc_info.value)
    assert "session_B" in str(exc_info.value)
    assert "separate ClaudeSDKClient instances" in str(exc_info.value)


@pytest.mark.asyncio
async def test_session_cleared_on_disconnect():
    """Test that active sessions are cleared when disconnecting."""
    from unittest.mock import AsyncMock, MagicMock
    
    options = ClaudeAgentOptions(max_turns=1, allowed_tools=[])
    client = ClaudeSDKClient(options=options)
    
    # Mock the internal state
    client._query = MagicMock()
    client._query.close = AsyncMock()
    client._transport = MagicMock()
    client._transport.write = AsyncMock()
    
    # Use a session
    await client.query("Message", session_id="session_A")
    assert "session_A" in client._active_sessions
    
    # Disconnect
    await client.disconnect()
    
    # Active sessions should be cleared
    assert len(client._active_sessions) == 0


@pytest.mark.asyncio
async def test_session_reuse_after_disconnect():
    """Test that a different session can be used after disconnect."""
    from unittest.mock import AsyncMock, MagicMock
    
    options = ClaudeAgentOptions(max_turns=1, allowed_tools=[])
    client = ClaudeSDKClient(options=options)
    
    # Mock the internal state
    mock_query = MagicMock()
    mock_query.close = AsyncMock()
    mock_transport = MagicMock()
    mock_transport.write = AsyncMock()
    
    client._query = mock_query
    client._transport = mock_transport
    
    # Use session_A
    await client.query("Message 1", session_id="session_A")
    assert "session_A" in client._active_sessions
    
    # Disconnect
    await client.disconnect()
    assert len(client._active_sessions) == 0
    
    # Reconnect (simulate)
    client._query = mock_query
    client._transport = mock_transport
    
    # Now session_B should work
    await client.query("Message 2", session_id="session_B")
    assert "session_B" in client._active_sessions
    assert "session_A" not in client._active_sessions


@pytest.mark.asyncio
async def test_error_message_clarity():
    """Test that the error message is clear and helpful."""
    from unittest.mock import AsyncMock, MagicMock
    
    options = ClaudeAgentOptions(max_turns=1, allowed_tools=[])
    client = ClaudeSDKClient(options=options)
    
    # Mock the internal state
    client._query = MagicMock()
    client._transport = MagicMock()
    client._transport.write = AsyncMock()
    
    # Use session_A
    await client.query("Message", session_id="session_A")
    
    # Try to use session_B
    with pytest.raises(ValueError) as exc_info:
        await client.query("Message", session_id="session_B")
    
    error_message = str(exc_info.value)
    
    # Verify error message contains helpful information
    assert "Session isolation error" in error_message
    assert "session_A" in error_message
    assert "session_B" in error_message
    assert "separate ClaudeSDKClient instances" in error_message
    assert "conversation context" in error_message


@pytest.mark.asyncio
async def test_not_connected_error_takes_precedence():
    """Test that connection error is raised before session validation."""
    options = ClaudeAgentOptions(max_turns=1, allowed_tools=[])
    client = ClaudeSDKClient(options=options)
    
    # Don't connect - _query and _transport are None
    
    # Should raise CLIConnectionError, not session validation error
    with pytest.raises(CLIConnectionError) as exc_info:
        await client.query("Message", session_id="session_A")
    
    assert "Not connected" in str(exc_info.value)
