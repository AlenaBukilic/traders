"""
Model Provider Abstraction Layer

This module provides a unified interface for creating model instances
that work with both OpenAI Agents SDK and Strands Agents SDK.

Usage:
    from model_providers import ModelProvider
    
    # Get Strands model
    model = ModelProvider.get_strands_model("gpt-4o-mini")
    
    # Get OpenAI Agents model (legacy)
    model = ModelProvider.get_openai_agents_model("gpt-4o-mini")
"""

from typing import Any
import os
from dotenv import load_dotenv

load_dotenv(override=True)


class ModelProvider:
    """Abstraction layer for model providers supporting both SDKs"""
    
    # Model provider configuration
    DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
    GROK_BASE_URL = "https://api.x.ai/v1"
    GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
    
    @staticmethod
    def get_strands_model(model_name: str) -> Any:
        """
        Get Strands-compatible model instance.
        
        Args:
            model_name: Model identifier (e.g., "gpt-4o-mini", "deepseek-chat")
            
        Returns:
            Strands Model instance
            
        Note:
            Uses the actual Strands API discovered in Phase 0:
            - Import from strands.models.openai (not strands.models)
            - Use model_id parameter (not model)
            - Use client_args for API configuration
        """
        from strands.models.openai import OpenAIModel
        
        # Determine provider based on model name
        if "/" in model_name:
            # OpenRouter format (e.g., "anthropic/claude-3.5-sonnet")
            api_key = os.getenv("OPENROUTER_API_KEY")
            base_url = ModelProvider.OPENROUTER_BASE_URL
        elif "deepseek" in model_name:
            api_key = os.getenv("DEEPSEEK_API_KEY")
            base_url = ModelProvider.DEEPSEEK_BASE_URL
        elif "grok" in model_name:
            api_key = os.getenv("GROK_API_KEY")
            base_url = ModelProvider.GROK_BASE_URL
        elif "gemini" in model_name:
            api_key = os.getenv("GOOGLE_API_KEY")
            base_url = ModelProvider.GEMINI_BASE_URL
        else:
            # Default to OpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            base_url = None  # Use default OpenAI base URL
        
        # Create client args
        client_args = {"api_key": api_key}
        if base_url:
            client_args["base_url"] = base_url
        
        # Create and return Strands model
        return OpenAIModel(
            model_id=model_name,
            client_args=client_args
        )
    
    @staticmethod
    def get_strands_model_with_litellm(model_name: str) -> Any:
        """
        Get Strands model using LiteLLM for unified multi-provider support.
        
        This is an alternative approach that uses LiteLLM to handle all providers.
        Requires: uv pip install litellm
        
        Args:
            model_name: Model identifier
            
        Returns:
            Strands LiteLLMModel instance
            
        Raises:
            ImportError: If litellm is not installed
        """
        try:
            from strands.models.litellm import LiteLLMModel
        except ImportError:
            raise ImportError(
                "LiteLLM not available. Install with: uv pip install litellm"
            )
        
        # Determine API key based on model name
        if "/" in model_name:
            api_key = os.getenv("OPENROUTER_API_KEY")
            base_url = ModelProvider.OPENROUTER_BASE_URL
        elif "deepseek" in model_name:
            api_key = os.getenv("DEEPSEEK_API_KEY")
            base_url = ModelProvider.DEEPSEEK_BASE_URL
        elif "grok" in model_name:
            api_key = os.getenv("GROK_API_KEY")
            base_url = ModelProvider.GROK_BASE_URL
        elif "gemini" in model_name:
            api_key = os.getenv("GOOGLE_API_KEY")
            base_url = ModelProvider.GEMINI_BASE_URL
        else:
            api_key = os.getenv("OPENAI_API_KEY")
            base_url = None
        
        # Create LiteLLM model
        return LiteLLMModel(
            model_id=model_name,
            client_args={
                "api_key": api_key,
                "base_url": base_url
            } if base_url else {"api_key": api_key}
        )
    
    @staticmethod
    def get_openai_agents_model(model_name: str) -> Any:
        """
        Get OpenAI Agents SDK model instance (legacy implementation).
        
        This preserves the existing logic from traders.py for backward compatibility.
        
        Args:
            model_name: Model identifier
            
        Returns:
            OpenAI Agents Model instance (typically OpenAIChatCompletionsModel)
        """
        from agents import OpenAIChatCompletionsModel
        from openai import AsyncOpenAI
        
        # Create appropriate client based on model name
        if "/" in model_name:
            # OpenRouter
            client = AsyncOpenAI(
                base_url=ModelProvider.OPENROUTER_BASE_URL,
                api_key=os.getenv("OPENROUTER_API_KEY")
            )
        elif "deepseek" in model_name:
            client = AsyncOpenAI(
                base_url=ModelProvider.DEEPSEEK_BASE_URL,
                api_key=os.getenv("DEEPSEEK_API_KEY")
            )
        elif "grok" in model_name:
            client = AsyncOpenAI(
                base_url=ModelProvider.GROK_BASE_URL,
                api_key=os.getenv("GROK_API_KEY")
            )
        elif "gemini" in model_name:
            client = AsyncOpenAI(
                base_url=ModelProvider.GEMINI_BASE_URL,
                api_key=os.getenv("GOOGLE_API_KEY")
            )
        else:
            # Return model name for default OpenAI (let agents SDK handle it)
            return model_name
        
        return OpenAIChatCompletionsModel(
            model=model_name,
            openai_client=client
        )


# Convenience functions for common use cases
def create_strands_model(model_name: str, use_litellm: bool = False) -> Any:
    """
    Convenience function to create a Strands model.
    
    Args:
        model_name: Model identifier
        use_litellm: If True, use LiteLLM (requires installation)
        
    Returns:
        Strands Model instance
    """
    if use_litellm:
        return ModelProvider.get_strands_model_with_litellm(model_name)
    return ModelProvider.get_strands_model(model_name)


def create_openai_agents_model(model_name: str) -> Any:
    """
    Convenience function to create an OpenAI Agents SDK model.
    
    Args:
        model_name: Model identifier
        
    Returns:
        OpenAI Agents Model instance
    """
    return ModelProvider.get_openai_agents_model(model_name)


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_providers():
        """Test model provider creation"""
        print("Testing Model Providers\n")
        
        # Test Strands models
        print("=== Strands Models ===")
        models_to_test = [
            "gpt-4o-mini",
            "deepseek-chat",
            "grok-3-mini-beta",
            "gemini-2.5-flash-preview-04-17"
        ]
        
        for model_name in models_to_test:
            try:
                model = ModelProvider.get_strands_model(model_name)
                print(f"✓ Created Strands model: {model_name}")
            except Exception as e:
                print(f"✗ Failed to create {model_name}: {e}")
        
        # Test OpenAI Agents models
        print("\n=== OpenAI Agents Models ===")
        for model_name in models_to_test:
            try:
                model = ModelProvider.get_openai_agents_model(model_name)
                print(f"✓ Created OpenAI Agents model: {model_name}")
            except Exception as e:
                print(f"✗ Failed to create {model_name}: {e}")
    
    asyncio.run(test_providers())
