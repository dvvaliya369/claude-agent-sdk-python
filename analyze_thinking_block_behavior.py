#!/usr/bin/env python3
"""
Analysis script to investigate ThinkingBlock behavioral changes between
claude-opus-4-5-20251101 and claude-opus-4-6.

This script will:
1. Test both models with identical prompts
2. Analyze the response structure and content blocks
3. Determine if ThinkingBlock content is present in the response stream
4. Identify whether the change is intentional, deprecated, or a regression
"""

import asyncio
import json
import os
from typing import Any

from claude_agent_sdk import ClaudeSDKClient
from claude_agent_sdk.types import (
    AssistantMessage,
    ClaudeAgentOptions,
    RedactedThinkingBlock,
    ResultMessage,
    StreamEvent,
    SystemMessage,
    TextBlock,
    ThinkingBlock,
)


async def test_model_thinking_behavior(
    model: str, include_partial: bool = False
) -> dict[str, Any]:
    """Test a specific model's thinking block behavior.

    Args:
        model: The model identifier to test
        include_partial: Whether to include partial messages (streaming)

    Returns:
        Dictionary containing analysis results
    """
    print(f"\n{'='*80}")
    print(f"Testing model: {model}")
    print(f"Include partial messages: {include_partial}")
    print(f"{'='*80}\n")

    options = ClaudeAgentOptions(
        model=model,
        max_turns=2,
        include_partial_messages=include_partial,
        env={
            "MAX_THINKING_TOKENS": "8000",
        },
    )

    collected_messages: list[Any] = []
    thinking_blocks_found = []
    redacted_thinking_blocks_found = []
    stream_events_found = []
    thinking_deltas_found = []

    try:
        async with ClaudeSDKClient(options) as client:
            # Use a prompt that should trigger extended thinking
            await client.query(
                "Think step by step about what is 127 * 89. "
                "Show your reasoning process, then provide the answer."
            )

            async for message in client.receive_response():
                collected_messages.append(message)

                # Analyze AssistantMessage for thinking blocks
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, ThinkingBlock):
                            thinking_blocks_found.append(
                                {
                                    "thinking": block.thinking[:100]
                                    + "..."
                                    if len(block.thinking) > 100
                                    else block.thinking,
                                    "signature": block.signature,
                                    "full_length": len(block.thinking),
                                }
                            )
                        elif isinstance(block, RedactedThinkingBlock):
                            redacted_thinking_blocks_found.append(
                                {
                                    "data": block.data[:50]
                                    + "..."
                                    if len(block.data) > 50
                                    else block.data,
                                    "full_length": len(block.data),
                                }
                            )

                # Analyze StreamEvent for thinking deltas
                if isinstance(message, StreamEvent):
                    stream_events_found.append(message.event.get("type"))
                    event = message.event
                    if event.get("type") == "content_block_delta":
                        delta = event.get("delta", {})
                        if delta.get("type") == "thinking_delta":
                            thinking_deltas_found.append(delta.get("thinking", ""))

    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        return {
            "model": model,
            "include_partial": include_partial,
            "error": str(e),
            "error_type": type(e).__name__,
        }

    # Compile results
    message_types = [type(msg).__name__ for msg in collected_messages]
    unique_stream_event_types = list(set(stream_events_found))

    results = {
        "model": model,
        "include_partial": include_partial,
        "total_messages": len(collected_messages),
        "message_types": message_types,
        "thinking_blocks_count": len(thinking_blocks_found),
        "thinking_blocks": thinking_blocks_found,
        "redacted_thinking_blocks_count": len(redacted_thinking_blocks_found),
        "redacted_thinking_blocks": redacted_thinking_blocks_found,
        "stream_events_count": len(stream_events_found),
        "unique_stream_event_types": unique_stream_event_types,
        "thinking_deltas_count": len(thinking_deltas_found),
        "combined_thinking_delta_length": len("".join(thinking_deltas_found)),
        "has_thinking_content": len(thinking_blocks_found) > 0
        or len(thinking_deltas_found) > 0,
    }

    # Print summary
    print(f"\nResults for {model}:")
    print(f"  Total messages: {results['total_messages']}")
    print(f"  Message types: {set(message_types)}")
    print(f"  ThinkingBlocks found: {results['thinking_blocks_count']}")
    print(
        f"  RedactedThinkingBlocks found: {results['redacted_thinking_blocks_count']}"
    )
    print(f"  StreamEvents found: {results['stream_events_count']}")
    print(f"  Thinking deltas found: {results['thinking_deltas_count']}")
    print(f"  Has thinking content: {results['has_thinking_content']}")

    if thinking_blocks_found:
        print(f"\n  ThinkingBlock samples:")
        for i, tb in enumerate(thinking_blocks_found[:2], 1):
            print(f"    {i}. Length: {tb['full_length']}, Preview: {tb['thinking']}")

    if thinking_deltas_found:
        combined = "".join(thinking_deltas_found)
        print(f"\n  Combined thinking deltas:")
        print(f"    Length: {len(combined)}")
        print(f"    Preview: {combined[:100]}...")

    return results


async def compare_models():
    """Compare thinking block behavior across different model versions."""
    print("\n" + "=" * 80)
    print("THINKING BLOCK BEHAVIORAL ANALYSIS")
    print("Comparing claude-opus-4-5-20251101 vs claude-opus-4-6")
    print("=" * 80)

    # Test configurations
    test_configs = [
        ("claude-opus-4-5-20251101", False),
        ("claude-opus-4-5-20251101", True),
        ("claude-opus-4-6", False),
        ("claude-opus-4-6", True),
    ]

    all_results = []

    for model, include_partial in test_configs:
        result = await test_model_thinking_behavior(model, include_partial)
        all_results.append(result)
        await asyncio.sleep(1)  # Brief pause between tests

    # Comparative analysis
    print("\n" + "=" * 80)
    print("COMPARATIVE ANALYSIS")
    print("=" * 80)

    opus_45_no_stream = all_results[0]
    opus_45_stream = all_results[1]
    opus_46_no_stream = all_results[2]
    opus_46_stream = all_results[3]

    print("\n1. ThinkingBlock presence in non-streaming mode:")
    print(
        f"   claude-opus-4-5-20251101: {opus_45_no_stream['has_thinking_content']} "
        f"({opus_45_no_stream['thinking_blocks_count']} blocks)"
    )
    print(
        f"   claude-opus-4-6: {opus_46_no_stream['has_thinking_content']} "
        f"({opus_46_no_stream['thinking_blocks_count']} blocks)"
    )

    print("\n2. ThinkingBlock presence in streaming mode:")
    print(
        f"   claude-opus-4-5-20251101: {opus_45_stream['has_thinking_content']} "
        f"({opus_45_stream['thinking_deltas_count']} deltas)"
    )
    print(
        f"   claude-opus-4-6: {opus_46_stream['has_thinking_content']} "
        f"({opus_46_stream['thinking_deltas_count']} deltas)"
    )

    print("\n3. RedactedThinkingBlock presence:")
    print(
        f"   claude-opus-4-5-20251101 (no stream): "
        f"{opus_45_no_stream['redacted_thinking_blocks_count']}"
    )
    print(
        f"   claude-opus-4-5-20251101 (stream): "
        f"{opus_45_stream['redacted_thinking_blocks_count']}"
    )
    print(
        f"   claude-opus-4-6 (no stream): "
        f"{opus_46_no_stream['redacted_thinking_blocks_count']}"
    )
    print(
        f"   claude-opus-4-6 (stream): "
        f"{opus_46_stream['redacted_thinking_blocks_count']}"
    )

    # Determine the nature of the change
    print("\n" + "=" * 80)
    print("CONCLUSION")
    print("=" * 80)

    thinking_lost_no_stream = (
        opus_45_no_stream["has_thinking_content"]
        and not opus_46_no_stream["has_thinking_content"]
    )
    thinking_lost_stream = (
        opus_45_stream["has_thinking_content"]
        and not opus_46_stream["has_thinking_content"]
    )

    if thinking_lost_no_stream or thinking_lost_stream:
        print("\n⚠️  BEHAVIORAL CHANGE DETECTED:")
        print(
            "   ThinkingBlock content is no longer included in claude-opus-4-6 responses."
        )

        if (
            opus_46_no_stream["redacted_thinking_blocks_count"] > 0
            or opus_46_stream["redacted_thinking_blocks_count"] > 0
        ):
            print("\n📋 ANALYSIS: INTENTIONAL CHANGE (Privacy/Safety)")
            print(
                "   - ThinkingBlocks have been replaced with RedactedThinkingBlocks"
            )
            print(
                "   - This appears to be an intentional privacy/safety feature change"
            )
            print(
                "   - The model still performs extended thinking, but content is encrypted"
            )
        else:
            print("\n📋 ANALYSIS: POTENTIAL REGRESSION OR API CHANGE")
            print("   - ThinkingBlocks are completely absent from responses")
            print("   - No RedactedThinkingBlocks found as replacement")
            print("   - This could be:")
            print("     a) A regression bug in the model or API")
            print("     b) An intentional deprecation without replacement")
            print("     c) A configuration or feature flag change")
    else:
        print("\n✅ NO BEHAVIORAL CHANGE DETECTED:")
        print("   ThinkingBlock behavior is consistent across both model versions.")

    # Save detailed results
    output_file = "/vercel/sandbox/thinking_block_analysis_results.json"
    with open(output_file, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\n📄 Detailed results saved to: {output_file}")

    return all_results


if __name__ == "__main__":
    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY environment variable not set")
        print("Please set your API key to run this analysis")
        exit(1)

    # Run the analysis
    asyncio.run(compare_models())
