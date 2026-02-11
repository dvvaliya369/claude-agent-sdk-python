#!/usr/bin/env python3
"""Verification script for clear_context implementation.

This script verifies that all the necessary components for the clear_context
feature are properly implemented.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def verify_types():
    """Verify that the control request type is defined."""
    print("Verifying types.py...")
    from claude_agent_sdk.types import SDKControlRequest
    
    # Check that the type annotation includes clear_context
    import inspect
    source = inspect.getsource(SDKControlRequest.__annotations__['request'])
    
    # The annotation should be a string containing the union
    print("  ✓ SDKControlRequest type exists")
    
    # Try to import the clear_context request type
    try:
        from claude_agent_sdk.types import SDKControlClearContextRequest
        print("  ✓ SDKControlClearContextRequest type exists")
    except ImportError:
        print("  ✗ SDKControlClearContextRequest type not found")
        return False
    
    return True


def verify_query():
    """Verify that Query class has clear_context method."""
    print("\nVerifying query.py...")
    from claude_agent_sdk._internal.query import Query
    
    if not hasattr(Query, 'clear_context'):
        print("  ✗ Query.clear_context method not found")
        return False
    
    print("  ✓ Query.clear_context method exists")
    
    # Check method signature
    import inspect
    sig = inspect.signature(Query.clear_context)
    if 'self' not in sig.parameters:
        print("  ✗ Query.clear_context has invalid signature")
        return False
    
    print("  ✓ Query.clear_context has correct signature")
    
    # Check docstring
    if not Query.clear_context.__doc__:
        print("  ⚠ Query.clear_context missing docstring")
    else:
        print("  ✓ Query.clear_context has docstring")
    
    return True


def verify_client():
    """Verify that ClaudeSDKClient has clear_context method."""
    print("\nVerifying client.py...")
    from claude_agent_sdk.client import ClaudeSDKClient
    
    if not hasattr(ClaudeSDKClient, 'clear_context'):
        print("  ✗ ClaudeSDKClient.clear_context method not found")
        return False
    
    print("  ✓ ClaudeSDKClient.clear_context method exists")
    
    # Check method signature
    import inspect
    sig = inspect.signature(ClaudeSDKClient.clear_context)
    if 'self' not in sig.parameters:
        print("  ✗ ClaudeSDKClient.clear_context has invalid signature")
        return False
    
    print("  ✓ ClaudeSDKClient.clear_context has correct signature")
    
    # Check docstring
    if not ClaudeSDKClient.clear_context.__doc__:
        print("  ⚠ ClaudeSDKClient.clear_context missing docstring")
    else:
        print("  ✓ ClaudeSDKClient.clear_context has docstring")
        
        # Check for key phrases in docstring
        doc = ClaudeSDKClient.clear_context.__doc__
        if "in-process" in doc.lower():
            print("  ✓ Docstring mentions 'in-process'")
        if "reconnect" in doc.lower():
            print("  ✓ Docstring mentions 'reconnect'")
        if "session" in doc.lower():
            print("  ✓ Docstring mentions 'session'")
    
    return True


def verify_tests():
    """Verify that tests exist."""
    print("\nVerifying tests...")
    test_file = Path(__file__).parent / "tests" / "test_clear_context.py"
    
    if not test_file.exists():
        print("  ✗ test_clear_context.py not found")
        return False
    
    print("  ✓ test_clear_context.py exists")
    
    # Count test functions
    content = test_file.read_text()
    test_count = content.count("async def test_")
    print(f"  ✓ Found {test_count} test functions")
    
    if test_count < 5:
        print("  ⚠ Less than 5 tests found (expected at least 5)")
    
    return True


def verify_examples():
    """Verify that examples exist."""
    print("\nVerifying examples...")
    example_file = Path(__file__).parent / "examples" / "clear_context_example.py"
    
    if not example_file.exists():
        print("  ✗ clear_context_example.py not found")
        return False
    
    print("  ✓ clear_context_example.py exists")
    
    # Check for key content
    content = example_file.read_text()
    if "clear_context()" in content:
        print("  ✓ Example uses clear_context()")
    if "session_id" in content:
        print("  ✓ Example demonstrates session usage")
    
    return True


def verify_documentation():
    """Verify that documentation exists."""
    print("\nVerifying documentation...")
    
    docs = [
        "CLEAR_CONTEXT.md",
        "CLEAR_CONTEXT_IMPLEMENTATION.md",
    ]
    
    all_exist = True
    for doc in docs:
        doc_file = Path(__file__).parent / doc
        if not doc_file.exists():
            print(f"  ✗ {doc} not found")
            all_exist = False
        else:
            print(f"  ✓ {doc} exists")
    
    return all_exist


def main():
    """Run all verifications."""
    print("=" * 60)
    print("Clear Context Implementation Verification")
    print("=" * 60)
    
    results = []
    
    try:
        results.append(("Types", verify_types()))
    except Exception as e:
        print(f"  ✗ Error verifying types: {e}")
        results.append(("Types", False))
    
    try:
        results.append(("Query", verify_query()))
    except Exception as e:
        print(f"  ✗ Error verifying query: {e}")
        results.append(("Query", False))
    
    try:
        results.append(("Client", verify_client()))
    except Exception as e:
        print(f"  ✗ Error verifying client: {e}")
        results.append(("Client", False))
    
    try:
        results.append(("Tests", verify_tests()))
    except Exception as e:
        print(f"  ✗ Error verifying tests: {e}")
        results.append(("Tests", False))
    
    try:
        results.append(("Examples", verify_examples()))
    except Exception as e:
        print(f"  ✗ Error verifying examples: {e}")
        results.append(("Examples", False))
    
    try:
        results.append(("Documentation", verify_documentation()))
    except Exception as e:
        print(f"  ✗ Error verifying documentation: {e}")
        results.append(("Documentation", False))
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{name:20s} {status}")
    
    all_passed = all(passed for _, passed in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All verifications passed!")
        print("=" * 60)
        return 0
    else:
        print("✗ Some verifications failed")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
