"""Tests for automatic interleaved-thinking beta header injection."""

import pytest

from claude_agent_sdk._internal.transport.subprocess_cli import SubprocessCLITransport
from claude_agent_sdk.types import ClaudeAgentOptions


def test_interleaved_thinking_beta_added_when_max_thinking_tokens_set():
    """Test that interleaved-thinking beta is automatically added when max_thinking_tokens is set."""
    options = ClaudeAgentOptions(
        max_thinking_tokens=8000,
        model="claude-opus-4-5-20251101",
    )
    
    transport = SubprocessCLITransport("test prompt", options)
    cmd = transport._build_command()
    
    # Find the --betas flag in the command
    betas_index = cmd.index("--betas")
    betas_value = cmd[betas_index + 1]
    
    # Should contain the interleaved-thinking beta
    assert "interleaved-thinking-2025-05-14" in betas_value


def test_interleaved_thinking_beta_added_with_existing_betas():
    """Test that interleaved-thinking beta is added alongside existing betas."""
    options = ClaudeAgentOptions(
        max_thinking_tokens=8000,
        betas=["some-other-beta-2025-01-01"],
        model="claude-opus-4-5-20251101",
    )
    
    transport = SubprocessCLITransport("test prompt", options)
    cmd = transport._build_command()
    
    # Find the --betas flag in the command
    betas_index = cmd.index("--betas")
    betas_value = cmd[betas_index + 1]
    
    # Should contain both betas
    assert "some-other-beta-2025-01-01" in betas_value
    assert "interleaved-thinking-2025-05-14" in betas_value


def test_interleaved_thinking_beta_not_duplicated():
    """Test that interleaved-thinking beta is not duplicated if already present."""
    options = ClaudeAgentOptions(
        max_thinking_tokens=8000,
        betas=["interleaved-thinking-2025-05-14"],
        model="claude-opus-4-5-20251101",
    )
    
    transport = SubprocessCLITransport("test prompt", options)
    cmd = transport._build_command()
    
    # Find the --betas flag in the command
    betas_index = cmd.index("--betas")
    betas_value = cmd[betas_index + 1]
    
    # Should only appear once
    assert betas_value.count("interleaved-thinking-2025-05-14") == 1


def test_no_betas_flag_when_no_thinking_and_no_betas():
    """Test that --betas flag is not present when neither max_thinking_tokens nor betas are set."""
    options = ClaudeAgentOptions(
        model="claude-opus-4-5-20251101",
    )
    
    transport = SubprocessCLITransport("test prompt", options)
    cmd = transport._build_command()
    
    # Should not have --betas flag
    assert "--betas" not in cmd


def test_interleaved_thinking_beta_works_with_opus_4_6():
    """Test that the beta is added for opus-4-6 (even though it's automatic there)."""
    options = ClaudeAgentOptions(
        max_thinking_tokens=8000,
        model="claude-opus-4-6",
    )
    
    transport = SubprocessCLITransport("test prompt", options)
    cmd = transport._build_command()
    
    # Find the --betas flag in the command
    betas_index = cmd.index("--betas")
    betas_value = cmd[betas_index + 1]
    
    # Should contain the interleaved-thinking beta (harmless for opus-4-6)
    assert "interleaved-thinking-2025-05-14" in betas_value


def test_max_thinking_tokens_flag_still_present():
    """Test that --max-thinking-tokens flag is still passed to CLI."""
    options = ClaudeAgentOptions(
        max_thinking_tokens=8000,
        model="claude-opus-4-5-20251101",
    )
    
    transport = SubprocessCLITransport("test prompt", options)
    cmd = transport._build_command()
    
    # Should have --max-thinking-tokens flag
    assert "--max-thinking-tokens" in cmd
    max_thinking_index = cmd.index("--max-thinking-tokens")
    assert cmd[max_thinking_index + 1] == "8000"
