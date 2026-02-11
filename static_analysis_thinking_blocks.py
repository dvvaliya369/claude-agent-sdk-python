#!/usr/bin/env python3
"""
Static analysis of ThinkingBlock behavior based on existing test data,
code structure, and API patterns.

This script analyzes the codebase to understand the behavioral change
between claude-opus-4-5-20251101 and claude-opus-4-6 without requiring
live API calls.
"""

import json
import re
from pathlib import Path


def analyze_test_files():
    """Analyze test files for ThinkingBlock usage patterns."""
    print("=" * 80)
    print("ANALYZING TEST FILES FOR THINKING BLOCK PATTERNS")
    print("=" * 80)

    test_parser_path = Path("/vercel/sandbox/tests/test_message_parser.py")
    test_e2e_path = Path("/vercel/sandbox/e2e-tests/test_include_partial_messages.py")

    findings = {
        "models_with_thinking_blocks": set(),
        "models_with_redacted_thinking": set(),
        "thinking_block_tests": [],
        "redacted_thinking_tests": [],
    }

    # Analyze test_message_parser.py
    if test_parser_path.exists():
        content = test_parser_path.read_text()

        # Find all model references with thinking blocks
        thinking_pattern = r'"model":\s*"([^"]+)".*?thinking'
        for match in re.finditer(thinking_pattern, content, re.DOTALL):
            model = match.group(1)
            findings["models_with_thinking_blocks"].add(model)

        # Find all model references with redacted thinking
        redacted_pattern = r'"model":\s*"([^"]+)".*?redacted_thinking'
        for match in re.finditer(redacted_pattern, content, re.DOTALL):
            model = match.group(1)
            findings["models_with_redacted_thinking"].add(model)

        # Count test functions
        thinking_tests = re.findall(
            r"def (test_.*thinking.*)\(", content, re.IGNORECASE
        )
        findings["thinking_block_tests"] = thinking_tests

    print("\n1. Models referenced with ThinkingBlock:")
    for model in sorted(findings["models_with_thinking_blocks"]):
        print(f"   - {model}")

    print("\n2. Models referenced with RedactedThinkingBlock:")
    for model in sorted(findings["models_with_redacted_thinking"]):
        print(f"   - {model}")

    print("\n3. ThinkingBlock-related test functions:")
    for test in findings["thinking_block_tests"]:
        print(f"   - {test}")

    return findings


def analyze_type_definitions():
    """Analyze type definitions for ThinkingBlock support."""
    print("\n" + "=" * 80)
    print("ANALYZING TYPE DEFINITIONS")
    print("=" * 80)

    types_path = Path("/vercel/sandbox/src/claude_agent_sdk/types.py")
    content = types_path.read_text()

    # Find ThinkingBlock definition
    thinking_match = re.search(
        r"class ThinkingBlock:.*?(?=\n\n|\nclass)", content, re.DOTALL
    )
    redacted_match = re.search(
        r"class RedactedThinkingBlock:.*?(?=\n\n|\nclass)", content, re.DOTALL
    )

    print("\n1. ThinkingBlock definition:")
    if thinking_match:
        print(f"   {thinking_match.group(0)}")

    print("\n2. RedactedThinkingBlock definition:")
    if redacted_match:
        print(f"   {redacted_match.group(0)}")

    # Check ContentBlock union
    content_block_match = re.search(r"ContentBlock = \(.*?\)", content, re.DOTALL)
    print("\n3. ContentBlock union type:")
    if content_block_match:
        print(f"   {content_block_match.group(0)}")


def analyze_message_parser():
    """Analyze message parser for thinking block handling."""
    print("\n" + "=" * 80)
    print("ANALYZING MESSAGE PARSER")
    print("=" * 80)

    parser_path = Path("/vercel/sandbox/src/claude_agent_sdk/_internal/message_parser.py")
    content = parser_path.read_text()

    # Find thinking block parsing logic
    thinking_parse = re.search(
        r'case "thinking":.*?(?=case |$)', content, re.DOTALL
    )
    redacted_parse = re.search(
        r'case "redacted_thinking":.*?(?=case |$)', content, re.DOTALL
    )

    print("\n1. ThinkingBlock parsing logic:")
    if thinking_parse:
        print(f"   {thinking_parse.group(0)[:200]}...")

    print("\n2. RedactedThinkingBlock parsing logic:")
    if redacted_parse:
        print(f"   {redacted_parse.group(0)[:200]}...")


def analyze_changelog():
    """Analyze changelog for relevant changes."""
    print("\n" + "=" * 80)
    print("ANALYZING CHANGELOG")
    print("=" * 80)

    changelog_path = Path("/vercel/sandbox/CHANGELOG.md")
    content = changelog_path.read_text()

    # Search for thinking-related changes
    thinking_mentions = []
    for line in content.split("\n"):
        if re.search(r"thinking|extended.*think", line, re.IGNORECASE):
            thinking_mentions.append(line)

    print("\n1. Thinking-related changelog entries:")
    if thinking_mentions:
        for mention in thinking_mentions:
            print(f"   {mention}")
    else:
        print("   No explicit mentions of thinking blocks in changelog")

    # Search for model version changes
    model_mentions = []
    for line in content.split("\n"):
        if re.search(r"opus-4-[56]|model.*version", line, re.IGNORECASE):
            model_mentions.append(line)

    print("\n2. Model version mentions:")
    if model_mentions:
        for mention in model_mentions:
            print(f"   {mention}")
    else:
        print("   No explicit model version changes in changelog")


def analyze_api_patterns():
    """Analyze API response patterns from test data."""
    print("\n" + "=" * 80)
    print("ANALYZING API RESPONSE PATTERNS")
    print("=" * 80)

    test_parser_path = Path("/vercel/sandbox/tests/test_message_parser.py")
    content = test_parser_path.read_text()

    # Extract test data structures
    print("\n1. ThinkingBlock test data structure:")
    thinking_test = re.search(
        r'def test_parse_assistant_message_with_thinking.*?(?=\n    def )',
        content,
        re.DOTALL,
    )
    if thinking_test:
        # Extract the data dict
        data_match = re.search(r'data = \{.*?\n        \}', thinking_test.group(0), re.DOTALL)
        if data_match:
            print(f"   {data_match.group(0)}")

    print("\n2. RedactedThinkingBlock test data structure:")
    redacted_test = re.search(
        r'def test_parse_assistant_message_with_redacted_thinking.*?(?=\n    def )',
        content,
        re.DOTALL,
    )
    if redacted_test:
        # Extract the data dict
        data_match = re.search(r'data = \{.*?\n        \}', redacted_test.group(0), re.DOTALL)
        if data_match:
            print(f"   {data_match.group(0)}")


def determine_behavioral_change():
    """Determine the nature of the behavioral change based on static analysis."""
    print("\n" + "=" * 80)
    print("BEHAVIORAL CHANGE ANALYSIS")
    print("=" * 80)

    test_parser_path = Path("/vercel/sandbox/tests/test_message_parser.py")
    content = test_parser_path.read_text()

    # Check which models are used with which thinking block types
    opus_45_contexts = []
    opus_46_contexts = []

    # Find all test contexts for opus-4-5-20251101
    for match in re.finditer(
        r'(def test_\w+.*?)"model":\s*"claude-opus-4-5-20251101".*?(?=\n    def |\Z)',
        content,
        re.DOTALL,
    ):
        test_name = re.search(r'def (test_\w+)', match.group(0))
        has_thinking = "thinking" in match.group(0) and "redacted" not in match.group(0)
        has_redacted = "redacted_thinking" in match.group(0)
        opus_45_contexts.append({
            "test": test_name.group(1) if test_name else "unknown",
            "has_thinking": has_thinking,
            "has_redacted": has_redacted,
        })

    # Find all test contexts for opus-4-6
    for match in re.finditer(
        r'(def test_\w+.*?)"model":\s*"claude-opus-4-6".*?(?=\n    def |\Z)',
        content,
        re.DOTALL,
    ):
        test_name = re.search(r'def (test_\w+)', match.group(0))
        has_thinking = '"type": "thinking"' in match.group(0)
        has_redacted = '"type": "redacted_thinking"' in match.group(0)
        opus_46_contexts.append({
            "test": test_name.group(1) if test_name else "unknown",
            "has_thinking": has_thinking,
            "has_redacted": has_redacted,
        })

    print("\n1. claude-opus-4-5-20251101 test contexts:")
    for ctx in opus_45_contexts:
        print(f"   - {ctx['test']}: thinking={ctx['has_thinking']}, redacted={ctx['has_redacted']}")

    print("\n2. claude-opus-4-6 test contexts:")
    for ctx in opus_46_contexts:
        print(f"   - {ctx['test']}: thinking={ctx['has_thinking']}, redacted={ctx['has_redacted']}")

    # Determine pattern
    print("\n" + "=" * 80)
    print("CONCLUSION")
    print("=" * 80)

    opus_45_has_thinking = any(ctx["has_thinking"] for ctx in opus_45_contexts)
    opus_46_has_thinking = any(ctx["has_thinking"] for ctx in opus_46_contexts)
    opus_46_has_redacted = any(ctx["has_redacted"] for ctx in opus_46_contexts)

    print(f"\nopus-4-5-20251101 has ThinkingBlock tests: {opus_45_has_thinking}")
    print(f"opus-4-6 has ThinkingBlock tests: {opus_46_has_thinking}")
    print(f"opus-4-6 has RedactedThinkingBlock tests: {opus_46_has_redacted}")

    if opus_46_has_thinking and opus_46_has_redacted:
        print("\n📋 ANALYSIS: BOTH TYPES SUPPORTED")
        print("   - opus-4-6 supports both ThinkingBlock and RedactedThinkingBlock")
        print("   - This suggests the model can return either type depending on content")
        print("   - Likely a safety/privacy feature where sensitive thinking is redacted")
    elif opus_46_has_redacted and not opus_46_has_thinking:
        print("\n📋 ANALYSIS: TRANSITION TO REDACTED THINKING")
        print("   - opus-4-6 primarily uses RedactedThinkingBlock")
        print("   - This appears to be an intentional privacy/safety change")
        print("   - Thinking still occurs but content is encrypted")
    elif not opus_46_has_thinking and not opus_46_has_redacted:
        print("\n📋 ANALYSIS: THINKING BLOCKS REMOVED")
        print("   - opus-4-6 has no thinking block tests")
        print("   - This could indicate deprecation or regression")
    else:
        print("\n📋 ANALYSIS: UNCLEAR PATTERN")
        print("   - Mixed or insufficient test data")

    return {
        "opus_45_has_thinking": opus_45_has_thinking,
        "opus_46_has_thinking": opus_46_has_thinking,
        "opus_46_has_redacted": opus_46_has_redacted,
    }


def main():
    """Run complete static analysis."""
    print("\n" + "=" * 80)
    print("STATIC ANALYSIS: ThinkingBlock Behavioral Change")
    print("claude-opus-4-5-20251101 vs claude-opus-4-6")
    print("=" * 80)

    # Run all analyses
    test_findings = analyze_test_files()
    analyze_type_definitions()
    analyze_message_parser()
    analyze_changelog()
    analyze_api_patterns()
    conclusion = determine_behavioral_change()

    # Save results
    results = {
        "test_findings": {
            "models_with_thinking_blocks": list(test_findings["models_with_thinking_blocks"]),
            "models_with_redacted_thinking": list(test_findings["models_with_redacted_thinking"]),
            "thinking_block_tests": test_findings["thinking_block_tests"],
        },
        "conclusion": conclusion,
    }

    output_file = Path("/vercel/sandbox/static_analysis_results.json")
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n📄 Results saved to: {output_file}")


if __name__ == "__main__":
    main()
