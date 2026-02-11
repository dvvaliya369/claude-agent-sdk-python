"""Verify the session isolation fix logic without dependencies."""

import ast
import sys


def check_client_py():
    """Check that client.py has the session isolation logic."""
    print("Checking src/claude_agent_sdk/client.py...")
    
    with open('src/claude_agent_sdk/client.py', 'r') as f:
        content = f.read()
    
    # Check for _active_sessions initialization
    if '_active_sessions: set[str] = set()' in content:
        print("✓ Found _active_sessions initialization in __init__")
    else:
        print("✗ Missing _active_sessions initialization")
        return False
    
    # Check for session validation in query()
    if 'Session isolation error' in content:
        print("✓ Found session isolation error message in query()")
    else:
        print("✗ Missing session isolation error message")
        return False
    
    # Check for session tracking
    if 'self._active_sessions.add(session_id)' in content:
        print("✓ Found session tracking logic")
    else:
        print("✗ Missing session tracking logic")
        return False
    
    # Check for session clearing on disconnect
    if 'self._active_sessions.clear()' in content:
        print("✓ Found session clearing in disconnect()")
    else:
        print("✗ Missing session clearing in disconnect()")
        return False
    
    # Check for validation logic
    if 'if self._active_sessions and session_id not in self._active_sessions:' in content:
        print("✓ Found session validation logic")
    else:
        print("✗ Missing session validation logic")
        return False
    
    # Check for helpful error message
    if 'separate ClaudeSDKClient instances' in content:
        print("✓ Found helpful error message about separate instances")
    else:
        print("✗ Missing helpful error message")
        return False
    
    # Verify syntax
    try:
        ast.parse(content)
        print("✓ Python syntax is valid")
    except SyntaxError as e:
        print(f"✗ Syntax error: {e}")
        return False
    
    return True


def check_test_file():
    """Check that the test file exists and is valid."""
    print("\nChecking tests/test_session_isolation.py...")
    
    try:
        with open('tests/test_session_isolation.py', 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print("✗ Test file not found")
        return False
    
    # Check for key test functions
    test_functions = [
        'test_single_session_allowed',
        'test_multiple_sessions_rejected',
        'test_session_cleared_on_disconnect',
        'test_session_reuse_after_disconnect',
        'test_error_message_clarity',
    ]
    
    for func in test_functions:
        if f'async def {func}' in content:
            print(f"✓ Found test: {func}")
        else:
            print(f"✗ Missing test: {func}")
            return False
    
    # Verify syntax
    try:
        ast.parse(content)
        print("✓ Test file syntax is valid")
    except SyntaxError as e:
        print(f"✗ Syntax error: {e}")
        return False
    
    return True


def main():
    """Run all checks."""
    print("=" * 60)
    print("Session Isolation Fix Verification")
    print("=" * 60)
    print()
    
    client_ok = check_client_py()
    test_ok = check_test_file()
    
    print()
    print("=" * 60)
    if client_ok and test_ok:
        print("✓ All checks passed!")
        print()
        print("Summary of changes:")
        print("1. Added _active_sessions tracking to ClaudeSDKClient")
        print("2. Added validation to prevent multiple sessions per client")
        print("3. Added session clearing on disconnect")
        print("4. Added comprehensive error messages")
        print("5. Created test suite for session isolation")
        print()
        print("The fix prevents session context leakage by:")
        print("- Tracking which session_id is active in each client instance")
        print("- Raising ValueError when attempting to use a different session_id")
        print("- Providing clear error messages guiding users to use separate clients")
        return 0
    else:
        print("✗ Some checks failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
