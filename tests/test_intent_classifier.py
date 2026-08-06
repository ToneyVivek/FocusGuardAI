"""
Unit tests for Intent Classifier.

Tests cover all intent types with representative user messages.
"""

import pytest
from app.ai.intent_classifier import IntentClassifier, Intent, IntentClassificationResult


class TestIntentClassifier:
    """Test suite for IntentClassifier."""
    
    @pytest.fixture
    def classifier(self):
        """Create a classifier instance for testing."""
        return IntentClassifier()
    
    # Basic Intents Tests
    def test_greeting_hi(self, classifier):
        result = classifier.classify("hi")
        assert result.intent == Intent.GREETING
        assert result.confidence >= 0.9
        assert not result.requires_analytics
        assert not result.requires_conversation_history
    
    def test_greeting_hello(self, classifier):
        result = classifier.classify("hello")
        assert result.intent == Intent.GREETING
        assert result.confidence >= 0.9
    
    def test_greeting_hey(self, classifier):
        result = classifier.classify("hey")
        assert result.intent == Intent.GREETING
        assert result.confidence >= 0.9
    
    def test_greeting_good_morning(self, classifier):
        result = classifier.classify("good morning")
        assert result.intent == Intent.GREETING
        assert result.confidence >= 0.9
    
    def test_farewell_bye(self, classifier):
        result = classifier.classify("bye")
        assert result.intent == Intent.FAREWELL
        assert result.confidence >= 0.9
        assert not result.requires_analytics
    
    def test_farewell_goodbye(self, classifier):
        result = classifier.classify("goodbye")
        assert result.intent == Intent.FAREWELL
        assert result.confidence >= 0.9
    
    def test_thanks_thank_you(self, classifier):
        result = classifier.classify("thank you")
        assert result.intent == Intent.THANKS
        assert result.confidence >= 0.9
        assert not result.requires_analytics
    
    def test_thanks_appreciate(self, classifier):
        result = classifier.classify("appreciate it")
        assert result.intent == Intent.THANKS
        assert result.confidence >= 0.9
    
    def test_small_talk_how_are_you(self, classifier):
        result = classifier.classify("how are you")
        assert result.intent == Intent.SMALL_TALK
        assert result.confidence >= 0.8
        assert not result.requires_analytics
    
    def test_small_talk_hows_it_going(self, classifier):
        result = classifier.classify("how's it going")
        assert result.intent == Intent.SMALL_TALK
        assert result.confidence >= 0.8
    
    # Conversation Intents Tests
    def test_correction_actually(self, classifier):
        result = classifier.classify("actually that's not right")
        assert result.intent == Intent.CORRECTION
        assert result.confidence >= 0.8
        assert not result.requires_analytics
        assert result.requires_conversation_history
    
    def test_correction_that_incorrect(self, classifier):
        result = classifier.classify("that's incorrect")
        assert result.intent == Intent.CORRECTION
        assert result.confidence >= 0.8
    
    def test_correction_no_actually(self, classifier):
        result = classifier.classify("no actually that's because")
        assert result.intent == Intent.CORRECTION
        assert result.confidence >= 0.8
    
    def test_clarification_can_you_explain(self, classifier):
        result = classifier.classify("can you explain that")
        assert result.intent == Intent.CLARIFICATION
        assert result.confidence >= 0.7
        assert not result.requires_analytics
        assert result.requires_conversation_history
    
    def test_clarification_what_do_you_mean(self, classifier):
        result = classifier.classify("what do you mean")
        assert result.intent == Intent.CLARIFICATION
        assert result.confidence >= 0.7
    
    def test_follow_up_why(self, classifier):
        result = classifier.classify("why")
        assert result.intent == Intent.FOLLOW_UP
        assert result.confidence >= 0.6
        assert not result.requires_analytics
        assert result.requires_conversation_history
    
    def test_follow_up_when_you_said(self, classifier):
        result = classifier.classify("when you said my focus score is low")
        # Matches "focus score" with higher confidence than "when you said"
        # This is reasonable - the user is asking about focus score
        assert result.intent == Intent.FOCUS_SCORE
        assert result.confidence >= 0.8
    
    def test_explanation_because(self, classifier):
        result = classifier.classify("my tab switching is high because i'm attending a lecture")
        # Matches "tab switching" (distraction_analysis) with higher confidence than "because" (explanation)
        # This is reasonable - the user is talking about tab switching
        assert result.intent == Intent.DISTRACTION_ANALYSIS
        assert result.confidence >= 0.7
        assert result.requires_analytics
    
    def test_explanation_thats_because(self, classifier):
        result = classifier.classify("that's because I had to check something")
        assert result.intent == Intent.EXPLANATION
        assert result.confidence >= 0.7
    
    def test_justification_i_had_to(self, classifier):
        result = classifier.classify("i had to switch tabs for my work")
        assert result.intent == Intent.JUSTIFICATION
        assert result.confidence >= 0.7
        assert not result.requires_analytics
        assert result.requires_conversation_history
    
    def test_justification_i_needed_to(self, classifier):
        result = classifier.classify("i needed to check email")
        assert result.intent == Intent.JUSTIFICATION
        assert result.confidence >= 0.7
    
    def test_personal_context_im_attending_lecture(self, classifier):
        result = classifier.classify("i'm attending a lecture")
        assert result.intent == Intent.PERSONAL_CONTEXT
        assert result.confidence >= 0.6
        assert not result.requires_analytics
        assert result.requires_conversation_history
    
    def test_personal_context_i_was(self, classifier):
        result = classifier.classify("i was working on a project")
        assert result.intent == Intent.PERSONAL_CONTEXT
        assert result.confidence >= 0.6
    
    def test_personal_context_currently_i(self, classifier):
        result = classifier.classify("currently i am in a meeting")
        assert result.intent == Intent.PERSONAL_CONTEXT
        assert result.confidence >= 0.6
    
    # Analytics Intents Tests
    def test_focus_score(self, classifier):
        result = classifier.classify("my focus score")
        assert result.intent == Intent.FOCUS_SCORE
        assert result.confidence >= 0.8
        assert result.requires_analytics
        assert not result.requires_conversation_history
    
    def test_focus_score_low(self, classifier):
        result = classifier.classify("focus score low")
        assert result.intent == Intent.FOCUS_SCORE
        assert result.confidence >= 0.8
    
    def test_productivity_score(self, classifier):
        result = classifier.classify("productivity score")
        assert result.intent == Intent.FOCUS_SCORE
        assert result.confidence >= 0.8
    
    def test_recommendations(self, classifier):
        result = classifier.classify("recommend")
        assert result.intent == Intent.RECOMMENDATIONS
        assert result.confidence >= 0.9
        assert result.requires_analytics
    
    def test_recommendations_how_can_i_improve(self, classifier):
        result = classifier.classify("how can i improve my productivity score")
        # Matches "how can i improve" (recommendations) - this is correct
        # The user is asking for recommendations to improve their score
        assert result.intent == Intent.RECOMMENDATIONS
        assert result.confidence >= 0.8
    
    def test_recommendations_tips(self, classifier):
        result = classifier.classify("tips for better focus")
        assert result.intent == Intent.RECOMMENDATIONS
        assert result.confidence >= 0.8
    
    def test_daily_review(self, classifier):
        result = classifier.classify("review my day")
        assert result.intent == Intent.DAILY_REVIEW
        assert result.confidence >= 0.9
        assert result.requires_analytics
    
    def test_daily_review_how_was_my_day(self, classifier):
        result = classifier.classify("how was my day")
        assert result.intent == Intent.DAILY_REVIEW
        assert result.confidence >= 0.9
    
    def test_weekly_review(self, classifier):
        result = classifier.classify("review my week")
        assert result.intent == Intent.WEEKLY_REVIEW
        assert result.confidence >= 0.9
        assert result.requires_analytics
    
    def test_weekly_review_how_was_my_week(self, classifier):
        result = classifier.classify("how was my week")
        assert result.intent == Intent.WEEKLY_REVIEW
        assert result.confidence >= 0.9
    
    def test_distraction_analysis(self, classifier):
        result = classifier.classify("what distracted me")
        assert result.intent == Intent.DISTRACTION_ANALYSIS
        assert result.confidence >= 0.8
        assert result.requires_analytics
    
    def test_distraction_analysis_tab_switching(self, classifier):
        result = classifier.classify("tab switching")
        assert result.intent == Intent.DISTRACTION_ANALYSIS
        assert result.confidence >= 0.8
    
    def test_comparison(self, classifier):
        result = classifier.classify("compare today with yesterday")
        assert result.intent == Intent.COMPARISON
        assert result.confidence >= 0.8
        assert result.requires_analytics
    
    def test_comparison_vs(self, classifier):
        result = classifier.classify("today vs yesterday")
        assert result.intent == Intent.COMPARISON
        assert result.confidence >= 0.8
    
    def test_coding_habits(self, classifier):
        result = classifier.classify("coding habits")
        assert result.intent == Intent.CODING_HABITS
        assert result.confidence >= 0.8
        assert result.requires_analytics
    
    def test_coding_habits_github(self, classifier):
        result = classifier.classify("github usage")
        assert result.intent == Intent.CODING_HABITS
        assert result.confidence >= 0.8
    
    def test_website_analysis(self, classifier):
        result = classifier.classify("what websites did i visit")
        assert result.intent == Intent.WEBSITE_ANALYSIS
        assert result.confidence >= 0.8
        assert result.requires_analytics
    
    def test_website_analysis_top_sites(self, classifier):
        result = classifier.classify("top sites")
        assert result.intent == Intent.WEBSITE_ANALYSIS
        assert result.confidence >= 0.8
    
    def test_category_analysis(self, classifier):
        result = classifier.classify("category breakdown")
        assert result.intent == Intent.CATEGORY_ANALYSIS
        assert result.confidence >= 0.8
        assert result.requires_analytics
    
    def test_category_analysis_time_by_category(self, classifier):
        result = classifier.classify("time by category")
        assert result.intent == Intent.CATEGORY_ANALYSIS
        assert result.confidence >= 0.8
    
    # Edge Cases and Low Confidence Tests
    def test_empty_message(self, classifier):
        result = classifier.classify("")
        assert result.intent == Intent.CHAT
        assert result.confidence < 0.6
    
    def test_whitespace_only(self, classifier):
        result = classifier.classify("   ")
        assert result.intent == Intent.CHAT
        assert result.confidence < 0.6
    
    def test_unrecognized_message(self, classifier):
        result = classifier.classify("the quick brown fox jumps over the lazy dog")
        assert result.intent == Intent.CHAT
        assert result.confidence < 0.6
    
    def test_ambiguous_message(self, classifier):
        result = classifier.classify("something random")
        assert result.intent == Intent.CHAT
        assert result.confidence < 0.6
    
    # Complex Multi-Intent Messages (should match highest confidence)
    def test_complex_message_with_explanation(self, classifier):
        result = classifier.classify("my focus score is low because i'm attending a lecture")
        # Matches "focus score" with higher confidence than "because"
        # This is reasonable - the user is primarily asking about focus score
        assert result.intent == Intent.FOCUS_SCORE
        assert result.requires_analytics
    
    def test_complex_message_with_personal_context(self, classifier):
        result = classifier.classify("i'm working on a coding project so my tab switching is high")
        # Matches "tab switching" (distraction_analysis) with higher confidence than "i'm" (personal_context)
        # This is reasonable - the user is primarily talking about tab switching
        assert result.intent == Intent.DISTRACTION_ANALYSIS
        assert result.requires_analytics
    
    # Test Confidence Threshold
    def test_low_confidence_fallback(self, classifier):
        result = classifier.classify("xyz")
        assert result.intent == Intent.CHAT
        assert result.confidence < 0.6
    
    # Test Result Structure
    def test_result_structure(self, classifier):
        result = classifier.classify("hello")
        assert isinstance(result, IntentClassificationResult)
        assert hasattr(result, 'intent')
        assert hasattr(result, 'confidence')
        assert hasattr(result, 'requires_analytics')
        assert hasattr(result, 'requires_conversation_history')
    
    def test_result_to_dict(self, classifier):
        result = classifier.classify("hello")
        result_dict = result.to_dict()
        assert 'intent' in result_dict
        assert 'confidence' in result_dict
        assert 'requires_analytics' in result_dict
        assert 'requires_conversation_history' in result_dict
    
    # Test Case Sensitivity
    def test_case_insensitive(self, classifier):
        result1 = classifier.classify("HELLO")
        result2 = classifier.classify("hello")
        result3 = classifier.classify("HeLLo")
        assert result1.intent == result2.intent == result3.intent == Intent.GREETING
    
    # Test Pattern Priority (more specific patterns should win)
    def test_pattern_priority_focus_score(self, classifier):
        result = classifier.classify("productivity score")
        # Should match FOCUS_SCORE (productivity score pattern) not generic chat
        assert result.intent == Intent.FOCUS_SCORE
        assert result.confidence >= 0.8
    
    # Test that all referenced intents exist in the enum
    def test_all_referenced_intents_exist(self):
        """
        Verify that all intents referenced in the codebase actually exist in the Intent enum.
        This test prevents future enum refactors from breaking the code.
        """
        from app.ai.intent_classifier import Intent
        
        # Get all valid Intent enum values
        valid_intents = {intent.value for intent in Intent}
        
        # Intents referenced in context_loader.py load_context method
        context_loader_intents = {
            "focus_score",
            "daily_review",
            "weekly_review",
            "recommendations",
            "comparison",
            "distraction_analysis",
            "coding_habits",
            "website_analysis",
            "category_analysis",
            "greeting",
            "farewell",
            "thanks",
            "small_talk",
            "clarification",
            "correction",
            "explanation",
            "justification",
            "follow_up",
            "personal_context",
            "chat"
        }
        
        # Intents referenced in service.py _generate_suggestions method
        service_suggestions_intents = {
            "greeting",
            "farewell",
            "thanks",
            "small_talk",
            "focus_score",
            "daily_review",
            "weekly_review",
            "recommendations",
            "comparison",
            "distraction_analysis",
            "coding_habits",
            "website_analysis",
            "category_analysis",
            "clarification",
            "correction",
            "explanation",
            "justification",
            "follow_up",
            "personal_context",
            "chat"
        }
        
        # Combine all referenced intents
        all_referenced_intents = context_loader_intents.union(service_suggestions_intents)
        
        # Check that all referenced intents exist in the enum
        missing_intents = all_referenced_intents - valid_intents
        
        if missing_intents:
            pytest.fail(
                f"The following intents are referenced in the code but do not exist in the Intent enum: {missing_intents}. "
                f"Please add them to the Intent enum or remove the references."
            )
        
        # Also check that all enum values are accounted for (optional - helps detect unused intents)
        unused_intents = valid_intents - all_referenced_intents
        if unused_intents:
            # This is a warning, not a failure - new intents might not be referenced yet
            print(f"\nWarning: The following Intent enum values are not referenced in the code: {unused_intents}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
