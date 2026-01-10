"""
Phase 0: Strands Agents SDK Validation Script

This script validates that:
1. Strands SDK is properly installed
2. Basic agent creation works
3. MCP server compatibility
4. Simple agent invocation succeeds
"""

import asyncio
import sys
from dotenv import load_dotenv
import os

load_dotenv(override=True)


async def test_strands_import():
    """Test 1: Verify Strands SDK can be imported"""
    print("\n=== Test 1: Import Strands SDK ===")
    try:
        from strands import Agent
        from strands.models.openai import OpenAIModel
        print("✓ Successfully imported strands.Agent")
        print("✓ Successfully imported strands.models.openai.OpenAIModel")
        return True
    except ImportError as e:
        print(f"✗ Failed to import Strands SDK: {e}")
        print("\nPlease install Strands SDK:")
        print("  pip install strands-agents")
        return False


async def test_basic_agent_creation():
    """Test 2: Create a basic Strands agent"""
    print("\n=== Test 2: Create Basic Agent ===")
    try:
        from strands import Agent
        from strands.models.openai import OpenAIModel
        
        # Check if OpenAI API key is available
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("⚠ OPENAI_API_KEY not found in environment")
            print("  This is okay for import testing, but agent invocation will fail")
            print("  Creating agent anyway (will use default client)...")
        
        # Create model with Strands API
        model = OpenAIModel(
            model_id="gpt-4o-mini",
            client_args={"api_key": api_key} if api_key else None
        )
        
        # Create agent with Strands API
        agent = Agent(
            name="TestAgent",
            system_prompt="You are a helpful test agent.",
            model=model,
        )
        
        print(f"✓ Successfully created agent: {agent.name}")
        print(f"  Model: gpt-4o-mini")
        return True, agent
    except Exception as e:
        print(f"✗ Failed to create agent: {e}")
        import traceback
        traceback.print_exc()
        return False, None


async def test_agent_invocation(agent):
    """Test 3: Test simple agent invocation"""
    print("\n=== Test 3: Agent Invocation ===")
    
    if agent is None:
        print("⚠ Skipping invocation test (no agent created)")
        return False
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠ Skipping invocation test (no OPENAI_API_KEY)")
        return False
    
    try:
        print("Invoking agent with test message...")
        result = await agent.invoke_async("Say 'Hello from Strands!' and nothing else.")
        
        print(f"✓ Agent responded successfully")
        # Check what's in result
        if hasattr(result, 'messages') and result.messages:
            last_msg = result.messages[-1]
            if hasattr(last_msg, 'content'):
                print(f"  Response: {last_msg.content}")
            else:
                print(f"  Response: {last_msg}")
        else:
            print(f"  Response: {result}")
        return True
    except Exception as e:
        print(f"✗ Failed to invoke agent: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_mcp_import():
    """Test 4: Verify MCP integration can be imported"""
    print("\n=== Test 4: MCP Integration ===")
    try:
        from strands.tools.mcp import MCPClient
        print("✓ Successfully imported strands.tools.mcp.MCPClient")
        return True
    except ImportError:
        try:
            # Try alternative import path
            from strands.mcp import MCPServerStdio
            print("✓ Successfully imported strands.mcp.MCPServerStdio")
            return True
        except ImportError as e:
            print(f"✗ Failed to import MCP modules: {e}")
            print("  This might be okay - will verify during Phase 2")
            return False


async def test_model_providers():
    """Test 5: Check if LiteLLM is available for multi-provider support"""
    print("\n=== Test 5: Model Providers ===")
    try:
        from strands.models.litellm import LiteLLMModel
        print("✓ LiteLLMModel available for multi-provider support")
        return True
    except ImportError:
        print("⚠ LiteLLMModel not found (litellm package not installed)")
        print("  Will need to use provider-specific models or install litellm:")
        print("  uv pip install litellm")
        return False


async def main():
    """Run all validation tests"""
    print("=" * 60)
    print("Strands Agents SDK - Phase 0 Validation")
    print("=" * 60)
    
    results = []
    
    # Test 1: Import
    results.append(await test_strands_import())
    if not results[-1]:
        print("\n❌ Cannot proceed without Strands SDK installed")
        return False
    
    # Test 2: Agent creation
    success, agent = await test_basic_agent_creation()
    results.append(success)
    
    # Test 3: Agent invocation (only if agent created successfully)
    if success:
        results.append(await test_agent_invocation(agent))
    else:
        print("\n⚠ Skipping invocation test (agent creation failed)")
        results.append(False)
    
    # Test 4: MCP imports
    results.append(await test_mcp_import())
    
    # Test 5: Model providers
    results.append(await test_model_providers())
    
    # Summary
    print("\n" + "=" * 60)
    print("Validation Summary")
    print("=" * 60)
    
    test_names = [
        "Strands SDK Import",
        "Basic Agent Creation",
        "Agent Invocation",
        "MCP Integration",
        "Model Providers"
    ]
    
    for i, (name, result) in enumerate(zip(test_names, results), 1):
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"Test {i}: {name:<25} {status}")
    
    passed = sum(results)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    # Determine overall success
    # For Phase 0, we need at least tests 1, 2, and 4 to pass
    critical_tests = [results[0], results[1], results[3]]  # Import, Creation, MCP
    
    if all(critical_tests):
        print("\n✅ Phase 0 validation SUCCESSFUL!")
        print("Ready to proceed to Phase 1 (Model Provider Abstraction)")
        return True
    else:
        print("\n⚠ Phase 0 validation INCOMPLETE")
        print("Please address the failed tests before proceeding")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nValidation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error during validation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
