# Session Isolation Security Fix

## Problem

When using a single `ClaudeSDKClient` instance and sending requests with different `session_id` values, conversation context was being shared across sessions. This meant that:

- Session B could read secrets or information from Session A
- All sessions shared the same conversation history
- There was no isolation between different logical conversations

### Example of the Issue

```python
async with ClaudeSDKClient(options=options) as client:
    # Session A: Store a secret
    await client.query("Remember this secret: MY_PASSWORD_123", session_id="session_A")
    async for msg in client.receive_response(session_id="session_A"):
        pass  # Process response
    
    # Session B: Could access Session A's secret!
    await client.query("What secret did I tell you?", session_id="session_B")
    async for msg in client.receive_response(session_id="session_B"):
        # This would reveal MY_PASSWORD_123 from session_A
        pass
```

## Root Cause

The issue occurred because:

1. A single `ClaudeSDKClient` instance maintains one subprocess (CLI process)
2. The CLI subprocess maintains a single conversation context
3. While `session_id` was sent with each message, it was only used for filtering responses on the client side
4. The underlying CLI did not isolate conversation contexts per `session_id`

## Solution

The fix implements session isolation at the SDK level by:

1. **Tracking Active Sessions**: Each `ClaudeSDKClient` instance now tracks which `session_id` it's handling via `_active_sessions` set
2. **Validation**: When `query()` is called, it validates that the `session_id` matches the active session
3. **Error on Mismatch**: If a different `session_id` is used, a `ValueError` is raised with a clear error message
4. **Session Cleanup**: When `disconnect()` is called, active sessions are cleared

### Code Changes

#### 1. Added Session Tracking in `__init__`

```python
def __init__(self, options: ClaudeAgentOptions | None = None, transport: Transport | None = None):
    # ... existing code ...
    self._active_sessions: set[str] = set()  # Track active session IDs
```

#### 2. Added Validation in `query()`

```python
async def query(self, prompt: str | AsyncIterable[dict[str, Any]], session_id: str = "default") -> None:
    # Validate session isolation: only one session per client instance
    if self._active_sessions and session_id not in self._active_sessions:
        raise ValueError(
            f"Session isolation error: This ClaudeSDKClient instance is already "
            f"handling session(s) {self._active_sessions}. Cannot switch to session '{session_id}'. "
            f"To use multiple sessions, create separate ClaudeSDKClient instances for each session. "
            f"This prevents conversation context from being shared across different sessions."
        )
    
    # Track this session as active
    self._active_sessions.add(session_id)
    # ... rest of the method ...
```

#### 3. Added Cleanup in `disconnect()`

```python
async def disconnect(self) -> None:
    # ... existing code ...
    self._active_sessions.clear()
```

## Usage

### ✅ Correct: Single Session Per Client

```python
async with ClaudeSDKClient(options=options) as client:
    await client.query("First message", session_id="session_A")
    async for msg in client.receive_response(session_id="session_A"):
        pass
    
    await client.query("Second message", session_id="session_A")
    async for msg in client.receive_response(session_id="session_A"):
        pass
```

### ✅ Correct: Multiple Clients for Multiple Sessions

```python
# Create separate clients for different sessions
async with ClaudeSDKClient(options=options) as client_a:
    async with ClaudeSDKClient(options=options) as client_b:
        # Session A
        await client_a.query("Message for A", session_id="session_A")
        
        # Session B (completely isolated)
        await client_b.query("Message for B", session_id="session_B")
        
        # Process responses independently
        async for msg in client_a.receive_response(session_id="session_A"):
            pass
        
        async for msg in client_b.receive_response(session_id="session_B"):
            pass
```

### ❌ Incorrect: Multiple Sessions on Same Client

```python
async with ClaudeSDKClient(options=options) as client:
    await client.query("Message", session_id="session_A")
    
    # This will raise ValueError!
    await client.query("Message", session_id="session_B")
    # ValueError: Session isolation error: This ClaudeSDKClient instance is already 
    # handling session(s) {'session_A'}. Cannot switch to session 'session_B'.
```

## Testing

Comprehensive tests have been added in `tests/test_session_isolation.py`:

1. `test_single_session_allowed` - Verifies single session usage works
2. `test_multiple_sessions_rejected` - Verifies multiple sessions are rejected
3. `test_session_cleared_on_disconnect` - Verifies cleanup on disconnect
4. `test_session_reuse_after_disconnect` - Verifies new session after disconnect
5. `test_error_message_clarity` - Verifies error messages are helpful
6. `test_not_connected_error_takes_precedence` - Verifies error priority

## Security Impact

This fix prevents:

- **Information Leakage**: Secrets or sensitive data from one session cannot be accessed by another
- **Context Confusion**: Each session maintains its own isolated conversation context
- **Accidental Mixing**: Clear error messages prevent developers from accidentally mixing sessions

## Migration Guide

If you were previously using multiple `session_id` values with a single client:

**Before:**
```python
async with ClaudeSDKClient(options=options) as client:
    await client.query("...", session_id="session_1")
    await client.query("...", session_id="session_2")  # This worked but was unsafe
```

**After:**
```python
# Option 1: Use separate clients
async with ClaudeSDKClient(options=options) as client1:
    async with ClaudeSDKClient(options=options) as client2:
        await client1.query("...", session_id="session_1")
        await client2.query("...", session_id="session_2")

# Option 2: Use sequential sessions with disconnect
async with ClaudeSDKClient(options=options) as client:
    await client.query("...", session_id="session_1")
    # ... process session_1 ...
    
    await client.disconnect()
    await client.connect()
    
    await client.query("...", session_id="session_2")
    # ... process session_2 ...
```

## Related Files

- `src/claude_agent_sdk/client.py` - Main implementation
- `tests/test_session_isolation.py` - Test suite
- `verify_fix_logic.py` - Verification script

## References

- Issue: Session context sharing between different session_id values
- Fix: Enforce one session per ClaudeSDKClient instance
- Security: Prevents information leakage across sessions
