"""
Test script to verify all providers work with configured API keys.
"""

import asyncio
from app.ai.providers.gemini_provider import GeminiProvider
from app.ai.providers.grok_provider import GrokProvider
from app.ai.providers.openai_provider import OpenAIProvider
from app.ai.providers.mock_provider import MockAIProvider

async def test_provider(provider_name, provider_class):
    """Test a single provider."""
    print("=" * 80)
    print(f"TESTING {provider_name.upper()} PROVIDER")
    print("=" * 80)
    
    try:
        provider = provider_class()
        print(f"✓ {provider_name} provider initialized")
        
        response = await provider.generate_completion(
            prompt="Who is the president of India?",
            system_prompt="You are a helpful assistant. Answer in one sentence."
        )
        print(f"Response: {response[:200]}...")
        print(f"✓ {provider_name} provider works!")
        return True
    except Exception as e:
        print(f"✗ {provider_name} provider failed: {type(e).__name__}: {e}")
        return False

async def main():
    """Test all providers in failover order."""
    providers = [
        ("Gemini", GeminiProvider),
        ("Grok", GrokProvider),
        ("OpenAI", OpenAIProvider),
        ("Mock", MockAIProvider),
    ]
    
    results = {}
    for name, provider_class in providers:
        results[name] = await test_provider(name, provider_class)
        print()
    
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    for name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{name}: {status}")
    
    if all(results.values()):
        print("\n✓ All providers working correctly!")
    else:
        print("\n✗ Some providers failed")

if __name__ == "__main__":
    asyncio.run(main())
