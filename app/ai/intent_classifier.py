"""
Intent Classifier for AI Chat

Determines the user's intent from their message to decide what data to load.
"""

from typing import Literal
from enum import Enum


class Intent(str, Enum):
    """Supported conversation intents."""
    # Basic intents
    GREETING = "greeting"
    FAREWELL = "farewell"
    THANKS = "thanks"
    SMALL_TALK = "small_talk"
    
    # Analytics intents
    DAILY_REVIEW = "daily_review"
    WEEKLY_REVIEW = "weekly_review"
    FOCUS_SCORE = "focus_score"
    RECOMMENDATIONS = "recommendations"
    COMPARISON = "comparison"
    DISTRACTION_ANALYSIS = "distraction_analysis"
    CODING_HABITS = "coding_habits"
    WEBSITE_ANALYSIS = "website_analysis"
    CATEGORY_ANALYSIS = "category_analysis"
    HISTORICAL_ANALYSIS = "historical_analysis"
    
    # Conversation intents
    CLARIFICATION = "clarification"
    CORRECTION = "correction"
    EXPLANATION = "explanation"
    JUSTIFICATION = "justification"
    FOLLOW_UP = "follow_up"
    PERSONAL_CONTEXT = "personal_context"
    
    # Default
    CHAT = "chat"


class IntentClassificationResult:
    """Result of intent classification with metadata."""
    
    def __init__(
        self,
        intent: Intent,
        confidence: float,
        requires_analytics: bool,
        requires_conversation_history: bool
    ):
        self.intent = intent
        self.confidence = confidence
        self.requires_analytics = requires_analytics
        self.requires_conversation_history = requires_conversation_history
    
    def to_dict(self) -> dict:
        return {
            "intent": self.intent.value,
            "confidence": self.confidence,
            "requires_analytics": self.requires_analytics,
            "requires_conversation_history": self.requires_conversation_history
        }


class IntentClassifier:
    """
    Rule-based intent classifier for determining user intent from messages.
    """
    
    def __init__(self):
        """Initialize the classifier with intent patterns and weights."""
        self.patterns = {
            # Basic intents (highest weight, checked first)
            Intent.GREETING: {
                "patterns": ["hi", "hello", "hey", "good morning", "good afternoon", "good evening",
                            "greetings", "what's up", "sup", "yo"],
                "weight": 1.0,
                "requires_analytics": False,
                "requires_conversation_history": False
            },
            Intent.FAREWELL: {
                "patterns": ["bye", "goodbye", "see you", "see ya", "later", "farewell",
                            "good night", "have a good one"],
                "weight": 1.0,
                "requires_analytics": False,
                "requires_conversation_history": False
            },
            Intent.THANKS: {
                "patterns": ["thanks", "thank you", "appreciate it", "thank you very much"],
                "weight": 1.0,
                "requires_analytics": False,
                "requires_conversation_history": False
            },
            Intent.SMALL_TALK: {
                "patterns": ["how are you", "how's it going", "what's new", "how do you do",
                            "nice to meet you", "i'm doing well", "doing good"],
                "weight": 0.9,
                "requires_analytics": False,
                "requires_conversation_history": False
            },
            
            # Conversation intents (medium weight)
            Intent.CORRECTION: {
                "patterns": ["actually", "that's not right", "that's incorrect", "no that's wrong",
                            "that's not correct", "actually that's", "wait that's", "no actually",
                            "that's wrong", "incorrect", "that is wrong"],
                "weight": 0.95,
                "requires_analytics": False,
                "requires_conversation_history": True
            },
            Intent.CLARIFICATION: {
                "patterns": ["can you explain", "what do you mean", "explain that", "clarify",
                            "what does that mean", "how so", "why is that", "what are you saying"],
                "weight": 0.85,
                "requires_analytics": False,
                "requires_conversation_history": True
            },
            Intent.FOLLOW_UP: {
                "patterns": ["why", "when you said", "what about", "how about", "tell me more",
                            "elaborate", "go on", "continue", "what else", "and then"],
                "weight": 0.8,
                "requires_analytics": False,
                "requires_conversation_history": True
            },
            Intent.EXPLANATION: {
                "patterns": ["because", "since", "as", "due to", "the reason is", "that's because",
                            "this is because", "it's because", "my reason is"],
                "weight": 0.85,
                "requires_analytics": False,
                "requires_conversation_history": True
            },
            Intent.JUSTIFICATION: {
                "patterns": ["i had to", "i needed to", "i was forced to", "i had no choice",
                            "it was necessary", "i couldn't help it", "i was required to"],
                "weight": 0.85,
                "requires_analytics": False,
                "requires_conversation_history": True
            },
            Intent.PERSONAL_CONTEXT: {
                "patterns": ["i'm", "i am", "i was", "i've been", "i have been", "my situation",
                            "my context", "currently i", "right now i", "at the moment i"],
                "weight": 0.75,
                "requires_analytics": False,
                "requires_conversation_history": True
            },
            
            # Analytics intents (specific patterns, high weight)
            Intent.RECOMMENDATIONS: {
                "patterns": ["recommend", "suggestion", "how can i improve", "tips",
                            "advice", "better", "optimization", "increase productivity", "improve productivity"],
                "weight": 0.95,
                "requires_analytics": True,
                "requires_conversation_history": False
            },
            Intent.FOCUS_SCORE: {
                "patterns": ["focus score", "why is my focus score", "focus score low", "focus score high",
                            "my focus score", "explain focus score", "focus rating", "productivity score"],
                "weight": 0.95,
                "requires_analytics": True,
                "requires_conversation_history": False
            },
            Intent.DAILY_REVIEW: {
                "patterns": ["review my day", "daily review", "how was my day", "today's review",
                            "review today", "how did i do today", "today's performance"],
                "weight": 0.95,
                "requires_analytics": True,
                "requires_conversation_history": False
            },
            Intent.WEEKLY_REVIEW: {
                "patterns": ["review my week", "weekly review", "how was my week", "this week's review",
                            "review this week", "how did i do this week", "weekly summary"],
                "weight": 0.95,
                "requires_analytics": True,
                "requires_conversation_history": False
            },
            Intent.DISTRACTION_ANALYSIS: {
                "patterns": ["distract", "distraction", "distracting", "what distracted me",
                            "why was i distracted", "distractions", "time wasting", "tab switching"],
                "weight": 0.9,
                "requires_analytics": True,
                "requires_conversation_history": False
            },
            Intent.COMPARISON: {
                "patterns": ["compare", "difference", "vs", "versus", "better than", "worse than",
                            "compare today", "compare this week", "compare with yesterday"],
                "weight": 0.9,
                "requires_analytics": True,
                "requires_conversation_history": False
            },
            Intent.CODING_HABITS: {
                "patterns": ["coding", "programming", "developer", "code", "leetcode", "github",
                            "stack overflow", "programming habits", "development"],
                "weight": 0.85,
                "requires_analytics": True,
                "requires_conversation_history": False
            },
            Intent.WEBSITE_ANALYSIS: {
                "patterns": ["website", "domain", "site", "what websites", "top sites",
                            "most visited", "web usage", "browser"],
                "weight": 0.85,
                "requires_analytics": True,
                "requires_conversation_history": False
            },
            Intent.CATEGORY_ANALYSIS: {
                "patterns": ["category", "categories", "what category", "category breakdown",
                            "time by category", "category distribution"],
                "weight": 0.85,
                "requires_analytics": True,
                "requires_conversation_history": False
            },
            Intent.HISTORICAL_ANALYSIS: {
                "patterns": ["best day", "most productive day", "highest focus score", "best performance",
                            "which day was", "which day did", "what day had", "what day did",
                            "when was my best", "most productive", "highest productivity",
                            "best day this week", "best day this month", "worst day", "least productive day",
                            "most time coding", "most time in development", "most time programming"],
                "weight": 0.9,
                "requires_analytics": True,
                "requires_conversation_history": False
            }
        }
    
    def classify(self, message: str) -> IntentClassificationResult:
        """
        Classify the intent of a user message with confidence scoring.
        
        Args:
            message: The user's message text
            
        Returns:
            IntentClassificationResult with intent, confidence, and metadata
        """
        print(f"[INTENT CLASSIFIER] Raw message: '{message}'")
        
        if not message or not message.strip():
            print("[INTENT CLASSIFIER] Empty message, returning CHAT with low confidence")
            return IntentClassificationResult(
                intent=Intent.CHAT,
                confidence=0.3,
                requires_analytics=False,
                requires_conversation_history=False
            )
        
        message_lower = message.lower().strip()
        print(f"[INTENT CLASSIFIER] Normalized message: '{message_lower}'")
        
        best_match = None
        best_confidence = 0.0
        
        # Check each intent's patterns
        for intent, config in self.patterns.items():
            patterns = config["patterns"]
            weight = config["weight"]
            
            for pattern in patterns:
                # Use word boundary matching to avoid substring matches
                # Check if pattern exists as a whole word or phrase
                if self._pattern_matches(message_lower, pattern):
                    # Calculate confidence based on pattern match quality
                    if message_lower == pattern:
                        confidence = weight * 1.0
                    elif message_lower.startswith(pattern + " ") or message_lower.endswith(" " + pattern):
                        confidence = weight * 0.95
                    elif " " + pattern + " " in message_lower:
                        confidence = weight * 0.9
                    else:
                        confidence = weight * 0.85
                    
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = intent
                        print(f"[INTENT CLASSIFIER] Matched pattern '{pattern}' -> Intent: {intent.value}, Confidence: {confidence}")
        
        # If no match or low confidence, return CHAT
        if best_match is None or best_confidence < 0.6:
            print(f"[INTENT CLASSIFIER] No high-confidence match, returning CHAT")
            return IntentClassificationResult(
                intent=Intent.CHAT,
                confidence=best_confidence if best_match else 0.3,
                requires_analytics=False,
                requires_conversation_history=False
            )
        
        # Return the best match with its config
        config = self.patterns[best_match]
        print(f"[INTENT CLASSIFIER] Final intent: {best_match.value}, Confidence: {best_confidence}")
        print(f"[INTENT CLASSIFIER] Requires analytics: {config['requires_analytics']}")
        
        return IntentClassificationResult(
            intent=best_match,
            confidence=best_confidence,
            requires_analytics=config["requires_analytics"],
            requires_conversation_history=config["requires_conversation_history"]
        )
    
    def _pattern_matches(self, message: str, pattern: str) -> bool:
        """
        Check if pattern matches as a whole word or phrase, not as substring.
        
        Args:
            message: The normalized message
            pattern: The pattern to match
            
        Returns:
            True if pattern matches as whole word/phrase
        """
        # Exact match
        if message == pattern:
            return True
        
        # Pattern at start (followed by space or end)
        if message.startswith(pattern):
            if len(message) == len(pattern) or message[len(pattern)] == ' ':
                return True
        
        # Pattern at end (preceded by space)
        if message.endswith(pattern):
            if len(message) == len(pattern) or message[-len(pattern) - 1] == ' ':
                return True
        
        # Pattern in middle (surrounded by spaces)
        if f" {pattern} " in message:
            return True
        
        return False
    
    def requires_analytics(self, result: IntentClassificationResult) -> bool:
        """
        Determine if an intent requires loading analytics data.
        
        Args:
            result: The classification result
            
        Returns:
            True if analytics should be loaded, False otherwise
        """
        return result.requires_analytics
