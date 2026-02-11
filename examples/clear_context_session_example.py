"""Example demonstrating session-specific clear_context() functionality.

This example shows how to use clear_context(session_id=...) to clear
context for specific sessions, enabling more granular control over
conversation state management.
"""

import anyio

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    TextBlock,
)


async def main() -> None:
    """Demonstrate session-specific clear_context() usage."""
    
    # Configure options
    options = ClaudeAgentOptions(
        max_turns=1,
        allowed_tools=[],  # No tools needed for this example
    )

    async with ClaudeSDKClient(options=options) as client:
        print("=" * 60)
        print("Session-Specific Context Clearing Examples")
        print("=" * 60)
        
        # Example 1: Clear specific session while keeping others
        print("\n--- Example 1: Clear specific session ---")
        print("Starting conversation in session_A...")
        
        await client.query(
            "Remember this: The answer is 42",
            session_id="session_A"
        )
        
        async for msg in client.receive_response(session_id="session_A"):
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        print(f"Claude (session_A): {block.text}")
        
        # Clear only session_A
        print("\n--- Clearing context for session_A only ---")
        await client.clear_context(session_id="session_A")
        print("Context cleared for session_A!")
        
        # Reuse session_A - should not remember the previous conversation
        print("\n--- Reusing session_A (should not remember 42) ---")
        await client.query(
            "What did I tell you to remember?",
            session_id="session_A"
        )
        
        async for msg in client.receive_response(session_id="session_A"):
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        print(f"Claude (session_A): {block.text}")
        
        # Example 2: Clear all sessions at once
        print("\n\n" + "=" * 60)
        print("Example 2: Clear all sessions at once")
        print("=" * 60)
        
        # Clear all context
        print("\n--- Clearing all context (no session_id parameter) ---")
        await client.clear_context()
        print("All context cleared!")
        
        # Now we can use any session_id
        print("\n--- Starting new conversation in session_B ---")
        await client.query(
            "What is 2 + 2?",
            session_id="session_B"
        )
        
        async for msg in client.receive_response(session_id="session_B"):
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        print(f"Claude (session_B): {block.text}")
        
        # Example 3: Demonstrate session isolation
        print("\n\n" + "=" * 60)
        print("Example 3: Session isolation with selective clearing")
        print("=" * 60)
        
        # Clear all first
        await client.clear_context()
        
        # Start conversation in session_X
        print("\n--- Conversation in session_X ---")
        await client.query(
            "My favorite color is blue",
            session_id="session_X"
        )
        
        async for msg in client.receive_response(session_id="session_X"):
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        print(f"Claude (session_X): {block.text}")
        
        # Clear session_X specifically
        print("\n--- Clearing session_X ---")
        await client.clear_context(session_id="session_X")
        
        # Start new conversation in session_Y
        print("\n--- New conversation in session_Y ---")
        await client.query(
            "What is my favorite color?",
            session_id="session_Y"
        )
        
        async for msg in client.receive_response(session_id="session_Y"):
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        print(f"Claude (session_Y): {block.text}")
                        print("(Should not know about blue from session_X)")
        
        print("\n" + "=" * 60)
        print("Key Features of Session-Specific clear_context():")
        print("=" * 60)
        print("✓ Clear specific sessions: clear_context(session_id='session_A')")
        print("✓ Clear all sessions: clear_context()")
        print("✓ Reuse session IDs after clearing")
        print("✓ Maintain session isolation")
        print("✓ No reconnection overhead")
        print("✓ Fast in-process reset")


async def use_case_multi_user() -> None:
    """Example use case: Multi-user application with session management."""
    
    options = ClaudeAgentOptions(max_turns=1, allowed_tools=[])
    
    print("\n" + "=" * 60)
    print("Use Case: Multi-User Application")
    print("=" * 60)
    
    async with ClaudeSDKClient(options=options) as client:
        # Simulate multiple users
        users = ["user_alice", "user_bob", "user_charlie"]
        
        for user_id in users:
            print(f"\n--- Processing request from {user_id} ---")
            
            # Each user gets their own session
            await client.query(
                f"Hello, I'm {user_id}. What's 2+2?",
                session_id=user_id
            )
            
            async for msg in client.receive_response(session_id=user_id):
                if isinstance(msg, AssistantMessage):
                    for block in msg.content:
                        if isinstance(block, TextBlock):
                            print(f"Response to {user_id}: {block.text[:50]}...")
            
            # Clear context for this user after processing
            await client.clear_context(session_id=user_id)
            print(f"Context cleared for {user_id}")
        
        print("\n" + "=" * 60)
        print("Benefits for multi-user applications:")
        print("=" * 60)
        print("✓ Each user gets isolated session")
        print("✓ Clear context after each user request")
        print("✓ No context leakage between users")
        print("✓ Efficient resource usage (single client)")
        print("✓ Fast session cleanup")


async def use_case_testing() -> None:
    """Example use case: Testing with session-specific cleanup."""
    
    options = ClaudeAgentOptions(max_turns=1, allowed_tools=[])
    
    print("\n" + "=" * 60)
    print("Use Case: Testing with Session Cleanup")
    print("=" * 60)
    
    async with ClaudeSDKClient(options=options) as client:
        test_cases = [
            {"id": "test_1", "input": "What is 1+1?", "expected": "2"},
            {"id": "test_2", "input": "What is 2+2?", "expected": "4"},
            {"id": "test_3", "input": "What is 3+3?", "expected": "6"},
        ]
        
        for test in test_cases:
            print(f"\n--- Running {test['id']} ---")
            
            # Run test in isolated session
            await client.query(test["input"], session_id=test["id"])
            
            async for msg in client.receive_response(session_id=test["id"]):
                if isinstance(msg, AssistantMessage):
                    for block in msg.content:
                        if isinstance(block, TextBlock):
                            print(f"Result: {block.text[:50]}...")
            
            # Clear context for this test
            await client.clear_context(session_id=test["id"])
            print(f"Test {test['id']} completed and cleaned up")
        
        print("\n" + "=" * 60)
        print("Benefits for testing:")
        print("=" * 60)
        print("✓ Isolated test sessions")
        print("✓ Fast cleanup between tests")
        print("✓ No test interference")
        print("✓ Reusable client instance")


if __name__ == "__main__":
    # Run the main example
    anyio.run(main)
    
    # Uncomment to run use case examples (requires actual Claude Code CLI)
    # anyio.run(use_case_multi_user)
    # anyio.run(use_case_testing)
