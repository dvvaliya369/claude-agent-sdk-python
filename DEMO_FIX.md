# Session Isolation Fix - Demonstration

## The Problem (Before Fix)

When using a single `ClaudeSDKClient` with different `session_id` values, conversation context was shared:

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

async with ClaudeSDKClient(options=options) as client:
    # Session A: User stores a secret
    await client.query(
        "Remember this secret password: MY_SECRET_123",
        session_id="session_A"
    )
    async for msg in client.receive_response(session_id="session_A"):
        # Claude responds: "I'll remember that password."
        pass
    
    # Session B: Different user tries to access the secret
    await client.query(
        "What password did I tell you?",
        session_id="session_B"
    )
    async for msg in client.receive_response(session_id="session_B"):
        # ❌ SECURITY ISSUE: Claude responds with "MY_SECRET_123"
        # Session B can see Session A's secret!
        pass
```

**Why this happened:**
- Single CLI subprocess maintained one conversation context
- `session_id` only filtered messages, didn't isolate context
- All messages went to the same conversation history

## The Solution (After Fix)

The fix prevents this by enforcing one session per client instance:

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

async with ClaudeSDKClient(options=options) as client:
    # Session A: User stores a secret
    await client.query(
        "Remember this secret password: MY_SECRET_123",
        session_id="session_A"
    )
    async for msg in client.receive_response(session_id="session_A"):
        pass
    
    # Session B: Attempting to use different session
    try:
        await client.query(
            "What password did I tell you?",
            session_id="session_B"
        )
    except ValueError as e:
        # ✅ SECURITY FIX: Raises clear error
        print(e)
        # "Session isolation error: This ClaudeSDKClient instance is already 
        #  handling session(s) {'session_A'}. Cannot switch to session 'session_B'.
        #  To use multiple sessions, create separate ClaudeSDKClient instances 
        #  for each session. This prevents conversation context from being 
        #  shared across different sessions."
```

## Correct Usage Patterns

### Pattern 1: Single Session (Most Common)

```python
async with ClaudeSDKClient(options=options) as client:
    # All queries use the same session - works perfectly
    await client.query("First question", session_id="my_session")
    async for msg in client.receive_response(session_id="my_session"):
        pass
    
    await client.query("Follow-up question", session_id="my_session")
    async for msg in client.receive_response(session_id="my_session"):
        pass
```

### Pattern 2: Multiple Isolated Sessions

```python
# Create separate clients for true isolation
async with ClaudeSDKClient(options=options) as client_a:
    async with ClaudeSDKClient(options=options) as client_b:
        # Session A - completely isolated
        await client_a.query(
            "Secret: PASSWORD_A",
            session_id="session_A"
        )
        
        # Session B - completely isolated
        await client_b.query(
            "Secret: PASSWORD_B",
            session_id="session_B"
        )
        
        # Process responses independently
        async for msg in client_a.receive_response(session_id="session_A"):
            # Only sees Session A's context
            pass
        
        async for msg in client_b.receive_response(session_id="session_B"):
            # Only sees Session B's context
            pass
```

### Pattern 3: Sequential Sessions

```python
async with ClaudeSDKClient(options=options) as client:
    # First session
    await client.query("Question 1", session_id="session_1")
    async for msg in client.receive_response(session_id="session_1"):
        pass
    
    # Disconnect to clear session
    await client.disconnect()
    await client.connect()
    
    # New session - previous context is gone
    await client.query("Question 2", session_id="session_2")
    async for msg in client.receive_response(session_id="session_2"):
        pass
```

## Error Messages

The fix provides clear, actionable error messages:

```python
ValueError: Session isolation error: This ClaudeSDKClient instance is already 
handling session(s) {'session_A'}. Cannot switch to session 'session_B'. 
To use multiple sessions, create separate ClaudeSDKClient instances for each 
session. This prevents conversation context from being shared across different 
sessions.
```

**What the error tells you:**
1. **What went wrong**: Trying to use a different session
2. **Current state**: Which session(s) are active
3. **How to fix**: Create separate client instances
4. **Why it matters**: Prevents context sharing (security)

## Security Benefits

### Before Fix
- ❌ Session B could read Session A's secrets
- ❌ Conversation context leaked between sessions
- ❌ No warning or error when mixing sessions
- ❌ Silent security vulnerability

### After Fix
- ✅ Sessions are strictly isolated
- ✅ Attempting to mix sessions raises clear error
- ✅ Error message explains how to fix
- ✅ Prevents accidental context leakage

## Migration Examples

### Example 1: Chat Application

**Before:**
```python
# ❌ Insecure: All users share context
client = ClaudeSDKClient()

async def handle_user_message(user_id, message):
    await client.query(message, session_id=user_id)
    async for msg in client.receive_response(session_id=user_id):
        return msg
```

**After:**
```python
# ✅ Secure: Each user gets isolated client
user_clients = {}

async def handle_user_message(user_id, message):
    if user_id not in user_clients:
        user_clients[user_id] = ClaudeSDKClient()
        await user_clients[user_id].connect()
    
    client = user_clients[user_id]
    await client.query(message, session_id=user_id)
    async for msg in client.receive_response(session_id=user_id):
        return msg
```

### Example 2: Testing Multiple Scenarios

**Before:**
```python
# ❌ Tests would interfere with each other
async def test_scenarios():
    client = ClaudeSDKClient()
    
    # Test scenario A
    await client.query("Test A", session_id="scenario_a")
    
    # Test scenario B - would see scenario A's context!
    await client.query("Test B", session_id="scenario_b")
```

**After:**
```python
# ✅ Each scenario is isolated
async def test_scenarios():
    # Scenario A
    async with ClaudeSDKClient() as client_a:
        await client_a.query("Test A", session_id="scenario_a")
        async for msg in client_a.receive_response(session_id="scenario_a"):
            pass
    
    # Scenario B - completely independent
    async with ClaudeSDKClient() as client_b:
        await client_b.query("Test B", session_id="scenario_b")
        async for msg in client_b.receive_response(session_id="scenario_b"):
            pass
```

## Summary

The session isolation fix:

1. **Prevents Security Vulnerability**: Stops context leakage between sessions
2. **Provides Clear Errors**: Helpful messages guide users to correct usage
3. **Enforces Best Practices**: One session per client instance
4. **Easy Migration**: Simple pattern changes for affected code

**Bottom Line**: This fix ensures that when you use different `session_id` values, you're actually getting isolated conversations, not just filtered message streams from a shared context.
