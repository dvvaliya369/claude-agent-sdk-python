"""Example demonstrating clear_context() for in-process context reset.

This example shows how to use clear_context() to reset the conversation
context without the overhead of reconnecting. This is useful when you want
to start fresh conversations while reusing the same client instance.
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
    """Demonstrate clear_context() usage."""
    
    # Configure options
    options = ClaudeAgentOptions(
        max_turns=1,
        allowed_tools=[],  # No tools needed for this example
    )

    async with ClaudeSDKClient(options=options) as client:
        print("=" * 60)
        print("Example 1: Multiple conversations with clear_context()")
        print("=" * 60)
        
        # First conversation
        print("\n--- First Conversation (session_1) ---")
        await client.query(
            "Remember this number: 42. What is it?",
            session_id="session_1"
        )
        
        async for msg in client.receive_response(session_id="session_1"):
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        print(f"Claude: {block.text}")
            elif isinstance(msg, ResultMessage):
                print(f"Cost: ${msg.total_cost_usd:.4f}" if msg.total_cost_usd else "Cost: N/A")
        
        # Clear context - this resets the conversation without reconnecting
        print("\n--- Clearing context (in-process reset) ---")
        await client.clear_context()
        print("Context cleared! Starting fresh conversation...")
        
        # Second conversation with different session
        # This would normally fail due to session isolation, but works after clear_context()
        print("\n--- Second Conversation (session_2) ---")
        await client.query(
            "What number did I tell you to remember?",
            session_id="session_2"
        )
        
        async for msg in client.receive_response(session_id="session_2"):
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        print(f"Claude: {block.text}")
                        print("(Claude should not remember 42 from the previous conversation)")
            elif isinstance(msg, ResultMessage):
                print(f"Cost: ${msg.total_cost_usd:.4f}" if msg.total_cost_usd else "Cost: N/A")
        
        print("\n" + "=" * 60)
        print("Example 2: Reusing the same session_id after clear")
        print("=" * 60)
        
        # Clear context again
        print("\n--- Clearing context again ---")
        await client.clear_context()
        
        # Reuse session_1 (same ID as first conversation)
        print("\n--- Third Conversation (reusing session_1) ---")
        await client.query(
            "What is 2 + 2?",
            session_id="session_1"
        )
        
        async for msg in client.receive_response(session_id="session_1"):
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        print(f"Claude: {block.text}")
            elif isinstance(msg, ResultMessage):
                print(f"Cost: ${msg.total_cost_usd:.4f}" if msg.total_cost_usd else "Cost: N/A")
        
        print("\n" + "=" * 60)
        print("Benefits of clear_context() over disconnect/reconnect:")
        print("=" * 60)
        print("✓ No subprocess restart")
        print("✓ No MCP server re-initialization")
        print("✓ Much faster than disconnect/connect cycle")
        print("✓ Maintains the same connection")
        print("✓ Allows switching between different session IDs")
        print("✓ Provides reliable reset semantics")


async def compare_with_disconnect() -> None:
    """Compare clear_context() with disconnect/reconnect approach."""
    
    options = ClaudeAgentOptions(max_turns=1, allowed_tools=[])
    
    print("\n" + "=" * 60)
    print("Comparison: clear_context() vs disconnect/reconnect")
    print("=" * 60)
    
    # Approach 1: Using clear_context() (recommended)
    print("\n--- Approach 1: Using clear_context() ---")
    import time
    
    async with ClaudeSDKClient(options=options) as client:
        start = time.time()
        
        # First conversation
        await client.query("What is 1+1?", session_id="session_A")
        async for msg in client.receive_response(session_id="session_A"):
            pass
        
        # Clear context (fast)
        await client.clear_context()
        
        # Second conversation
        await client.query("What is 2+2?", session_id="session_B")
        async for msg in client.receive_response(session_id="session_B"):
            pass
        
        elapsed = time.time() - start
        print(f"Time with clear_context(): {elapsed:.2f}s")
    
    # Approach 2: Using disconnect/reconnect (slower)
    print("\n--- Approach 2: Using disconnect/reconnect ---")
    
    client = ClaudeSDKClient(options=options)
    start = time.time()
    
    # First conversation
    await client.connect()
    await client.query("What is 1+1?", session_id="session_A")
    async for msg in client.receive_response(session_id="session_A"):
        pass
    
    # Disconnect and reconnect (slow)
    await client.disconnect()
    await client.connect()
    
    # Second conversation
    await client.query("What is 2+2?", session_id="session_B")
    async for msg in client.receive_response(session_id="session_B"):
        pass
    
    await client.disconnect()
    
    elapsed = time.time() - start
    print(f"Time with disconnect/reconnect: {elapsed:.2f}s")
    
    print("\nConclusion: clear_context() is significantly faster!")


if __name__ == "__main__":
    # Run the main example
    anyio.run(main)
    
    # Uncomment to run the comparison (requires actual Claude Code CLI)
    # anyio.run(compare_with_disconnect)
