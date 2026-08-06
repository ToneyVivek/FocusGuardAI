"""
Test script to debug chat pipeline with specific message.
"""
import asyncio
from app.ai.intent_classifier import IntentClassifier
from app.ai.context_loader import ContextLoader
from app.ai.service import AIService

# Test the intent classifier
print("=" * 80)
print("TESTING INTENT CLASSIFIER")
print("=" * 80)

classifier = IntentClassifier()
test_message = "How can I improve my productivity score?"
intent = classifier.classify(test_message)

print(f"\nMessage: '{test_message}'")
print(f"Detected Intent: {intent.value}")
print(f"Expected: recommendations or focus_score")
print(f"Match: {intent.value in ['recommendations', 'focus_score']}")

print("\n" + "=" * 80)
print("TESTING COMPLETE")
print("=" * 80)
