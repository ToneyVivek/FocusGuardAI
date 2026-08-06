"""
Context Loader for AI Chat

Loads only the analytics data required for a specific intent.
"""

from datetime import date, datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.models import User
from app.ai.intent_classifier import Intent
from app.ai.analytics_aggregator import AnalyticsAggregator


class ContextLoader:
    """
    Loads context-specific analytics data based on user intent.
    
    Instead of loading all analytics for every request, this service
    loads only the data required for the detected intent.
    """
    
    def __init__(self):
        """Initialize the context loader with an analytics aggregator."""
        self.aggregator = AnalyticsAggregator()
    
    def load_context(
        self,
        db: Session,
        user: User,
        intent: Intent,
        target_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Load analytics context based on the detected intent.
        
        Args:
            db: Database session
            user: Authenticated user
            intent: The classified user intent
            target_date: Optional target date for analysis
            
        Returns:
            Context dictionary with only the required analytics data
        """
        print(f"[CONTEXT LOADER] Loading context - Intent: {intent.value}, User: {user.id}, Date: {target_date}")
        
        # These intents don't require any analytics
        no_analytics_intents = [
            Intent.GREETING, Intent.FAREWELL, Intent.THANKS, Intent.SMALL_TALK,
            Intent.CLARIFICATION, Intent.CORRECTION, Intent.EXPLANATION,
            Intent.JUSTIFICATION, Intent.FOLLOW_UP, Intent.PERSONAL_CONTEXT
        ]
        
        if intent in no_analytics_intents:
            print(f"[CONTEXT LOADER] Intent {intent.value} requires no analytics")
            return {"has_analytics": False}
        
        # Default to today if no date provided
        if target_date is None:
            target_date = date.today()
        
        context = {"has_analytics": True, "intent": intent.value, "date": target_date.isoformat()}
        
        # Load data based on intent
        if intent == Intent.FOCUS_SCORE:
            print(f"[CONTEXT LOADER] Loading FOCUS_SCORE context")
            context.update(self._load_focus_score_context(db, user, target_date))
        elif intent == Intent.DAILY_REVIEW:
            print(f"[CONTEXT LOADER] Loading DAILY_REVIEW context")
            context.update(self._load_daily_review_context(db, user, target_date))
        elif intent == Intent.WEEKLY_REVIEW:
            print(f"[CONTEXT LOADER] Loading WEEKLY_REVIEW context")
            context.update(self._load_weekly_review_context(db, user, target_date))
        elif intent == Intent.RECOMMENDATIONS:
            print(f"[CONTEXT LOADER] Loading RECOMMENDATIONS context")
            context.update(self._load_recommendations_context(db, user, target_date))
        elif intent == Intent.COMPARISON:
            print(f"[CONTEXT LOADER] Loading COMPARISON context")
            context.update(self._load_comparison_context(db, user, target_date))
        elif intent == Intent.DISTRACTION_ANALYSIS:
            print(f"[CONTEXT LOADER] Loading DISTRACTION_ANALYSIS context")
            context.update(self._load_distraction_context(db, user, target_date))
        elif intent == Intent.CODING_HABITS:
            print(f"[CONTEXT LOADER] Loading CODING_HABITS context")
            context.update(self._load_coding_habits_context(db, user, target_date))
        elif intent == Intent.WEBSITE_ANALYSIS:
            print(f"[CONTEXT LOADER] Loading WEBSITE_ANALYSIS context")
            context.update(self._load_website_analysis_context(db, user, target_date))
        elif intent == Intent.CATEGORY_ANALYSIS:
            print(f"[CONTEXT LOADER] Loading CATEGORY_ANALYSIS context")
            context.update(self._load_category_analysis_context(db, user, target_date))
        elif intent == Intent.HISTORICAL_ANALYSIS:
            print(f"[CONTEXT LOADER] Loading HISTORICAL_ANALYSIS context")
            context.update(self._load_historical_analysis_context(db, user, target_date))
        else:
            print(f"[CONTEXT LOADER] Loading MINIMAL context (default)")
            context.update(self._load_minimal_context(db, user, target_date))
        
        # Log analytics availability
        has_sufficient_data = context.get("has_sufficient_data", True)
        reason = context.get("reason", "has_data")
        print(f"[CHAT] analytics_available={has_sufficient_data} reason={reason}")
        
        print(f"[CONTEXT LOADER] Loaded context keys: {list(context.keys())}")
        print(f"[CONTEXT LOADER] Context data: {context}")
        return context
    
    def _load_focus_score_context(self, db: Session, user: User, target_date: date) -> Dict[str, Any]:
        """
        Load context for focus score questions.
        
        Loads: focus score, productive time, idle time, sessions
        """
        print(f"[CONTEXT LOADER] _load_focus_score_context called for user {user.id} on {target_date}")
        summary = self.aggregator.aggregate_daily_metrics(db, user, target_date)
        print(f"[CONTEXT LOADER] Summary keys: {list(summary.keys())}")
        
        # Check if analytics are available
        if not summary.get("has_sufficient_data", True):
            print(f"[CONTEXT LOADER] No sufficient data available")
            return {
                "has_sufficient_data": False,
                "reason": summary.get("reason", "no_activity")
            }
        
        result = {
            "has_sufficient_data": True,
            "focus_score": summary.get("focus_score"),
            "productive_minutes": summary.get("productive_minutes"),
            "idle_minutes": summary.get("idle_time_minutes"),
            "total_sessions": summary.get("completed_sessions"),
            "coding_minutes": summary.get("coding_minutes", 0),
            "total_minutes": summary.get("total_focus_time_minutes", 0),
            "session_lengths": summary.get("session_lengths", []),
        }
        print(f"[CONTEXT LOADER] Focus score context loaded: {result}")
        print(f"[CONTEXT LOADER] coding_minutes: {result.get('coding_minutes')}")
        print(f"[CONTEXT LOADER] total_minutes: {result.get('total_minutes')}")
        print(f"[CONTEXT LOADER] session_lengths count: {len(result.get('session_lengths', []))}")
        return result
    
    def _load_daily_review_context(self, db: Session, user: User, target_date: date) -> Dict[str, Any]:
        """
        Load context for daily review.
        
        Loads: daily summary, productivity breakdown, top categories
        """
        summary = self.aggregator.aggregate_daily_metrics(db, user, target_date)
        
        # Check if analytics are available
        if not summary.get("has_sufficient_data", True):
            return {
                "has_sufficient_data": False,
                "reason": summary.get("reason", "no_activity")
            }
        
        return {
            "has_sufficient_data": True,
            "daily_summary": {
                "total_minutes": summary.get("total_focus_time_minutes"),
                "productive_minutes": summary.get("productive_minutes"),
                "idle_minutes": summary.get("idle_time_minutes"),
                "focus_score": summary.get("focus_score"),
                "total_sessions": summary.get("completed_sessions")
            },
            "productivity_breakdown": {
                "productive_percentage": summary.get("productivity_percentage"),
                "neutral_percentage": summary.get("neutral_percentage"),
                "non_productive_percentage": summary.get("non_productive_percentage")
            },
            "top_categories": summary.get("top_categories", [])[:5]
        }
    
    def _load_weekly_review_context(self, db: Session, user: User, target_date: date) -> Dict[str, Any]:
        """
        Load context for weekly review.
        
        Loads: weekly summary, best day, worst day, top categories
        """
        # Calculate week start (Monday)
        week_start = target_date - timedelta(days=target_date.weekday())
        week_end = week_start + timedelta(days=6)
        
        summary = self.aggregator.aggregate_weekly_metrics(db, user, week_start, week_end)
        
        # Check if analytics are available
        if not summary.get("has_sufficient_data", True):
            return {
                "has_sufficient_data": False,
                "reason": summary.get("reason", "no_activity")
            }
        
        return {
            "has_sufficient_data": True,
            "weekly_summary": {
                "total_minutes": summary.get("total_focus_time_minutes"),
                "productive_minutes": summary.get("productive_minutes"),
                "idle_minutes": summary.get("idle_time_minutes"),
                "average_focus_score": summary.get("average_focus_score"),
                "total_sessions": summary.get("completed_sessions")
            },
            "best_day": summary.get("best_day"),
            "worst_day": summary.get("worst_day"),
            "top_categories": summary.get("top_categories", [])[:5],
            "daily_breakdown": summary.get("daily_breakdown", [])[:7]
        }
    
    def _load_recommendations_context(self, db: Session, user: User, target_date: date) -> Dict[str, Any]:
        """
        Load context for recommendations.
        
        Loads: productivity breakdown, distractions, idle time
        """
        summary = self.aggregator.aggregate_daily_metrics(db, user, target_date)
        
        # Check if analytics are available
        if not summary.get("has_sufficient_data", True):
            return {
                "has_sufficient_data": False,
                "reason": summary.get("reason", "no_activity")
            }
        
        return {
            "has_sufficient_data": True,
            "productive_minutes": summary.get("productive_minutes"),
            "idle_minutes": summary.get("idle_time_minutes"),
            "focus_score": summary.get("focus_score"),
            "productivity_breakdown": {
                "productive_percentage": summary.get("productivity_percentage"),
                "non_productive_percentage": summary.get("non_productive_percentage")
            },
            "top_distracting_domains": summary.get("top_domains", [])[:5],
            "longest_idle_session": summary.get("longest_focus_session_minutes")
        }
    
    def _load_comparison_context(self, db: Session, user: User, target_date: date) -> Dict[str, Any]:
        """
        Load context for comparison.
        
        Loads: metrics for target date and previous period
        """
        # Load current day
        current = self.aggregator.aggregate_daily_metrics(db, user, target_date)
        
        # Load previous day
        previous_date = target_date - timedelta(days=1)
        previous = self.aggregator.aggregate_daily_metrics(db, user, previous_date)
        
        # Check if either period has data
        has_current = current.get("has_sufficient_data", True)
        has_previous = previous.get("has_sufficient_data", True)
        
        if not has_current and not has_previous:
            return {
                "has_sufficient_data": False,
                "reason": "no_activity"
            }
        
        return {
            "has_sufficient_data": True,
            "current_date": {
                "date": target_date.isoformat(),
                "productive_minutes": current.get("productive_minutes") if has_current else None,
                "idle_minutes": current.get("idle_time_minutes") if has_current else None,
                "focus_score": current.get("focus_score") if has_current else None,
                "total_sessions": current.get("completed_sessions") if has_current else None,
                "has_data": has_current
            },
            "previous_date": {
                "date": previous_date.isoformat(),
                "productive_minutes": previous.get("productive_minutes") if has_previous else None,
                "idle_minutes": previous.get("idle_time_minutes") if has_previous else None,
                "focus_score": previous.get("focus_score") if has_previous else None,
                "total_sessions": previous.get("completed_sessions") if has_previous else None,
                "has_data": has_previous
            }
        }
    
    def _load_distraction_context(self, db: Session, user: User, target_date: date) -> Dict[str, Any]:
        """
        Load context for distraction analysis.
        
        Loads: tab switches, top distracting domains, entertainment time
        """
        summary = self.aggregator.aggregate_daily_metrics(db, user, target_date)
        
        # Check if analytics are available
        if not summary.get("has_sufficient_data", True):
            return {
                "has_sufficient_data": False,
                "reason": summary.get("reason", "no_activity")
            }
        
        return {
            "has_sufficient_data": True,
            "total_sessions": summary.get("completed_sessions"),
            "tab_switches": summary.get("tab_switches"),
            "top_distracting_domains": summary.get("top_domains", [])[:10],
            "entertainment_minutes": summary.get("entertainment_minutes"),
            "social_minutes": summary.get("social_minutes"),
            "total_distracting_minutes": summary.get("entertainment_minutes", 0) + summary.get("social_minutes", 0)
        }
    
    def _load_coding_habits_context(self, db: Session, user: User, target_date: date) -> Dict[str, Any]:
        """
        Load context for coding habits.
        
        Loads: development category, AI tools, LeetCode, GitHub, StackOverflow
        """
        summary = self.aggregator.aggregate_daily_metrics(db, user, target_date)
        
        # Check if analytics are available
        if not summary.get("has_sufficient_data", True):
            return {
                "has_sufficient_data": False,
                "reason": summary.get("reason", "no_activity")
            }
        
        # Get domain breakdown for coding sites
        domains = summary.get("top_domains", [])
        
        coding_domains = [d for d in domains if any(
            keyword in d.lower()
            for keyword in ["github", "leetcode", "stackoverflow", "gitlab", "bitbucket"]
        )]
        
        return {
            "has_sufficient_data": True,
            "development_minutes": summary.get("coding_minutes"),
            "ai_tools_minutes": summary.get("coding_minutes"),  # Combined for now
            "coding_domains": coding_domains[:5],
            "total_coding_time": summary.get("coding_minutes")
        }
    
    def _load_website_analysis_context(self, db: Session, user: User, target_date: date) -> Dict[str, Any]:
        """
        Load context for website analysis.
        
        Loads: top domains, domain categories
        """
        summary = self.aggregator.aggregate_daily_metrics(db, user, target_date)
        
        # Check if analytics are available
        if not summary.get("has_sufficient_data", True):
            return {
                "has_sufficient_data": False,
                "reason": summary.get("reason", "no_activity")
            }
        
        return {
            "has_sufficient_data": True,
            "top_domains": summary.get("top_domains", [])[:15],
            "total_unique_domains": len(summary.get("top_domains", [])),
            "most_visited_domain": summary.get("top_domains", [{}])[0] if summary.get("top_domains") else None
        }
    
    def _load_category_analysis_context(self, db: Session, user: User, target_date: date) -> Dict[str, Any]:
        """
        Load context for category analysis.
        
        Loads: category breakdown, time by category
        """
        summary = self.aggregator.aggregate_daily_metrics(db, user, target_date)
        
        # Check if analytics are available
        if not summary.get("has_sufficient_data", True):
            return {
                "has_sufficient_data": False,
                "reason": summary.get("reason", "no_activity")
            }
        
        return {
            "has_sufficient_data": True,
            "category_distribution": {
                "development": summary.get("coding_minutes"),
                "entertainment": summary.get("entertainment_minutes"),
                "social": summary.get("social_minutes")
            },
            "top_categories": summary.get("top_categories", [])[:10],
            "productivity_breakdown": {
                "productive_percentage": summary.get("productivity_percentage"),
                "neutral_percentage": summary.get("neutral_percentage"),
                "non_productive_percentage": summary.get("non_productive_percentage")
            }
        }
    
    def _load_historical_analysis_context(self, db: Session, user: User, target_date: date) -> Dict[str, Any]:
        """
        Load context for historical analysis (best day, worst day, etc.).
        
        Loads: daily breakdown for the past 30 days, best day, worst day
        """
        print(f"[HISTORICAL ANALYSIS CONTEXT] Loading for user {user.id}, target_date: {target_date}")
        
        # Load data for the past 30 days
        start_date = target_date - timedelta(days=30)
        print(f"[HISTORICAL ANALYSIS CONTEXT] Date range: {start_date} to {target_date}")
        
        weekly_summary = self.aggregator.aggregate_weekly_metrics(db, user, start_date, target_date)
        print(f"[HISTORICAL ANALYSIS CONTEXT] Weekly summary keys: {list(weekly_summary.keys())}")
        print(f"[HISTORICAL ANALYSIS CONTEXT] Weekly summary has_sufficient_data: {weekly_summary.get('has_sufficient_data')}")
        
        # Check if analytics are available
        if not weekly_summary.get("has_sufficient_data", True):
            print(f"[HISTORICAL ANALYSIS CONTEXT] No sufficient data available")
            return {
                "has_sufficient_data": False,
                "reason": weekly_summary.get("reason", "no_activity")
            }
        
        daily_breakdown = weekly_summary.get("daily_breakdown", [])
        print(f"[HISTORICAL ANALYSIS CONTEXT] Daily breakdown count: {len(daily_breakdown)}")
        print(f"[HISTORICAL ANALYSIS CONTEXT] Daily breakdown sample (first 3): {daily_breakdown[:3]}")
        
        # Filter to only days with actual data
        days_with_data = [day for day in daily_breakdown if day.get('focus_score', 0) > 0]
        print(f"[HISTORICAL ANALYSIS CONTEXT] Days with data (focus_score > 0): {len(days_with_data)}")
        
        if not days_with_data:
            print(f"[HISTORICAL ANALYSIS CONTEXT] No days with data found")
            return {
                "has_sufficient_data": False,
                "reason": "no_historical_data"
            }
        
        # Find best and worst days by focus score
        best_day = max(days_with_data, key=lambda x: x.get('focus_score', 0))
        worst_day = min(days_with_data, key=lambda x: x.get('focus_score', 0))
        
        # Find most productive day by productive minutes
        most_productive_day = max(days_with_data, key=lambda x: x.get('productive_minutes', 0))
        
        # Find day with most development time (if category breakdowns exist)
        most_development_day = None
        days_with_category_data = [day for day in days_with_data if day.get('category_breakdown')]
        print(f"[HISTORICAL ANALYSIS CONTEXT] Days with category breakdowns: {len(days_with_category_data)}")
        
        if days_with_category_data:
            most_development_day = max(
                days_with_category_data,
                key=lambda x: x.get('category_breakdown', {}).get('DEVELOPMENT', 0)
            )
            print(f"[HISTORICAL ANALYSIS CONTEXT] Most development day: {most_development_day}")
            print(f"[HISTORICAL ANALYSIS CONTEXT] Development minutes: {most_development_day.get('category_breakdown', {}).get('DEVELOPMENT', 0)}")
        
        result = {
            "has_sufficient_data": True,
            "daily_breakdown": days_with_data,
            "best_day": best_day,
            "worst_day": worst_day,
            "most_productive_day": most_productive_day,
            "most_development_day": most_development_day,
            "total_days_with_data": len(days_with_data),
            "date_range": {
                "start": start_date.isoformat(),
                "end": target_date.isoformat()
            }
        }
        
        print(f"[HISTORICAL ANALYSIS CONTEXT] Returning result with {len(days_with_data)} days")
        print(f"[HISTORICAL ANALYSIS CONTEXT] Best day: {best_day}")
        print(f"[HISTORICAL ANALYSIS CONTEXT] Most productive day: {most_productive_day}")
        print(f"[HISTORICAL ANALYSIS CONTEXT] Complete result: {result}")
        
        return result
    
    def _load_minimal_context(self, db: Session, user: User, target_date: date) -> Dict[str, Any]:
        """
        Load minimal context for general chat.
        
        Loads: basic summary only
        """
        summary = self.aggregator.aggregate_daily_metrics(db, user, target_date)
        
        # Check if analytics are available
        if not summary.get("has_sufficient_data", True):
            return {
                "has_sufficient_data": False,
                "reason": summary.get("reason", "no_activity")
            }
        
        return {
            "has_sufficient_data": True,
            "focus_score": summary.get("focus_score"),
            "productive_minutes": summary.get("productive_minutes")
        }
