"""
Phase 1: Model Provider Validation Script

This script validates that:
1. Model provider abstraction works correctly
2. Both Strands and OpenAI Agents models can be created
3. Models work with actual agent creation
4. All configured model types are accessible
"""

import asyncio
import sys
from dotenv import load_dotenv
import os

load_dotenv(override=True)


async def test_strands_model_creation():
    """Test 1: Create Strands models for different providers"""
    print("\n=== Test 1: Strands Model Creation ===")
    
    from core.model_providers import ModelProvider
    
    # Models to test (based on what's configured in traders.py)
    test_cases = [
        ("gpt-4o-mini", "OpenAI"),
        ("deepseek-chat", "DeepSeek"),
        ("gemini-2.5-flash-preview-04-17", "Gemini"),
        ("grok-3-mini-beta", "Grok"),
    ]
    
    results = []
    for model_name, provider in test_cases:
        try:
            model = ModelProvider.get_strands_model(model_name)
            print(f"✓ {provider}: Created model for {model_name}")
            results.append(True)
        except Exception as e:
            print(f"✗ {provider}: Failed to create {model_name}: {e}")
            results.append(False)
    
    return all(results)


async def test_openai_agents_model_creation():
    """Test 2: Create OpenAI Agents SDK models for different providers"""
    print("\n=== Test 2: OpenAI Agents Model Creation ===")
    
    from core.model_providers import ModelProvider
    
    test_cases = [
        ("gpt-4o-mini", "OpenAI"),
        ("deepseek-chat", "DeepSeek"),
        ("gemini-2.5-flash-preview-04-17", "Gemini"),
        ("grok-3-mini-beta", "Grok"),
    ]
    
    results = []
    for model_name, provider in test_cases:
        try:
            model = ModelProvider.get_openai_agents_model(model_name)
            print(f"✓ {provider}: Created model for {model_name}")
            results.append(True)
        except Exception as e:
            print(f"✗ {provider}: Failed to create {model_name}: {e}")
            results.append(False)
    
    return all(results)


async def test_strands_agent_with_model():
    """Test 3: Create Strands agent using model provider"""
    print("\n=== Test 3: Strands Agent with Model Provider ===")
    
    try:
        from core.model_providers import ModelProvider
        from strands import Agent
        
        # Test with gpt-4o-mini since we know OpenAI key is available
        model = ModelProvider.get_strands_model("gpt-4o-mini")
        
        agent = Agent(
            name="TestTrader",
            system_prompt="You are a test trading agent.",
            model=model
        )
        
        print(f"✓ Created Strands agent with model provider")
        print(f"  Agent name: {agent.name}")
        
        # Optional: Test invocation if API key is available
        if os.getenv("OPENAI_API_KEY"):
            print("  Testing agent invocation...")
            result = await agent.invoke_async("Say 'Model provider works!' and nothing else.")
            # Just verify it works, don't try to parse complex response structure
            print(f"  ✓ Agent invoked successfully (response received)")
        
        return True
    except Exception as e:
        print(f"✗ Failed to create agent: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_openai_agents_agent_with_model():
    """Test 4: Create OpenAI Agents SDK agent using model provider"""
    print("\n=== Test 4: OpenAI Agents Agent with Model Provider ===")
    
    try:
        from core.model_providers import ModelProvider
        from agents import Agent
        
        # Test with gpt-4o-mini
        model = ModelProvider.get_openai_agents_model("gpt-4o-mini")
        
        agent = Agent(
            name="TestTrader",
            instructions="You are a test trading agent.",
            model=model
        )
        
        print(f"✓ Created OpenAI Agents agent with model provider")
        print(f"  Agent name: {agent.name}")
        
        return True
    except Exception as e:
        print(f"✗ Failed to create OpenAI Agents agent: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_model_switching():
    """Test 5: Test switching between different model providers"""
    print("\n=== Test 5: Model Switching ===")
    
    from core.model_providers import ModelProvider
    
    # Test creating multiple different models in sequence
    model_sequence = [
        "gpt-4o-mini",
        "deepseek-chat",
        "gpt-4o-mini"  # Switch back
    ]
    
    try:
        for model_name in model_sequence:
            model = ModelProvider.get_strands_model(model_name)
            print(f"✓ Switched to {model_name}")
        
        print(f"✓ Model switching works correctly")
        return True
    except Exception as e:
        print(f"✗ Model switching failed: {e}")
        return False


async def test_litellm_availability():
    """Test 6: Check if LiteLLM is available (optional)"""
    print("\n=== Test 6: LiteLLM Availability (Optional) ===")
    
    try:
        from core.model_providers import ModelProvider
        model = ModelProvider.get_strands_model_with_litellm("gpt-4o-mini")
        print("✓ LiteLLM is available and working")
        return True
    except ImportError:
        print("⚠ LiteLLM not installed (optional)")
        print("  Install with: uv pip install litellm")
        return False
    except Exception as e:
        print(f"✗ LiteLLM error: {e}")
        return False


async def main():
    """Run all validation tests"""
    print("=" * 60)
    print("Model Provider Abstraction - Phase 1 Validation")
    print("=" * 60)
    
    results = []
    
    # Test 1: Strands model creation
    results.append(await test_strands_model_creation())
    
    # Test 2: OpenAI Agents model creation
    results.append(await test_openai_agents_model_creation())
    
    # Test 3: Strands agent with model provider
    results.append(await test_strands_agent_with_model())
    
    # Test 4: OpenAI Agents agent with model provider
    results.append(await test_openai_agents_agent_with_model())
    
    # Test 5: Model switching
    results.append(await test_model_switching())
    
    # Test 6: LiteLLM (optional)
    litellm_result = await test_litellm_availability()
    # Don't count LiteLLM in critical results
    
    # Summary
    print("\n" + "=" * 60)
    print("Validation Summary")
    print("=" * 60)
    
    test_names = [
        "Strands Model Creation",
        "OpenAI Agents Model Creation",
        "Strands Agent Integration",
        "OpenAI Agents Integration",
        "Model Switching",
    ]
    
    for i, (name, result) in enumerate(zip(test_names, results), 1):
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"Test {i}: {name:<30} {status}")
    
    # LiteLLM (optional)
    litellm_status = "✓ AVAILABLE" if litellm_result else "⚠ NOT INSTALLED"
    print(f"Test 6: LiteLLM (Optional)            {litellm_status}")
    
    passed = sum(results)
    total = len(results)
    print(f"\nTotal: {passed}/{total} critical tests passed")
    
    # Determine overall success
    if all(results):
        print("\n✅ Phase 1 validation SUCCESSFUL!")
        print("Ready to proceed to Phase 2 (Researcher Agent Migration)")
        return True
    else:
        print("\n⚠ Phase 1 validation INCOMPLETE")
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
