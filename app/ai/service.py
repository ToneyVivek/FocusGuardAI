"""
AI Service

Orchestrates AI operations: fetches analytics, builds context, calls AI provider, formats response.
This service does not contain prompt text - that lives in prompts.py.
"""

import logging
import time
from datetime import date, datetime, timezone
from typing import Optional, Any, Type
from sqlalchemy.orm import Session
from pydantic import BaseModel, ValidationError

from app.models.models import User, AIConversation
from app.ai.analytics_aggregator import AnalyticsAggregator
from app.ai.context_builder import AIContextBuilder
from app.ai.intent_classifier import IntentClassifier, Intent
from app.ai.context_loader import ContextLoader
from app.ai.conversation_memory import ConversationMemory
from app.ai.provider_manager import ProviderManager
from app.ai.prompts import DailySummaryPrompt, WeeklySummaryPrompt
from app.ai.insights.analyzer import InsightsAnalyzer
from app.ai.cache_service import AIReportCacheService
from app.ai.schemas import (
    DailySummaryResponse,
    WeeklySummaryResponse,
    InsightsResponse,
    InsightItem,
    RecommendationsResponse,
    RecommendationItem,
    ChatResponse,
)
from app.config.config import settings

logger = logging.getLogger(__name__)


class AIService:
    """
    AI service orchestrator.
    
    Coordinates between analytics data, context building, and AI providers
    to generate AI-powered productivity insights.
    """
    
    def __init__(self):
        """Initialize AI service with analytics aggregator and provider manager."""
        self.aggregator = AnalyticsAggregator()
        self.context_builder = AIContextBuilder()
        self.intent_classifier = IntentClassifier()
        self.context_loader = ContextLoader()
        self.conversation_memory = ConversationMemory(max_messages=8)
        self.provider_manager = ProviderManager()
        self.insights_analyzer = InsightsAnalyzer()
        self.cache_service = AIReportCacheService()
        
        # Prompt version for cache invalidation
        self.prompt_version = "7.5"
        
        # Log AI configuration at startup
        print(f"AI_PROVIDER_ORDER={settings.AI_PROVIDER_ORDER}")
        print(f"GEMINI_MODEL={settings.GEMINI_MODEL}")
        print(f"GEMINI_API_KEYS configured: {len(settings.gemini_api_keys_list)}")
        print(f"GROK_MODEL={settings.GROK_MODEL}")
        print(f"OPENAI_MODEL={settings.OPENAI_MODEL}")
    
    async def _generate_with_validation(
        self,
        prompt: str,
        system_prompt: str,
        response_schema: Type[BaseModel],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Any:
        """
        Generate structured response with validation and retry.
        
        Args:
            prompt: The user prompt
            system_prompt: System prompt for the AI
            response_schema: Pydantic model to validate against
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Validated response object
        """
        # Limit context size if needed
        prompt = self._limit_context_size(prompt)
        
        for attempt in range(settings.AI_MAX_RETRIES + 1):
            try:
                response_dict = await self.provider_manager.generate_structured_completion(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    response_format=response_schema.model_json_schema(),
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                # Validate against schema
                validated_response = response_schema.model_validate(response_dict)
                logger.info(f"Structured response validation successful on attempt {attempt + 1}")
                return validated_response
                
            except ValidationError as e:
                logger.warning(f"Validation error on attempt {attempt + 1}: {str(e)}")
                if attempt == settings.AI_MAX_RETRIES:
                    logger.error("Max retries reached for validation")
                    raise ValueError(f"Failed to validate response after {settings.AI_MAX_RETRIES} retries")
                    
            except Exception as e:
                logger.error(f"Error generating structured response on attempt {attempt + 1}: {str(e)}")
                if attempt == settings.AI_MAX_RETRIES:
                    raise
    
    def _limit_context_size(self, context: str) -> str:
        """
        Limit context size to stay within token limits.
        
        Args:
            context: The full context string
            
        Returns:
            Truncated context if needed
        """
        # Approximate token count (1 token ≈ 4 characters)
        estimated_tokens = len(context) // 4
        
        if estimated_tokens <= settings.AI_MAX_CONTEXT_TOKENS:
            return context
        
        # Truncate context to stay within limit
        max_chars = settings.AI_MAX_CONTEXT_TOKENS * 4
        truncated = context[:max_chars]
        
        logger.warning(
            f"Context truncated from {estimated_tokens} to ~{settings.AI_MAX_CONTEXT_TOKENS} tokens"
        )
        
        return truncated + "\n\n[Context truncated due to size limits]"
    
    def _get_fallback_daily_summary(self, metrics: dict, target_date: Optional[date]) -> DailySummaryResponse:
        """Generate fallback daily summary when AI fails."""
        logger.warning("Using fallback daily summary")
        
        # Check if analytics are available
        if not metrics.get('has_sufficient_data', True):
            return DailySummaryResponse(
                title="Daily Productivity Summary",
                summary="No activity was recorded for this day. Unable to generate productivity insights.",
                highlights=[
                    "No browser activity tracked",
                    "Check if the extension was active",
                    "You may have been working outside the browser"
                ],
                recommendations=[
                    "Ensure the browser extension is running",
                    "Check your tracking settings",
                    "Try again when activity is available"
                ],
                assessment="neutral",
                focus_score=0,
                date=target_date.isoformat() if target_date else ""
            )
        
        assessment = "neutral"
        if metrics['focus_score'] >= 80:
            assessment = "positive"
        elif metrics['focus_score'] < 60:
            assessment = "needs_improvement"
        
        return DailySummaryResponse(
            title="Daily Productivity Summary",
            summary="Unable to generate AI summary at this time. Please try again later.",
            highlights=[
                f"Focus score of {metrics['focus_score']}",
                f"{self._format_minutes(metrics['productive_minutes'])} of productive work",
                f"{metrics['completed_sessions']} completed sessions"
            ],
            recommendations=[
                "Check your productivity metrics for detailed insights",
                "Try again later for AI-powered analysis"
            ],
            assessment=assessment,
            focus_score=metrics['focus_score'],
            date=target_date.isoformat() if target_date else ""
        )
    
    def _get_fallback_weekly_summary(self, metrics: dict, start_date: Optional[date], end_date: Optional[date]) -> WeeklySummaryResponse:
        """Generate fallback weekly summary when AI fails."""
        logger.warning("Using fallback weekly summary")
        
        # Check if analytics are available
        if not metrics.get('has_sufficient_data', True):
            return WeeklySummaryResponse(
                title="Weekly Productivity Review",
                summary="No activity was recorded for this week. Unable to generate productivity insights.",
                highlights=[
                    "No browser activity tracked",
                    "Check if the extension was active",
                    "You may have been working outside the browser"
                ],
                recommendations=[
                    "Ensure the browser extension is running",
                    "Check your tracking settings",
                    "Try again when activity is available"
                ],
                assessment="neutral",
                next_week_goal="Start tracking activity to get insights",
                focus_score=0,
                start_date=start_date.isoformat() if start_date else "",
                end_date=end_date.isoformat() if end_date else ""
            )
        
        assessment = "neutral"
        if metrics['focus_score'] >= 80:
            assessment = "excellent"
        elif metrics['focus_score'] < 60:
            assessment = "fair"
        
        return WeeklySummaryResponse(
            title="Weekly Productivity Review",
            summary="Unable to generate AI summary at this time. Please try again later.",
            highlights=[
                f"{self._format_minutes(metrics['productive_minutes'])} of productive work",
                f"Average focus score of {metrics['average_focus_score']}",
                f"{metrics['completed_sessions']} completed sessions"
            ],
            recommendations=[
                "Check your productivity metrics for detailed insights",
                "Try again later for AI-powered analysis"
            ],
            assessment=assessment,
            next_week_goal="Improve productivity tracking",
            focus_score=metrics['average_focus_score'],
            start_date=start_date.isoformat() if start_date else "",
            end_date=end_date.isoformat() if end_date else ""
        )
    
    def _get_fallback_insights(self, metrics: dict) -> InsightsResponse:
        """Generate fallback insights when AI fails."""
        logger.warning("Using fallback insights")
        
        return InsightsResponse(
            title="Productivity Insights",
            insights=[
                InsightItem(
                    category="general",
                    insight="AI insights temporarily unavailable",
                    data_point="Check metrics for details"
                )
            ],
            patterns=["Unable to analyze patterns at this time"],
            distractions=["Unable to analyze distractions at this time"],
            category_balance="Unable to analyze category balance at this time",
            focus_score_recommendations=["Check your focus score metrics"],
            time_allocation_suggestions=["Review your time allocation metrics"]
        )
    
    def _get_fallback_recommendations(self, metrics: dict) -> RecommendationsResponse:
        """Generate fallback recommendations when AI fails."""
        logger.warning("Using fallback recommendations")
        
        return RecommendationsResponse(
            title="Personalized Recommendations",
            recommendations=[
                RecommendationItem(
                    title="Review Your Metrics",
                    description="Check your productivity metrics for personalized insights",
                    impact="medium",
                    implementation_steps=["Open analytics dashboard", "Review recent activity"]
                )
            ],
            priority_order=["Review Your Metrics"]
        )
    
    def _get_fallback_chat_response(self, message: str) -> ChatResponse:
        """Generate fallback chat response when AI fails."""
        logger.warning("Using fallback chat response")
        
        return ChatResponse(
            message="I'm unable to process your request at this time. Please try again later.",
            context_used=False,
            suggestions=["Try again later", "Check your analytics dashboard"]
        )
    
    async def generate_daily_summary(
        self,
        db: Session,
        user: User,
        target_date: Optional[date] = None
    ) -> DailySummaryResponse:
        """
        Generate a daily productivity summary with production-ready caching.
        
        Args:
            db: Database session
            user: Authenticated user
            target_date: Optional date to analyze (defaults to today)
            
        Returns:
            Daily summary response
        """
        logger.info(f"Daily summary request - user_id: {user.id}, target_date: {target_date}")
        
        try:
            # Get aggregated metrics
            metrics = self.aggregator.aggregate_daily_metrics(db, user, target_date)
            
            # Compute analytics hash for cache lookup
            analytics_hash = self.cache_service.compute_analytics_hash(metrics)
            
            # Set date range for cache
            if target_date:
                start_date = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc)
                end_date = datetime.combine(target_date, datetime.max.time()).replace(tzinfo=timezone.utc)
            else:
                today = date.today()
                start_date = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
                end_date = datetime.combine(today, datetime.max.time()).replace(tzinfo=timezone.utc)
            
            # Get current provider and model
            provider = self.provider_manager.provider_order[0] if self.provider_manager.provider_order else "gemini"
            model = settings.GEMINI_MODEL if provider == "gemini" else "unknown"
            
            # Check cache with versioning
            cached_summary = self.cache_service.get_cached_report(
                db=db,
                user=user,
                report_type="daily",
                start_date=start_date,
                end_date=end_date,
                analytics_hash=analytics_hash,
                provider=provider,
                model=model,
                prompt_version=self.prompt_version
            )
            
            if cached_summary:
                # Return cached response
                return DailySummaryResponse(**cached_summary)
            
            # Cache miss - generate new summary
            generation_start = time.time()
            
            # Build context
            context = self.context_builder.build_daily_context(db, user, target_date)
            
            # Generate AI response using new prompt template
            logger.info(f"Sending daily summary request to provider - context_length: {len(context)}")
            ai_summary = await self.provider_manager.generate_completion(
                prompt=context,
                system_prompt=DailySummaryPrompt.SYSTEM,
                temperature=0.7
            )
            
            generation_time = time.time() - generation_start
            
            logger.info(f"Daily summary generated successfully - response_length: {len(ai_summary)}, generation_time: {generation_time:.2f}s")
            
            # Determine assessment based on focus score
            if metrics['focus_score'] >= 80:
                assessment = "positive"
            elif metrics['focus_score'] >= 60:
                assessment = "neutral"
            else:
                assessment = "needs_improvement"
            
            # Generate highlights from metrics
            highlights = [
                f"Focus score of {metrics['focus_score']}",
                f"{self._format_minutes(metrics['productive_minutes'])} of productive work",
                f"{metrics['completed_sessions']} completed sessions"
            ]
            
            if metrics['longest_focus_session_minutes'] > 60:
                highlights.append(f"Longest focus session: {metrics['longest_focus_session_minutes']} minutes")
            
            # Generate recommendations based on metrics
            recommendations = self._generate_daily_recommendations(metrics)
            
            # Build response
            response = DailySummaryResponse(
                title="Daily Productivity Summary",
                summary=ai_summary,
                highlights=highlights,
                recommendations=recommendations,
                assessment=assessment,
                focus_score=metrics['focus_score'],
                date=target_date.isoformat() if target_date else date.today().isoformat()
            )
            
            # Save to cache with structured storage
            self.cache_service.save_cached_report(
                db=db,
                user=user,
                report_type="daily",
                start_date=start_date,
                end_date=end_date,
                analytics_hash=analytics_hash,
                provider=provider,
                model=model,
                prompt_version=self.prompt_version,
                raw_llm_response=ai_summary,
                parsed_summary=response.dict(),
                generation_time=generation_time,
                token_usage=None  # Could be extracted from provider response if available
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating daily summary: {str(e)}")
            # Return fallback response
            metrics = self.aggregator.aggregate_daily_metrics(db, user, target_date)
            return self._get_fallback_daily_summary(metrics, target_date)
    
    async def generate_weekly_summary(
        self,
        db: Session,
        user: User,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> WeeklySummaryResponse:
        """
        Generate a weekly productivity review with production-ready caching.
        
        Args:
            db: Database session
            user: Authenticated user
            start_date: Optional start date
            end_date: Optional end date
            
        Returns:
            Weekly summary response
        """
        logger.info(f"Weekly summary request - user_id: {user.id}, date_range: {start_date} to {end_date}")
        
        try:
            # Get aggregated metrics
            metrics = self.aggregator.aggregate_weekly_metrics(db, user, start_date, end_date)
            
            # Compute analytics hash for cache lookup
            analytics_hash = self.cache_service.compute_analytics_hash(metrics)
            
            # Set date range for cache
            if start_date:
                cache_start_date = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
            else:
                # Default to start of current week
                today = date.today()
                cache_start_date = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
            
            if end_date:
                cache_end_date = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=timezone.utc)
            else:
                # Default to end of current week
                today = date.today()
                cache_end_date = datetime.combine(today, datetime.max.time()).replace(tzinfo=timezone.utc)
            
            # Get current provider and model
            provider = self.provider_manager.provider_order[0] if self.provider_manager.provider_order else "gemini"
            model = settings.GEMINI_MODEL if provider == "gemini" else "unknown"
            
            # Check cache with versioning
            cached_summary = self.cache_service.get_cached_report(
                db=db,
                user=user,
                report_type="weekly",
                start_date=cache_start_date,
                end_date=cache_end_date,
                analytics_hash=analytics_hash,
                provider=provider,
                model=model,
                prompt_version=self.prompt_version
            )
            
            if cached_summary:
                # Return cached response
                return WeeklySummaryResponse(**cached_summary)
            
            # Cache miss - generate new summary
            generation_start = time.time()
            
            # Build context
            context = self.context_builder.build_weekly_context(db, user, start_date, end_date)
            
            # Generate AI response using new prompt template
            logger.info(f"Sending weekly summary request to provider - context_length: {len(context)}")
            ai_summary = await self.provider_manager.generate_completion(
                prompt=context,
                system_prompt=WeeklySummaryPrompt.SYSTEM,
                temperature=0.7
            )
            
            generation_time = time.time() - generation_start
            
            logger.info(f"Weekly summary generated successfully - response_length: {len(ai_summary)}, generation_time: {generation_time:.2f}s")
            
            # Determine assessment based on focus score
            if metrics['focus_score'] >= 80:
                assessment = "excellent"
            elif metrics['focus_score'] >= 60:
                assessment = "good"
            else:
                assessment = "fair"
            
            # Generate highlights from metrics
            highlights = [
                f"{self._format_minutes(metrics['productive_minutes'])} of productive work",
                f"Average focus score of {metrics['average_focus_score']}",
                f"{metrics['completed_sessions']} completed sessions"
            ]
            
            if metrics['best_day']:
                highlights.append(f"Best day: {metrics['best_day']['date']} (score: {metrics['best_day']['focus_score']})")
            
            # Generate recommendations
            recommendations = self._generate_weekly_recommendations(metrics)
            
            # Generate next week goal
            next_week_goal = self._generate_weekly_goal(metrics)
            
            # Build response
            response = WeeklySummaryResponse(
                title="Weekly Productivity Review",
                summary=ai_summary,
                highlights=highlights,
                recommendations=recommendations,
                assessment=assessment,
                next_week_goal=next_week_goal,
                focus_score=metrics['focus_score'],
                start_date=start_date.isoformat() if start_date else date.today().isoformat(),
                end_date=end_date.isoformat() if end_date else date.today().isoformat()
            )
            
            # Save to cache with structured storage
            self.cache_service.save_cached_report(
                db=db,
                user=user,
                report_type="weekly",
                start_date=cache_start_date,
                end_date=cache_end_date,
                analytics_hash=analytics_hash,
                provider=provider,
                model=model,
                prompt_version=self.prompt_version,
                raw_llm_response=ai_summary,
                parsed_summary=response.dict(),
                generation_time=generation_time,
                token_usage=None  # Could be extracted from provider response if available
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating weekly summary: {str(e)}")
            # Return fallback response
            metrics = self.aggregator.aggregate_weekly_metrics(db, user, start_date, end_date)
            return self._get_fallback_weekly_summary(metrics, start_date, end_date)
    
    async def generate_insights(
        self,
        db: Session,
        user: User,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> InsightsResponse:
        """
        Generate productivity insights.
        
        Args:
            db: Database session
            user: Authenticated user
            start_date: Optional start date
            end_date: Optional end date
            
        Returns:
            Insights response
        """
        logger.info(f"Insights request - user_id: {user.id}, date_range: {start_date} to {end_date}")
        
        try:
            # Get aggregated metrics
            metrics = self.aggregator.aggregate_insights_metrics(db, user, start_date, end_date)
            
            # Build context
            context = self.context_builder.build_insights_context(db, user, start_date, end_date)
            
            # Generate data-driven insights
            insights = self._generate_data_insights(metrics)
            
            # Generate patterns
            patterns = self._generate_patterns(metrics)
            
            # Generate distractions
            distractions = self._generate_distractions(metrics)
            
            # Generate category balance analysis
            category_balance = self._analyze_category_balance(metrics)
            
            # Generate focus score recommendations
            focus_recommendations = self._generate_focus_score_recommendations(metrics)
            
            # Generate time allocation suggestions
            time_suggestions = self._generate_time_allocation_suggestions(metrics)
            
            logger.info(f"Insights generated successfully - insights_count: {len(insights)}, patterns_count: {len(patterns)}")
            
            return InsightsResponse(
                title="Productivity Insights",
                insights=insights,
                patterns=patterns,
                distractions=distractions,
                category_balance=category_balance,
                focus_score_recommendations=focus_recommendations,
                time_allocation_suggestions=time_suggestions
            )
            
        except Exception as e:
            logger.error(f"Error generating insights: {str(e)}")
            # Return fallback response
            metrics = self.aggregator.aggregate_insights_metrics(db, user, start_date, end_date)
            return self._get_fallback_insights(metrics)
    
    async def generate_recommendations(
        self,
        db: Session,
        user: User,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> RecommendationsResponse:
        """
        Generate personalized recommendations.
        
        Args:
            db: Database session
            user: Authenticated user
            start_date: Optional start date
            end_date: Optional end date
            
        Returns:
            Recommendations response
        """
        logger.info(f"Recommendations request - user_id: {user.id}, date_range: {start_date} to {end_date}")
        
        try:
            # Get aggregated metrics
            metrics = self.aggregator.aggregate_insights_metrics(db, user, start_date, end_date)
            
            # Generate rule-based recommendations
            recommendations = self._generate_rule_based_recommendations(metrics)
            
            # Create priority order
            priority_order = [rec.title for rec in recommendations]
            
            logger.info(f"Recommendations generated successfully - count: {len(recommendations)}")
            
            return RecommendationsResponse(
                title="Personalized Recommendations",
                recommendations=recommendations,
                priority_order=priority_order
            )
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            # Return fallback response
            metrics = self.aggregator.aggregate_insights_metrics(db, user, start_date, end_date)
            return self._get_fallback_recommendations(metrics)
    
    async def chat(
        self,
        db: Session,
        user: User,
        message: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> ChatResponse:
        """
        Generate AI chat response with intent-aware context loading.
        
        Args:
            db: Database session
            user: Authenticated user
            message: User message
            start_date: Optional start date for context
            end_date: Optional end date for context
            
        Returns:
            Chat response
        """
        print(f"[CHAT PIPELINE] ========== START ==========")
        print(f"[CHAT PIPELINE] 1. Raw user message: '{message}'")
        print(f"[CHAT PIPELINE] 2. User ID: {user.id}")
        print(f"[CHAT PIPELINE] 3. Date range: {start_date} to {end_date}")
        
        logger.info(f"Chat request received - user_id: {user.id}, message: {message[:50]}...")
        
        try:
            # Classify intent
            classification = self.intent_classifier.classify(message)
            intent = classification.intent
            confidence = classification.confidence
            requires_analytics = classification.requires_analytics
            requires_conversation_history = classification.requires_conversation_history
            
            print(f"[CHAT PIPELINE] 4. Detected intent: {intent.value}")
            print(f"[CHAT PIPELINE] 4a. Confidence: {confidence}")
            print(f"[CHAT PIPELINE] 4b. Requires analytics: {requires_analytics}")
            print(f"[CHAT PIPELINE] 4c. Requires conversation history: {requires_conversation_history}")
            logger.info(f"Detected intent: {intent.value}, confidence: {confidence}")
            
            # Add user message to conversation memory
            self.conversation_memory.add_user_message(message)
            
            # Get conversation history (needed for conversation intents)
            conversation_history = self.conversation_memory.get_conversation_history()
            
            # Load context based on intent
            target_date = start_date if start_date else date.today()
            print(f"[CHAT PIPELINE] 5. Loading context for date: {target_date}")
            context = self.context_loader.load_context(db, user, intent, target_date)
            print(f"[CHAT PIPELINE] 6. Context loaded - has_analytics: {context.get('has_analytics', False)}")
            print(f"[CHAT PIPELINE] 7. Context keys: {list(context.keys())}")
            
            # Build prompt based on intent
            if intent == Intent.GREETING:
                prompt = self._build_greeting_prompt()
            elif intent == Intent.FAREWELL:
                prompt = self._build_farewell_prompt()
            elif intent == Intent.THANKS:
                prompt = self._build_thanks_prompt()
            elif intent == Intent.SMALL_TALK:
                prompt = self._build_small_talk_prompt(message)
            elif intent in [Intent.CLARIFICATION, Intent.CORRECTION, Intent.EXPLANATION, 
                           Intent.JUSTIFICATION, Intent.FOLLOW_UP, Intent.PERSONAL_CONTEXT]:
                # Conversation intents - use conversation history
                prompt = self._build_conversation_prompt(message, intent, conversation_history)
            else:
                # Analytics question - include context
                prompt = self._build_analytics_prompt(message, context)
            
            # Build system prompt
            system_prompt = self._get_system_prompt()
            
            # Generate AI response
            print(f"[CHAT PIPELINE] 10. Sending to AI provider...")
            logger.info(f"Sending chat request to provider - intent: {intent.value}, has_analytics: {context.get('has_analytics', False)}")
            
            response = await self.provider_manager.generate_completion(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.7
            )
            
            print(f"[CHAT PIPELINE] 11. Raw Gemini response: '{response}'")
            print(f"[CHAT PIPELINE] 12. Response length: {len(response)}")
            
            # Add assistant response to memory
            self.conversation_memory.add_assistant_message(response)
            
            # Generate suggested follow-up questions
            suggestions = self._generate_suggestions(intent, context)
            
            logger.info(f"Chat response generated successfully - response_length: {len(response)}")
            print(f"[CHAT PIPELINE] ========== END ==========")
            
            return ChatResponse(
                message=response,
                context_used=context.get("has_analytics", False),
                suggestions=suggestions
            )
            
        except Exception as e:
            print(f"[CHAT PIPELINE] ERROR: {type(e).__name__}: {str(e)}")
            logger.error(f"Error generating chat response: {str(e)}")
            # Return fallback response
            return self._get_fallback_chat_response(message)
    
    def _format_minutes(self, minutes: int) -> str:
        """Format minutes into hours and minutes."""
        if minutes < 60:
            return f"{minutes}m"
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours}h {mins}m" if mins > 0 else f"{hours}h"
    
    def _generate_daily_recommendations(self, metrics: dict) -> list:
        """Generate daily recommendations based on metrics."""
        recommendations = []
        
        if metrics['focus_score'] >= 80:
            recommendations.append("Maintain your current productivity levels")
        elif metrics['focus_score'] >= 60:
            recommendations.append("Take more frequent breaks to sustain focus")
        else:
            recommendations.append("Focus on reducing distractions and improving deep work sessions")
        
        if metrics['entertainment_minutes'] > 30:
            recommendations.append("Consider reducing entertainment time during work hours")
        
        if metrics['longest_focus_session_minutes'] < 30:
            recommendations.append("Try to extend your focus sessions to at least 30 minutes")
        
        return recommendations[:3]
    
    def _generate_weekly_recommendations(self, metrics: dict) -> list:
        """Generate weekly recommendations based on metrics."""
        recommendations = []
        
        if metrics['focus_score'] >= 80:
            recommendations.append("Maintain your excellent productivity habits")
        elif metrics['focus_score'] >= 60:
            recommendations.append("Continue improving your focus consistency")
        else:
            recommendations.append("Implement structured focus blocks to improve productivity")
        
        if metrics['entertainment_minutes'] > 180:
            recommendations.append("Set limits on entertainment time during work hours")
        
        if metrics['average_focus_session_minutes'] < 30:
            recommendations.append("Practice longer focus sessions using the Pomodoro technique")
        
        return recommendations[:3]
    
    def _generate_weekly_goal(self, metrics: dict) -> str:
        """Generate a specific goal for next week."""
        if metrics['focus_score'] >= 80:
            return "Maintain focus score above 80"
        elif metrics['focus_score'] >= 60:
            return "Increase focus score to 75"
        else:
            return "Improve focus score by 10 points"
    
    def _generate_data_insights(self, metrics: dict) -> list:
        """Generate data-driven insights."""
        insights = []
        
        if metrics['most_productive_hour'] is not None:
            insights.append(InsightItem(
                category="pattern",
                insight=f"You are most productive around {metrics['most_productive_hour']}:00",
                data_point=f"Peak productivity hour"
            ))
        
        if metrics['most_productive_category']:
            insights.append(InsightItem(
                category="category",
                insight=f"Your most productive category is {metrics['most_productive_category']}",
                data_point=f"Top category by time"
            ))
        
        if metrics['average_uninterrupted_session_minutes'] > 30:
            insights.append(InsightItem(
                category="session",
                insight=f"Your average uninterrupted session is {metrics['average_uninterrupted_session_minutes']}",
                data_point=f"Deep work capability"
            ))
        
        return insights
    
    def _generate_patterns(self, metrics: dict) -> list:
        """Generate productivity patterns."""
        patterns = []
        
        if metrics['focus_score'] >= 70:
            patterns.append("Consistent high productivity throughout the period")
        
        if metrics['uninterrupted_session_count'] > 5:
            patterns.append("Good deep work habits with multiple uninterrupted sessions")
        
        if metrics['tab_switch_frequency_per_hour'] < 20:
            patterns.append("Low tab switching indicates good focus")
        
        return patterns
    
    def _generate_distractions(self, metrics: dict) -> list:
        """Generate identified distractions."""
        distractions = []
        
        if metrics['non_productive_minutes'] > 60:
            distractions.append(f"Significant time spent on non-productive activities ({self._format_minutes(metrics['non_productive_minutes'])})")
        
        if metrics['tab_switch_frequency_per_hour'] > 30:
            distractions.append("High tab switching frequency may indicate distraction")
        
        return distractions
    
    def _analyze_category_balance(self, metrics: dict) -> str:
        """Analyze category balance."""
        if metrics['productivity_percentage'] >= 70:
            return "Excellent balance with strong focus on productive activities"
        elif metrics['productivity_percentage'] >= 50:
            return "Good balance with room for improvement in productive time"
        else:
            return "Category balance needs improvement - increase productive activities"
    
    def _generate_focus_score_recommendations(self, metrics: dict) -> list:
        """Generate recommendations to improve focus score."""
        recommendations = []
        
        if metrics['average_focus_session_minutes'] < 30:
            recommendations.append("Extend focus sessions to at least 30 minutes")
        
        if metrics['tab_switch_frequency_per_hour'] > 25:
            recommendations.append("Reduce tab switching to improve focus")
        
        if metrics['uninterrupted_session_count'] < 3:
            recommendations.append("Schedule more uninterrupted deep work sessions")
        
        return recommendations
    
    def _generate_time_allocation_suggestions(self, metrics: dict) -> list:
        """Generate suggestions for better time allocation."""
        suggestions = []
        
        if metrics['non_productive_percentage'] > 30:
            suggestions.append("Reduce non-productive time allocation")
        
        if metrics['most_productive_category'] == 'DEVELOPMENT':
            suggestions.append("Continue prioritizing development work")
        
        suggestions.append("Allocate more time to high-impact activities")
        
        return suggestions
    
    def _generate_rule_based_recommendations(self, metrics: dict) -> list:
        """Generate rule-based recommendations."""
        recommendations = []
        
        # Entertainment > 25%
        if metrics['non_productive_minutes'] > 0:
            total_time = metrics['productive_minutes'] + metrics['neutral_minutes'] + metrics['non_productive_minutes']
            if total_time > 0 and (metrics['non_productive_minutes'] / total_time) > 0.25:
                recommendations.append(RecommendationItem(
                    title="Reduce non-productive time",
                    impact="high",
                    implementation_steps=[
                        "Set time limits on entertainment websites",
                        "Use website blockers during work hours",
                        "Schedule specific break times for non-productive activities"
                    ],
                    expected_outcome="Increase productivity percentage by 10-15%"
                ))
        
        # Average focus session < 30 min
        if metrics['average_focus_session_minutes'] < 30:
            recommendations.append(RecommendationItem(
                title="Extend focus sessions",
                impact="medium",
                implementation_steps=[
                    "Use Pomodoro technique (25 min focus + 5 min break)",
                    "Disable notifications during focus sessions",
                    "Schedule dedicated deep work blocks"
                ],
                expected_outcome="Increase average session length to 30+ minutes"
            ))
        
        # Productive time increased (check trend)
        if metrics['focus_score_trend'] == 'up':
            recommendations.append(RecommendationItem(
                title="Maintain productivity momentum",
                impact="medium",
                implementation_steps=[
                    "Continue current work schedule",
                    "Track what's working well",
                    "Share successful habits with team"
                ],
                expected_outcome="Sustain or improve current productivity levels"
            ))
        
        # Coding time is highest
        if metrics['most_productive_category'] == 'DEVELOPMENT':
            recommendations.append(RecommendationItem(
                title="Reinforce development habits",
                impact="low",
                implementation_steps=[
                    "Continue prioritizing coding tasks",
                    "Allocate prime hours to development work",
                    "Minimize context switching during coding"
                ],
                expected_outcome="Maintain strong development productivity"
            ))
        
        # If no recommendations generated, add a default one
        if not recommendations:
            recommendations.append(RecommendationItem(
                title="Maintain consistent work habits",
                impact="medium",
                implementation_steps=[
                    "Keep regular work hours",
                    "Take regular breaks",
                    "Review productivity metrics weekly"
                ],
                expected_outcome="Sustainable productivity improvement"
            ))
        
        return recommendations[:5]
    
    def _get_system_prompt(self) -> str:
        """
        Get the system prompt for the AI.
        
        Returns:
            System prompt string
        """
        return """You are a professional productivity coach AI assistant for FocusGuard.

Your role is to help users understand their productivity patterns and provide actionable, specific insights.

RESPONSE GUIDELINES:
- Default response length: 2-4 paragraphs
- Only produce long analyses when explicitly requested
- Avoid repeating metrics multiple times
- Never restate obvious information

RESPONSE FORMAT:
When giving advice, follow this structure:
1. Observation (what the data shows)
2. Reason (why it matters)
3. Recommendation (what to do)

Example:
"Your focus score is 73, which is solid. The biggest opportunity isn't your score itself—it's the short focus sessions that prevented deeper work. Try extending your focus sessions to 25+ minutes using the Pomodoro technique."

ANALYTICS USAGE:
- Reference metrics naturally in sentences
- Example: "You averaged 142 tab switches, which suggests frequent context switching."
- Never invent analytics or estimate values
- If data is unavailable, clearly say: "I don't have enough tracked activity to determine that."
- Never interpret missing data as zero

CONTEXT AWARENESS:
- When users provide context (e.g., "I was attending lectures", "I was debugging"), reinterpret the analytics before giving advice
- Example: If user says "I was attending lectures" after you mention high tab switching, reinterpret this as potentially productive educational activity
- Adapt your interpretation based on their real-world context

COMMUNICATION STYLE:
- Be conversational and professional, like a human productivity coach
- Avoid motivational filler like "Keep pushing!" or "You've got this!" unless the conversation naturally calls for encouragement
- Ask at most ONE follow-up question per response
- Do not ask a question in every response

IMPORTANT RULES:
1. Never invent numbers or estimate metrics. Only use the data provided in the context.
2. Never calculate values that were not supplied in the analytics data.
3. Always distinguish between:
   - Facts (what the data shows)
   - Possible explanations (what might explain the data)
   - Recommendations (what the user could do)
4. Never claim psychological causes as facts. Instead of "You are distracted," say "Your analytics suggest frequent context switching."
5. Keep responses concise and actionable.
6. For greetings, be warm and helpful without loading analytics.
7. For analytics questions, reference specific data points when available.
8. CRITICAL: When a user provides context that changes interpretation of previous data, acknowledge this and reinterpret your analysis.
"""
    
    def _build_greeting_prompt(self) -> str:
        """Build prompt for greeting intent."""
        return "The user greeted you. Respond warmly and briefly. Ask how you can help them with their productivity today. Mention that you can help with daily reviews, focus score explanations, comparisons, recommendations, distraction analysis, and coding habits."
    
    def _build_farewell_prompt(self) -> str:
        """Build prompt for farewell intent."""
        return "The user is saying goodbye. Respond briefly and warmly. Wish them well with their productivity."
    
    def _build_thanks_prompt(self) -> str:
        """Build prompt for thanks intent."""
        return "The user is thanking you. Respond briefly and warmly. Let them know you're always here to help with their productivity."
    
    def _build_small_talk_prompt(self, message: str) -> str:
        """Build prompt for small talk intent."""
        return f"The user said: {message}\n\nRespond briefly and conversationally. Gently steer the conversation toward productivity topics if appropriate."
    
    def _build_conversation_prompt(self, message: str, intent: Intent, conversation_history: list) -> str:
        """
        Build prompt for conversation intents (clarification, correction, explanation, etc.).
        
        Args:
            message: User's message
            intent: The conversation intent
            conversation_history: Previous conversation messages
            
        Returns:
            Formatted prompt with conversation context
        """
        print(f"[PROMPT BUILDER] Building conversation prompt for intent: {intent.value}")
        
        prompt = f"User Message: {message}\n"
        prompt += f"Intent: {intent.value}\n\n"
        
        if conversation_history:
            prompt += "Conversation History:\n"
            for msg in conversation_history[-5:]:  # Last 5 messages
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                prompt += f"{role}: {content}\n"
            prompt += "\n"
            
            # Add context awareness instruction
            prompt += "IMPORTANT: The user may have provided context in previous messages that changes "
            prompt += "how you should interpret their productivity data. For example:\n"
            prompt += "- If they mentioned attending lectures, high tab switching might be educational\n"
            prompt += "- If they mentioned meetings, idle time might be work-related\n"
            prompt += "- Adapt your interpretation based on this context and acknowledge it in your response.\n\n"
        else:
            prompt += "No conversation history available.\n\n"
        
        # Add intent-specific instructions
        if intent == Intent.CORRECTION:
            prompt += "The user is correcting something you said. Acknowledge the correction and adjust your response accordingly."
        elif intent == Intent.CLARIFICATION:
            prompt += "The user is asking for clarification. Explain your previous point more clearly."
        elif intent == Intent.EXPLANATION:
            prompt += "The user is providing an explanation. Acknowledge their context and incorporate it into your understanding. This is critical - their explanation may completely change how you should interpret their productivity metrics."
        elif intent == Intent.JUSTIFICATION:
            prompt += "The user is justifying their behavior. Acknowledge their reasoning without judgment. Their justification may reveal important context about their work environment or activities."
        elif intent == Intent.FOLLOW_UP:
            prompt += "The user is asking a follow-up question. Continue the conversation based on the context. Remember any context they've provided that might affect your interpretation."
        elif intent == Intent.PERSONAL_CONTEXT:
            prompt += "The user is providing personal context. Acknowledge their situation and adjust your advice accordingly. This context is crucial for accurate interpretation of their productivity data."
        
        print(f"[PROMPT BUILDER] Conversation prompt built")
        return prompt
    
    def _build_analytics_prompt(self, message: str, context: Dict[str, Any]) -> str:
        """
        Build prompt for analytics questions using insights engine.
        
        Args:
            message: User's message
            context: Analytics context data
            
        Returns:
            Formatted prompt with insights instead of raw analytics
        """
        print(f"[PROMPT BUILDER] Building analytics prompt with insights engine")
        print(f"[PROMPT BUILDER] User message: '{message}'")
        print(f"[PROMPT BUILDER] Context has_analytics: {context.get('has_analytics', False)}")
        print(f"[PROMPT BUILDER] Context intent: {context.get('intent', 'unknown')}")
        print(f"[PROMPT BUILDER] Context keys: {list(context.keys())}")
        print(f"[PROMPT BUILDER] Context data: {context}")
        
        prompt = f"User Question: {message}\n\n"
        
        # Check if analytics are available
        has_sufficient_data = context.get("has_sufficient_data", True)
        
        if not has_sufficient_data:
            reason = context.get("reason", "no_activity")
            print(f"[CHAT] analytics_available=False reason={reason}")
            
            prompt += "Analytics Status:\n"
            prompt += "No activity was recorded for the selected period.\n\n"
            prompt += "The available analytics are insufficient to evaluate the user's productivity. "
            prompt += "Explain that you cannot accurately identify distractions and ask the user "
            prompt += "whether they were working away from the tracked browser or whether tracking may not have been active.\n\n"
            print(f"[PROMPT BUILDER] No sufficient data available - reason: {reason}")
            return prompt
        
        print(f"[CHAT] analytics_available=True reason=has_data")
        
        # Special handling for comparison context
        if context.get("intent") == "comparison":
            prompt += self._build_comparison_prompt(context)
            print(f"[PROMPT BUILDER] Comparison prompt built")
            return prompt
        
        # Special handling for historical analysis context
        if context.get("intent") == "historical_analysis":
            prompt += self._build_historical_analysis_prompt(context)
            print(f"[PROMPT BUILDER] Historical analysis prompt built")
            print(f"[PROMPT BUILDER] Final prompt length: {len(prompt)}")
            print(f"[PROMPT BUILDER] Final prompt (first 500 chars): {prompt[:500]}")
            return prompt
        
        if context.get("has_analytics"):
            # Use insights engine to convert raw analytics into meaningful insights
            try:
                # Convert context to raw metrics format expected by insights analyzer
                raw_metrics = self._context_to_raw_metrics(context)
                
                # Generate insights
                insights = self.insights_analyzer.analyze_daily_insights(raw_metrics)
                
                # Format insights for prompt
                insights_text = self.insights_analyzer.format_insights_for_prompt(insights)
                prompt += insights_text
                
                print(f"[PROMPT BUILDER] Insights generated and formatted for prompt")
            except Exception as e:
                print(f"[PROMPT BUILDER] Error generating insights: {e}")
                # Fallback to raw analytics if insights generation fails
                prompt += "Analytics Data:\n"
                for key, value in context.items():
                    if key not in ["has_analytics", "intent", "date", "has_sufficient_data", "reason"]:
                        prompt += f"{key}: {value}\n"
                print(f"[PROMPT BUILDER] Fallback to raw analytics")
        else:
            prompt += "No analytics data available for this request.\n"
            print(f"[PROMPT BUILDER] No analytics data available")
        
        print(f"[PROMPT BUILDER] Final prompt length: {len(prompt)}")
        return prompt
    
    def _context_to_raw_metrics(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert context loader output to raw metrics format for insights analyzer.
        
        Args:
            context: Context from context_loader
            
        Returns:
            Raw metrics dictionary
        """
        print(f"[CONTEXT TO RAW METRICS] Input context keys: {list(context.keys())}")
        print(f"[CONTEXT TO RAW METRICS] Input context: {context}")
        
        raw_metrics = {
            "focus_score": context.get("focus_score", 0),
            "tab_switches": context.get("tab_switches", 0),
            "productive_minutes": context.get("productive_minutes", 0),
            "idle_minutes": context.get("idle_minutes", 0),
            "total_minutes": context.get("total_minutes", 0),
            "total_sessions": context.get("total_sessions", 0),
            "longest_focus_session": context.get("longest_focus_session", 0),
            "coding_minutes": context.get("coding_minutes", 0),
            "ai_tool_minutes": context.get("ai_tool_minutes", 0),
            "entertainment_minutes": context.get("entertainment_minutes", 0),
            "social_minutes": context.get("social_minutes", 0),
        }
        
        print(f"[CONTEXT TO RAW METRICS] Raw metrics before derived fields: {raw_metrics}")
        
        # Calculate derived fields
        raw_metrics["productive_ratio"] = (
            raw_metrics["productive_minutes"] / max(raw_metrics["total_minutes"], 1)
        )
        
        # Add session lengths if available
        raw_metrics["session_lengths"] = context.get("session_lengths", [])
        
        # Add hourly productivity if available
        raw_metrics["hourly_productivity"] = context.get("hourly_productivity", {})
        
        # Add session variance
        if len(raw_metrics["session_lengths"]) > 1:
            from statistics import stdev
            raw_metrics["session_variance"] = stdev(raw_metrics["session_lengths"])
        else:
            raw_metrics["session_variance"] = 0
        
        # Add unique websites count
        raw_metrics["unique_websites"] = context.get("unique_websites", 0)
        
        print(f"[CONTEXT TO RAW METRICS] Raw metrics after derived fields: {raw_metrics}")
        return raw_metrics
    
    def _build_comparison_prompt(self, context: Dict[str, Any]) -> str:
        """
        Build prompt for comparison questions with both current and previous period data.
        
        Args:
            context: Comparison context with current_date and previous_date data
            
        Returns:
            Formatted prompt with comparison data
        """
        print(f"[PROMPT BUILDER] Building comparison prompt")
        
        current = context.get("current_date", {})
        previous = context.get("previous_date", {})
        
        prompt = "Productivity Comparison:\n\n"
        
        # Current period data
        prompt += f"Current Period ({current.get('date', 'today')}):\n"
        if current.get("has_data"):
            prompt += f"- Productive Time: {current.get('productive_minutes', 0)} minutes\n"
            prompt += f"- Idle Time: {current.get('idle_minutes', 0)} minutes\n"
            prompt += f"- Focus Score: {current.get('focus_score', 0)}/100\n"
            prompt += f"- Total Sessions: {current.get('total_sessions', 0)}\n"
        else:
            prompt += "- No activity data available for this period\n"
        
        prompt += "\n"
        
        # Previous period data
        prompt += f"Previous Period ({previous.get('date', 'previous day')}):\n"
        if previous.get("has_data"):
            prompt += f"- Productive Time: {previous.get('productive_minutes', 0)} minutes\n"
            prompt += f"- Idle Time: {previous.get('idle_minutes', 0)} minutes\n"
            prompt += f"- Focus Score: {previous.get('focus_score', 0)}/100\n"
            prompt += f"- Total Sessions: {previous.get('total_sessions', 0)}\n"
        else:
            prompt += "- No activity data available for this period\n"
        
        prompt += "\n"
        prompt += "Compare these two periods and provide insights about the differences. "
        prompt += "If one period has no data, acknowledge this and focus on the available data.\n"
        
        return prompt
    
    def _build_historical_analysis_prompt(self, context: Dict[str, Any]) -> str:
        """
        Build prompt for historical analysis questions with best/worst day data.
        
        Args:
            context: Historical analysis context with daily breakdown
            
        Returns:
            Formatted prompt with historical data
        """
        print(f"[PROMPT BUILDER] Building historical analysis prompt")
        
        best_day = context.get("best_day", {})
        worst_day = context.get("worst_day", {})
        most_productive_day = context.get("most_productive_day", {})
        most_development_day = context.get("most_development_day", {})
        total_days = context.get("total_days_with_data", 0)
        date_range = context.get("date_range", {})
        
        prompt = "Historical Productivity Analysis:\n\n"
        
        prompt += f"Date Range: {date_range.get('start', 'N/A')} to {date_range.get('end', 'N/A')}\n"
        prompt += f"Total days with data: {total_days}\n\n"
        
        # Best day by focus score
        if best_day:
            prompt += f"Best Day (by Focus Score):\n"
            prompt += f"- Date: {best_day.get('date', 'N/A')}\n"
            prompt += f"- Focus Score: {best_day.get('focus_score', 0)}/100\n"
            prompt += f"- Productive Time: {best_day.get('productive_minutes', 0)} minutes\n\n"
        
        # Worst day by focus score
        if worst_day:
            prompt += f"Worst Day (by Focus Score):\n"
            prompt += f"- Date: {worst_day.get('date', 'N/A')}\n"
            prompt += f"- Focus Score: {worst_day.get('focus_score', 0)}/100\n"
            prompt += f"- Productive Time: {worst_day.get('productive_minutes', 0)} minutes\n\n"
        
        # Most productive day
        if most_productive_day:
            prompt += f"Most Productive Day (by Productive Minutes):\n"
            prompt += f"- Date: {most_productive_day.get('date', 'N/A')}\n"
            prompt += f"- Productive Time: {most_productive_day.get('productive_minutes', 0)} minutes\n"
            prompt += f"- Focus Score: {most_productive_day.get('focus_score', 0)}/100\n"
            if most_productive_day.get('category_breakdown'):
                prompt += f"- Category Breakdown: {most_productive_day.get('category_breakdown')}\n"
            prompt += "\n"
        
        # Most development day (if category data available)
        if most_development_day:
            prompt += f"Most Development Time Day:\n"
            prompt += f"- Date: {most_development_day.get('date', 'N/A')}\n"
            prompt += f"- Development Time: {most_development_day.get('category_breakdown', {}).get('DEVELOPMENT', 0)} minutes\n"
            prompt += f"- Total Productive Time: {most_development_day.get('productive_minutes', 0)} minutes\n"
            prompt += f"- Focus Score: {most_development_day.get('focus_score', 0)}/100\n"
            if most_development_day.get('category_breakdown'):
                prompt += f"- Full Category Breakdown: {most_development_day.get('category_breakdown')}\n"
            prompt += "\n"
        
        prompt += "Use this historical data to answer the user's question about their best day, "
        prompt += "most productive day, or performance patterns. Explain why certain days were better "
        prompt += "and provide specific metrics to support your analysis.\n"
        
        return prompt
    
    def _generate_suggestions(self, intent: Intent, context: Dict[str, Any]) -> list:
        """
        Generate suggested follow-up questions based on intent.
        
        Args:
            intent: The detected intent
            context: Analytics context
            
        Returns:
            List of 3 suggested follow-up questions
        """
        suggestions_map = {
            Intent.GREETING: [
                "Review today's productivity",
                "Explain my focus score",
                "Compare this week with last week"
            ],
            Intent.FAREWELL: [
                "Review today's productivity",
                "How can I improve tomorrow?",
                "What distracted me today?"
            ],
            Intent.THANKS: [
                "Review today's productivity",
                "How can I improve?",
                "Analyze my distractions"
            ],
            Intent.SMALL_TALK: [
                "Review today's productivity",
                "Explain my focus score",
                "How can I improve?"
            ],
            Intent.FOCUS_SCORE: [
                "How can I improve my focus score?",
                "Compare today with yesterday",
                "What distracted me today?"
            ],
            Intent.DAILY_REVIEW: [
                "Compare this with yesterday",
                "What were my main distractions?",
                "How can I improve tomorrow?"
            ],
            Intent.WEEKLY_REVIEW: [
                "Compare this week with last week",
                "What was my best day?",
                "How can I improve next week?"
            ],
            Intent.RECOMMENDATIONS: [
                "Review today's productivity",
                "Explain my focus score",
                "Analyze my distractions"
            ],
            Intent.COMPARISON: [
                "Compare this week with last week",
                "What was my best day?",
                "How can I improve?"
            ],
            Intent.DISTRACTION_ANALYSIS: [
                "How can I reduce distractions?",
                "Review today's productivity",
                "Explain my focus score"
            ],
            Intent.CODING_HABITS: [
                "Review today's productivity",
                "What distracted me today?",
                "How can I improve?"
            ],
            Intent.WEBSITE_ANALYSIS: [
                "What distracted me today?",
                "Review today's productivity",
                "How can I improve?"
            ],
            Intent.CATEGORY_ANALYSIS: [
                "What distracted me today?",
                "Review today's productivity",
                "How can I improve?"
            ],
            Intent.CHAT: [
                "Review today's productivity",
                "Explain my focus score",
                "How can I improve?"
            ]
        }
        
        return suggestions_map.get(intent, suggestions_map[Intent.CHAT])
    
    def save_conversation(
        self,
        db: Session,
        user: User,
        user_message: str,
        assistant_message: str,
        suggestions: list
    ) -> None:
        """
        Save conversation to database for persistence.

        Args:
            db: Database session
            user: Authenticated user
            user_message: User's message
            assistant_message: AI's response
            suggestions: Suggested follow-up questions
        """
        try:
            print(f"[SAVE CONVERSATION] Saving conversation for user {user.id}")
            print(f"[SAVE CONVERSATION] User message: {user_message[:50]}...")
            print(f"[SAVE CONVERSATION] Assistant message: {assistant_message[:50]}...")

            # Get or create conversation for user
            conversation = db.query(AIConversation).filter(
                AIConversation.user_id == user.id
            ).first()

            if not conversation:
                print(f"[SAVE CONVERSATION] Creating new conversation")
                print(f"[SAVE CONVERSATION] Existing conversation ID: None")
                print(f"[SAVE CONVERSATION] Existing stored message count: 0")
                conversation = AIConversation(
                    user_id=user.id,
                    messages=[],
                    suggested_questions=suggestions
                )
                db.add(conversation)
            else:
                print(f"[SAVE CONVERSATION] Updating existing conversation")
                print(f"[SAVE CONVERSATION] Existing conversation ID: {conversation.id}")
                print(f"[SAVE CONVERSATION] Existing stored message count: {len(conversation.messages)}")
                # Update existing conversation
                conversation.suggested_questions = suggestions

            # Add new messages
            from datetime import datetime, timezone
            conversation.messages.append({
                "role": "user",
                "content": user_message,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            conversation.messages.append({
                "role": "assistant",
                "content": assistant_message,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

            print(f"[SAVE CONVERSATION] New message count after append: {len(conversation.messages)}")

            # Flag the messages column as modified so SQLAlchemy detects the change
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(conversation, "messages")

            # Keep only last 20 messages
            if len(conversation.messages) > 20:
                conversation.messages = conversation.messages[-20:]
                print(f"[SAVE CONVERSATION] Trimmed to last 20 messages")
                flag_modified(conversation, "messages")

            conversation.last_message_at = datetime.now(timezone.utc)

            db.commit()
            print(f"[SAVE CONVERSATION] Database commit completed")
            print(f"[SAVE CONVERSATION] Final message count in database: {len(conversation.messages)}")
            print(f"[SAVE CONVERSATION] Conversation ID: {conversation.id}")
            logger.info(f"Conversation saved for user {user.id}, total messages: {len(conversation.messages)}")
        except Exception as e:
            logger.error(f"Error saving conversation: {str(e)}")
            print(f"[SAVE CONVERSATION] Error: {str(e)}")
            db.rollback()
    
    def get_latest_conversation(
        self,
        db: Session,
        user: User
    ):
        """
        Get the user's latest conversation from database.

        Args:
            db: Database session
            user: Authenticated user

        Returns:
            ConversationResponse with messages and suggestions
        """
        from app.ai.schemas import ConversationResponse, ChatMessage

        try:
            print(f"[GET LATEST CONVERSATION] Fetching for user {user.id}")
            conversation = db.query(AIConversation).filter(
                AIConversation.user_id == user.id
            ).first()

            if not conversation:
                print(f"[GET LATEST CONVERSATION] No conversation found for user {user.id}")
                return ConversationResponse(
                    messages=[],
                    suggested_questions=[],
                    last_message_at=None
                )

            print(f"[GET LATEST CONVERSATION] Found conversation ID: {conversation.id}")
            print(f"[GET LATEST CONVERSATION] Message count in database: {len(conversation.messages)}")
            
            # Convert messages to ChatMessage format
            chat_messages = []
            for msg in conversation.messages:
                chat_messages.append(ChatMessage(
                    role=msg["role"],
                    content=msg["content"],
                    timestamp=datetime.fromisoformat(msg["timestamp"]) if msg.get("timestamp") else None
                ))
            
            return ConversationResponse(
                messages=chat_messages,
                suggested_questions=conversation.suggested_questions or [],
                last_message_at=conversation.last_message_at
            )
        except Exception as e:
            logger.error(f"Error loading conversation: {str(e)}")
            return ConversationResponse(
                messages=[],
                suggested_questions=[],
                last_message_at=None
            )
    
    def clear_conversation(
        self,
        db: Session,
        user: User
    ) -> None:
        """
        Clear the user's conversation from database.
        
        Args:
            db: Database session
            user: Authenticated user
        """
        try:
            conversation = db.query(AIConversation).filter(
                AIConversation.user_id == user.id
            ).first()
            
            if conversation:
                db.delete(conversation)
                db.commit()
                logger.info(f"Conversation cleared for user {user.id}")
        except Exception as e:
            logger.error(f"Error clearing conversation: {str(e)}")
            db.rollback()
