"""Tests for session isolation in ClaudeSDKClient."""

import asyncio
import json
from unittest.mock import AsyncMock, Mock, patch

import anyio
import pytest

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeSDKClient,
    ResultMessage,
    TextBlock,
)


def create_mock_transport():
    """Create a properly configured mock transport for session testing."""
    mock_transport = AsyncMock()
    mock_transport.connect = AsyncMock()
    mock_transport.close = AsyncMock()
    mock_transport.end_input = AsyncMock()
    mock_transport.write = AsyncMock()
    mock_transport.is_ready = Mock(return_value=True)

    # Track written messages to simulate control protocol responses
    written_messages = []

    async def mock_write(data):
        written_messages.append(data)

    mock_transport.write.side_effect = mock_write

    # Default read_messages to handle control protocol and session-specific responses
    async def control_protocol_generator():
        # Wait for initialization request
        await asyncio.sleep(0.01)

        # Send initialization response
        for msg_str in written_messages:
            try:
                msg = json.loads(msg_str.strip())
                if (
                    msg.get("type") == "control_request"
                    and msg.get("request", {}).get("subtype") == "initialize"
                ):
                    yield {
                        "type": "control_response",
                        "response": {
                            "request_id": msg.get("request_id"),
                            "subtype": "success",
                            "commands": [],
                            "output_style": "default",
                        },
                    }
                    break
            except (json.JSONDecodeError, KeyError, AttributeError):
                pass

        # Track which sessions have been queried
        session_queries = {}
        last_check = len(written_messages)

        # Keep checking for user messages and respond appropriately
        for _ in range(100):  # Avoid infinite loop
            await asyncio.sleep(0.01)

            # Check for new messages
            for msg_str in written_messages[last_check:]:
                try:
                    msg = json.loads(msg_str.strip())
                    if msg.get("type") == "user":
                        session_id = msg.get("session_id", "default")
                        content = msg.get("message", {}).get("content", "")

                        # Track this query
                        if session_id not in session_queries:
                            session_queries[session_id] = []
                        session_queries[session_id].append(content)

                        # Respond with session-specific message
                        yield {
                            "type": "assistant",
                            "message": {
                                "role": "assistant",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": f"Response for session {session_id}: {content}",
                                    }
                                ],
                                "model": "claude-opus-4-1-20250805",
                            },
                        }
                        yield {
                            "type": "result",
                            "subtype": "success",
                            "duration_ms": 100,
                            "duration_api_ms": 50,
                            "is_error": False,
                            "num_turns": 1,
                            "session_id": session_id,
                            "total_cost_usd": 0.001,
                        }
                except (json.JSONDecodeError, KeyError, AttributeError):
                    pass

            last_check = len(written_messages)

    mock_transport.read_messages = control_protocol_generator
    return mock_transport


class TestSessionIsolation:
    """Test session isolation in ClaudeSDKClient."""

    def test_single_client_multiple_sessions(self):
        """Test that a single client can handle multiple sessions with isolated contexts.

        This test verifies that when using ClaudeSDKClient.query() with different
        session_ids, the responses are properly isolated and don't leak between sessions.
        """

        async def _test():
            with patch(
                "claude_agent_sdk._internal.transport.subprocess_cli.SubprocessCLITransport"
            ) as mock_transport_class:
                mock_transport = create_mock_transport()
                mock_transport_class.return_value = mock_transport

                async with ClaudeSDKClient() as client:
                    # Send two queries with different session IDs
                    await client.query("Question for session A", session_id="session-a")
                    await client.query("Question for session B", session_id="session-b")

                    # Collect responses - we expect 4 messages total (2 assistant + 2 result)
                    messages = []
                    async for msg in client.receive_messages():
                        messages.append(msg)
                        if len(messages) >= 4:
                            break

                    # Filter messages by type
                    assistant_messages = [
                        m for m in messages if isinstance(m, AssistantMessage)
                    ]
                    result_messages = [m for m in messages if isinstance(m, ResultMessage)]

                    # We should have 2 assistant messages and 2 result messages
                    assert len(assistant_messages) == 2, (
                        f"Expected 2 assistant messages, got {len(assistant_messages)}"
                    )
                    assert len(result_messages) == 2, (
                        f"Expected 2 result messages, got {len(result_messages)}"
                    )

                    # Extract text from assistant messages
                    responses = [
                        msg.content[0].text
                        for msg in assistant_messages
                        if isinstance(msg.content[0], TextBlock)
                    ]

                    # The first response should be for session A
                    assert "session-a" in responses[0].lower(), (
                        f"First response should mention session-a, got: {responses[0]}"
                    )
                    assert "Question for session A" in responses[0], (
                        f"First response should mention session A question, got: {responses[0]}"
                    )

                    # The second response should be for session B
                    assert "session-b" in responses[1].lower(), (
                        f"Second response should mention session-b, got: {responses[1]}"
                    )
                    assert "Question for session B" in responses[1], (
                        f"Second response should mention session B question, got: {responses[1]}"
                    )

                    # Verify session_ids in result messages
                    assert result_messages[0].session_id == "session-a", (
                        f"First result should have session-a, got: {result_messages[0].session_id}"
                    )
                    assert result_messages[1].session_id == "session-b", (
                        f"Second result should have session-b, got: {result_messages[1].session_id}"
                    )

        anyio.run(_test)

    def test_interleaved_session_responses(self):
        """Test that responses can be correctly attributed when sessions are interleaved.

        This is the more challenging case where we need to handle responses that
        come back in a different order than the queries were sent.
        """

        async def _test():
            with patch(
                "claude_agent_sdk._internal.transport.subprocess_cli.SubprocessCLITransport"
            ) as mock_transport_class:
                mock_transport = create_mock_transport()
                mock_transport_class.return_value = mock_transport

                async with ClaudeSDKClient() as client:
                    # Start concurrent queries for different sessions
                    async def query_session(session_id: str, question: str):
                        await client.query(question, session_id=session_id)
                        # Collect response for this session
                        async for msg in client.receive_messages():
                            if isinstance(msg, ResultMessage):
                                if msg.session_id == session_id:
                                    return msg
                        return None

                    # Run queries concurrently
                    async with anyio.create_task_group() as tg:
                        result_a = None
                        result_b = None

                        async def run_a():
                            nonlocal result_a
                            result_a = await query_session(
                                "session-a", "Question A"
                            )

                        async def run_b():
                            nonlocal result_b
                            result_b = await query_session(
                                "session-b", "Question B"
                            )

                        tg.start_soon(run_a)
                        tg.start_soon(run_b)

                    # Both queries should complete with correct session IDs
                    assert result_a is not None, "Session A result should not be None"
                    assert result_b is not None, "Session B result should not be None"
                    assert result_a.session_id == "session-a"
                    assert result_b.session_id == "session-b"

        # This test will likely fail with the current implementation
        # because there's no way to route responses back to the correct caller
        anyio.run(_test)
