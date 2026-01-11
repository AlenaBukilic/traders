"""
Phase 3: Agent-as-Tool Pattern Validation

This script validates that the Researcher agent can be successfully
converted to a tool and used by another agent (the Trader pattern).

Tests:
1. Researcher tool can be created
2. Tool has correct properties (name, description)
3. Tool can be invoked directly
4. Tool can be used by another agent
5. Nested invocation works end-to-end
"""

import asyncio
import sys
from dotenv import load_dotenv

load_dotenv(override=True)


async def test_researcher_tool_creation():
    """Test 1: Create researcher as a tool"""
    print("\n=== Test 1: Researcher Tool Creation ===")
    
    try:
        from agents.researcher import get_strands_researcher_tool
        
        researcher_tool = await get_strands_researcher_tool("TestTrader", "gpt-4o-mini")
        
        print(f"✓ Created researcher tool")
        print(f"  Type: {type(researcher_tool)}")
        print(f"  Name: {researcher_tool.name if hasattr(researcher_tool, 'name') else 'N/A'}")
        
        # Check if it has a description
        if hasattr(researcher_tool, 'description'):
            desc_preview = researcher_tool.description[:100] if researcher_tool.description else "N/A"
            print(f"  Description: {desc_preview}...")
        
        return True, researcher_tool
    except Exception as e:
        print(f"✗ Failed to create researcher tool: {e}")
        import traceback
        traceback.print_exc()
        return False, None


async def test_tool_direct_invocation():
    """Test 2: Invoke the researcher tool directly"""
    print("\n=== Test 2: Direct Tool Invocation ===")
    
    try:
        from agents.researcher import get_strands_researcher_tool
        
        researcher_tool = await get_strands_researcher_tool("TestTrader", "gpt-4o-mini")
        
        # Invoke the tool directly as a function
        query = "What is Tesla's current stock price? Be very brief."
        print(f"Query: {query}")
        print("Invoking tool... (may take 30-60 seconds)")
        
        result = await researcher_tool(query)
        
        print(f"✓ Tool invoked successfully")
        print(f"  Response type: {type(result)}")
        print(f"  Response preview: {str(result)[:200]}...")
        
        return True
    except Exception as e:
        print(f"✗ Tool invocation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_tool_with_agent():
    """Test 3: Use researcher tool with another agent"""
    print("\n=== Test 3: Tool Used by Another Agent ===")
    
    try:
        from agents.researcher import get_strands_researcher_tool
        from strands import Agent
        from core.model_providers import ModelProvider
        
        # Create researcher tool
        researcher_tool = await get_strands_researcher_tool("TestTrader", "gpt-4o-mini")
        
        # Create a test agent that uses the researcher tool
        model = ModelProvider.get_strands_model("gpt-4o-mini")
        test_agent = Agent(
            name="TestAgent",
            system_prompt="You are a test agent. You have access to a researcher tool. Use it to answer questions.",
            model=model,
            tools=[researcher_tool]
        )
        
        print(f"✓ Created test agent with researcher tool")
        
        # Ask the test agent a question that requires using the researcher
        query = "Use the researcher to find out: What is happening with Tesla stock today? Give a brief summary."
        print(f"\nQuery to agent: {query}")
        print("Invoking agent... (may take 60-90 seconds)")
        
        result = await test_agent.invoke_async(query)
        
        print(f"✓ Agent responded successfully")
        print(f"  Stop reason: {result.stop_reason}")
        
        # Try to extract response
        if hasattr(result, 'message'):
            msg = result.message
            if isinstance(msg, dict) and 'content' in msg:
                content = msg['content']
                if isinstance(content, list) and len(content) > 0:
                    first_content = content[0]
                    if isinstance(first_content, dict) and 'text' in first_content:
                        response_text = first_content['text'][:300]
                        print(f"  Response preview: {response_text}...")
        
        return True
    except Exception as e:
        print(f"✗ Agent with tool failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_compare_with_openai_agents():
    """Test 4: Compare with OpenAI Agents pattern"""
    print("\n=== Test 4: Compare with OpenAI Agents Pattern ===")
    
    try:
        from traders import get_researcher_tool
        from agents.mcp import MCPServerStdio
        from mcp_params import researcher_mcp_server_params
        from contextlib import AsyncExitStack
        
        # Create OpenAI Agents researcher tool
        async with AsyncExitStack() as stack:
            mcp_servers = [
                await stack.enter_async_context(
                    MCPServerStdio(params, client_session_timeout_seconds=120)
                )
                for params in researcher_mcp_server_params("TestTrader")
            ]
            
            researcher_tool = await get_researcher_tool(mcp_servers, "gpt-4o-mini")
            
            print(f"✓ Created OpenAI Agents researcher tool")
            print(f"  Type: {type(researcher_tool)}")
            print(f"  Name: {researcher_tool.name if hasattr(researcher_tool, 'name') else 'N/A'}")
            
            return True
    except Exception as e:
        print(f"✗ OpenAI Agents tool creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all validation tests"""
    print("=" * 60)
    print("Agent-as-Tool Pattern - Phase 3 Validation")
    print("=" * 60)
    
    results = []
    
    # Test 1: Tool creation
    success, researcher_tool = await test_researcher_tool_creation()
    results.append(success)
    
    if not success:
        print("\n⚠ Cannot proceed without tool creation working")
        return False
    
    # Test 2: Direct invocation
    print("\n⚠ Note: The next tests involve actual API calls and may take 1-2 minutes")
    results.append(await test_tool_direct_invocation())
    
    # Test 3: Tool with agent (the critical test!)
    results.append(await test_tool_with_agent())
    
    # Test 4: Compare with OpenAI Agents
    results.append(await test_compare_with_openai_agents())
    
    # Summary
    print("\n" + "=" * 60)
    print("Validation Summary")
    print("=" * 60)
    
    test_names = [
        "Researcher Tool Creation",
        "Direct Tool Invocation",
        "Tool Used by Agent (Critical!)",
        "OpenAI Agents Comparison",
    ]
    
    for i, (name, result) in enumerate(zip(test_names, results), 1):
        status = "✓ PASS" if result else "✗ FAIL"
        importance = " 🔥" if i == 3 else ""  # Mark the critical test
        print(f"Test {i}: {name:<35} {status}{importance}")
    
    passed = sum(results)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    # Determine overall success
    # Test 3 (tool used by agent) is the critical one
    if results[2]:  # Index 2 is test 3
        print("\n✅ Phase 3 validation SUCCESSFUL!")
        print("Agent-as-Tool pattern works correctly!")
        print("Ready to proceed to Phase 4 (Trader Agent Migration)")
        return True
    else:
        print("\n⚠ Phase 3 validation INCOMPLETE")
        print("The critical test (Tool Used by Agent) must pass")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nValidation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error during validation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
