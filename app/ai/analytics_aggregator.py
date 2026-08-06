"""
Analytics Aggregation Layer for AI

Transforms raw analytics data into AI-friendly aggregated metrics.
The AI service consumes these aggregated objects, not database models.
"""

from datetime import date, datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from app.models.models import User, ProductivityClassification
from app.analytics.services.analytics_service import (
    get_user_summary,
    get_user_productivity,
    get_user_category_breakdown,
    get_user_domain_breakdown,
    get_user_timeline,
)


class AnalyticsAggregator:
    """
    Aggregates analytics data into AI-friendly metrics.
    
    This layer sits between the analytics service and the AI context builder,
    transforming complex data into simple, consumable metrics.
    """
    
    def _check_analytics_availability(self, summary) -> bool:
        """
        Check if there's sufficient analytics data to provide meaningful insights.
        
        Args:
            summary: UserSummaryResponseV2 object from analytics service
            
        Returns:
            True if sufficient data is available, False otherwise
        """
        # Check if there's any focus time recorded
        total_focus_time = getattr(summary.metrics, 'total_focus_time', 0) or 0
        
        # Check if there are any completed sessions
        completed_sessions = getattr(summary.metrics, 'completed_sessions', 0) or 0
        
        # Check if there are any activity events
        activity_events = getattr(summary.metrics, 'activity_events', 0) or 0
        
        # Consider data insufficient if:
        # - No focus time recorded AND no sessions completed
        # - This indicates no browser activity was tracked
        has_data = total_focus_time > 0 or completed_sessions > 0 or activity_events > 0
        
        return has_data
    
    def aggregate_daily_metrics(
        self,
        db: Session,
        user: User,
        target_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Aggregate daily analytics metrics for AI consumption.
        
        Args:
            db: Database session
            user: Authenticated user
            target_date: Optional date to analyze (defaults to today)
            
        Returns:
            Aggregated metrics dictionary with analytics availability flag
        """
        # Validate date parameter
        if target_date is not None and not isinstance(target_date, date):
            raise ValueError(
                f"target_date must be a datetime.date object, got {type(target_date).__name__}. "
                f"Value: {target_date}"
            )
        # Get user summary for the date
        summary = get_user_summary(
            db=db,
            user=user,
            start_date=target_date,
            end_date=target_date
        )
        
        # Check if there's sufficient data
        has_sufficient_data = self._check_analytics_availability(summary)
        
        if not has_sufficient_data:
            print(f"[ANALYTICS AGGREGATOR] Insufficient data for user {user.id} on {target_date}")
            return {
                "date": target_date.isoformat() if target_date else date.today().isoformat(),
                "has_sufficient_data": False,
                "reason": "no_activity"
            }
        
        # Get productivity breakdown
        productivity = get_user_productivity(
            db=db,
            user=user,
            start_date=target_date,
            end_date=target_date
        )
        
        # Get category breakdown
        categories = get_user_category_breakdown(
            db=db,
            user=user,
            start_date=target_date,
            end_date=target_date
        )
        
        # Get domain breakdown (top 10)
        domains = get_user_domain_breakdown(
            db=db,
            user=user,
            start_date=target_date,
            end_date=target_date,
            limit=10
        )
        
        # Get timeline for session analysis
        timeline = get_user_timeline(
            db=db,
            user=user,
            start_date=target_date,
            end_date=target_date,
            limit=100
        )
        
        # Calculate session metrics
        session_durations = [getattr(item, 'duration_seconds', 0) for item in timeline.items] if timeline.items else []
        longest_session = max(session_durations) if session_durations else 0
        average_session = sum(session_durations) / len(session_durations) if session_durations else 0
        
        # Calculate category-specific minutes
        category_minutes = {}
        for cat in categories.categories:
            category_minutes[cat.category] = cat.duration_seconds / 60
        
        # Extract specific categories
        productive_minutes = productivity.productive.duration_seconds / 60
        neutral_minutes = productivity.neutral.duration_seconds / 60
        non_productive_minutes = productivity.non_productive.duration_seconds / 60
        
        # Map common categories
        entertainment_minutes = category_minutes.get('ENTERTAINMENT', 0)
        social_minutes = category_minutes.get('SOCIAL_MEDIA', 0)
        coding_minutes = category_minutes.get('DEVELOPMENT', 0)
        other_minutes = (
            productive_minutes + neutral_minutes + non_productive_minutes
            - entertainment_minutes - social_minutes - coding_minutes
        )
        other_minutes = max(0, other_minutes)
        
        return {
            "date": target_date.isoformat() if target_date else date.today().isoformat(),
            "has_sufficient_data": True,
            "productive_minutes": round(productive_minutes),
            "neutral_minutes": round(neutral_minutes),
            "non_productive_minutes": round(non_productive_minutes),
            "entertainment_minutes": round(entertainment_minutes),
            "social_minutes": round(social_minutes),
            "coding_minutes": round(coding_minutes),
            "other_minutes": round(other_minutes),
            "focus_score": summary.focus_score.score,
            "focus_score_trend": None,  # Trend not available in current schema
            "top_domains": [d.domain for d in domains.domains],
            "top_categories": [c.category for c in categories.categories],
            "longest_focus_session_minutes": round(longest_session / 60),
            "average_focus_session_minutes": round(average_session / 60),
            "tab_switches": summary.metrics.activity_events,
            "completed_sessions": summary.metrics.completed_sessions,
            "idle_time_minutes": round(summary.metrics.idle_time / 60),
            "idle_sessions": summary.metrics.idle_sessions,
            "productivity_percentage": round(productivity.productive.percentage),
            "neutral_percentage": round(productivity.neutral.percentage),
            "non_productive_percentage": round(productivity.non_productive.percentage),
            "total_focus_time_minutes": round(summary.metrics.total_focus_time / 60),
            "session_lengths": session_durations,  # Add session lengths for insights analyzer
        }
        print(f"[ANALYTICS AGGREGATOR] Returning metrics with session_lengths: {len(session_durations)} sessions")
    
    def aggregate_weekly_metrics(
        self,
        db: Session,
        user: User,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Aggregate weekly analytics metrics for AI consumption.
        
        Args:
            db: Database session
            user: Authenticated user
            start_date: Optional start date
            end_date: Optional end date
            
        Returns:
            Aggregated metrics dictionary with analytics availability flag
        """
        # Validate date parameters
        if start_date is not None and not isinstance(start_date, date):
            raise ValueError(
                f"start_date must be a datetime.date object, got {type(start_date).__name__}. "
                f"Value: {start_date}"
            )
        if end_date is not None and not isinstance(end_date, date):
            raise ValueError(
                f"end_date must be a datetime.date object, got {type(end_date).__name__}. "
                f"Value: {end_date}"
            )
        # Get user summary for the week
        summary = get_user_summary(
            db=db,
            user=user,
            start_date=start_date,
            end_date=end_date
        )
        
        # Check if there's sufficient data
        has_sufficient_data = self._check_analytics_availability(summary)
        
        if not has_sufficient_data:
            print(f"[ANALYTICS AGGREGATOR] Insufficient data for user {user.id} from {start_date} to {end_date}")
            return {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
                "has_sufficient_data": False,
                "reason": "no_activity"
            }
        
        # Get productivity breakdown
        productivity = get_user_productivity(
            db=db,
            user=user,
            start_date=start_date,
            end_date=end_date
        )
        
        # Get category breakdown
        categories = get_user_category_breakdown(
            db=db,
            user=user,
            start_date=start_date,
            end_date=end_date
        )
        
        # Get domain breakdown (top 15 for weekly)
        domains = get_user_domain_breakdown(
            db=db,
            user=user,
            start_date=start_date,
            end_date=end_date,
            limit=15
        )
        
        # Get timeline for session analysis
        timeline = get_user_timeline(
            db=db,
            user=user,
            start_date=start_date,
            end_date=end_date,
            limit=200
        )
        
        # Calculate session metrics
        session_durations = [getattr(item, 'duration_seconds', 0) for item in timeline.items] if timeline.items else []
        longest_session = max(session_durations) if session_durations else 0
        average_session = sum(session_durations) / len(session_durations) if session_durations else 0
        
        # Calculate category-specific minutes
        category_minutes = {}
        for cat in categories.categories:
            category_minutes[cat.category] = cat.duration_seconds / 60
        
        # Extract specific categories
        productive_minutes = productivity.productive.duration_seconds / 60
        neutral_minutes = productivity.neutral.duration_seconds / 60
        non_productive_minutes = productivity.non_productive.duration_seconds / 60
        
        # Map common categories
        entertainment_minutes = category_minutes.get('ENTERTAINMENT', 0)
        social_minutes = category_minutes.get('SOCIAL_MEDIA', 0)
        coding_minutes = category_minutes.get('DEVELOPMENT', 0)
        other_minutes = (
            productive_minutes + neutral_minutes + non_productive_minutes
            - entertainment_minutes - social_minutes - coding_minutes
        )
        other_minutes = max(0, other_minutes)
        
        # Calculate daily breakdown if we have date range
        daily_breakdown = []
        if start_date and end_date:
            print(f"[ANALYTICS AGGREGATOR] Building daily breakdown from {start_date} to {end_date}")
            current_date = start_date
            while current_date <= end_date:
                day_summary = get_user_summary(
                    db=db,
                    user=user,
                    start_date=current_date,
                    end_date=current_date
                )
                
                # Get category breakdown for this specific day
                day_categories = get_user_category_breakdown(
                    db=db,
                    user=user,
                    start_date=current_date,
                    end_date=current_date
                )
                
                # Build category minutes dict for this day
                category_minutes = {}
                for cat in day_categories.categories:
                    category_minutes[cat.category] = round(cat.duration_seconds / 60)
                
                daily_breakdown.append({
                    "date": current_date.isoformat(),
                    "focus_score": day_summary.focus_score.score,
                    "productive_minutes": round(day_summary.metrics.total_focus_time / 60),
                    "category_breakdown": category_minutes,
                })
                current_date += timedelta(days=1)
            print(f"[ANALYTICS AGGREGATOR] Daily breakdown built: {len(daily_breakdown)} days")
            print(f"[ANALYTICS AGGREGATOR] Daily breakdown sample (first 3): {daily_breakdown[:3]}")
        else:
            print(f"[ANALYTICS AGGREGATOR] No date range provided, skipping daily breakdown")
        
        # Find best and worst days
        best_day = None
        worst_day = None
        if daily_breakdown:
            best_day = max(daily_breakdown, key=lambda x: x['focus_score'])
            worst_day = min(daily_breakdown, key=lambda x: x['focus_score'])
        
        return {
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "has_sufficient_data": True,
            "productive_minutes": round(productive_minutes),
            "neutral_minutes": round(neutral_minutes),
            "non_productive_minutes": round(non_productive_minutes),
            "entertainment_minutes": round(entertainment_minutes),
            "social_minutes": round(social_minutes),
            "coding_minutes": round(coding_minutes),
            "other_minutes": round(other_minutes),
            "focus_score": summary.focus_score.score,
            "focus_score_trend": None,  # Trend not available in current schema
            "average_focus_score": round(sum(d['focus_score'] for d in daily_breakdown) / len(daily_breakdown)) if daily_breakdown else summary.focus_score.score,
            "top_domains": [d.domain for d in domains.domains],
            "top_categories": [c.category for c in categories.categories],
            "longest_focus_session_minutes": round(longest_session / 60),
            "average_focus_session_minutes": round(average_session / 60),
            "tab_switches": summary.metrics.activity_events,
            "completed_sessions": summary.metrics.completed_sessions,
            "idle_time_minutes": round(summary.metrics.idle_time / 60),
            "idle_sessions": summary.metrics.idle_sessions,
            "productivity_percentage": round(productivity.productive.percentage),
            "neutral_percentage": round(productivity.neutral.percentage),
            "non_productive_percentage": round(productivity.non_productive.percentage),
            "total_focus_time_minutes": round(summary.metrics.total_focus_time / 60),
            "daily_breakdown": daily_breakdown,
            "best_day": best_day,
            "worst_day": worst_day,
        }
    
    def aggregate_insights_metrics(
        self,
        db: Session,
        user: User,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Aggregate metrics specifically for AI insights generation.
        
        Args:
            db: Database session
            user: Authenticated user
            start_date: Optional start date
            end_date: Optional end date
            
        Returns:
            Aggregated metrics dictionary for insights
        """
        # Validate date parameters
        if start_date is not None and not isinstance(start_date, date):
            raise ValueError(
                f"start_date must be a datetime.date object, got {type(start_date).__name__}. "
                f"Value: {start_date}"
            )
        if end_date is not None and not isinstance(end_date, date):
            raise ValueError(
                f"end_date must be a datetime.date object, got {type(end_date).__name__}. "
                f"Value: {end_date}"
            )
        # Get user summary
        summary = get_user_summary(
            db=db,
            user=user,
            start_date=start_date,
            end_date=end_date
        )
        
        # Get productivity breakdown
        productivity = get_user_productivity(
            db=db,
            user=user,
            start_date=start_date,
            end_date=end_date
        )
        
        # Get category breakdown
        categories = get_user_category_breakdown(
            db=db,
            user=user,
            start_date=start_date,
            end_date=end_date
        )
        
        # Get domain breakdown (top 20 for insights)
        domains = get_user_domain_breakdown(
            db=db,
            user=user,
            start_date=start_date,
            end_date=end_date,
            limit=20
        )
        
        # Get timeline for pattern analysis
        timeline = get_user_timeline(
            db=db,
            user=user,
            start_date=start_date,
            end_date=end_date,
            limit=500
        )
        
        # Calculate session metrics
        session_durations = [getattr(item, 'duration_seconds', 0) for item in timeline.items] if timeline.items else []
        longest_session = max(session_durations) if session_durations else 0
        average_session = sum(session_durations) / len(session_durations) if session_durations else 0
        
        # Calculate uninterrupted sessions (sessions > 30 minutes)
        uninterrupted_sessions = [d for d in session_durations if d > 1800]
        average_uninterrupted = sum(uninterrupted_sessions) / len(uninterrupted_sessions) if uninterrupted_sessions else 0
        
        # Find most productive category
        most_productive_category = max(categories.categories, key=lambda x: x.duration_seconds) if categories.categories else None
        
        # Find most visited productive website
        productive_domains = [d for d in domains.domains if d.duration_seconds > 0]
        most_visited_productive = max(productive_domains, key=lambda x: x.duration_seconds) if productive_domains else None
        
        # Calculate tab-switch frequency (switches per hour)
        total_hours = summary.metrics.total_focus_time / 3600 if summary.metrics.total_focus_time > 0 else 1
        tab_switch_frequency = summary.metrics.activity_events / total_hours if total_hours > 0 else 0
        
        # Calculate hour-by-hour productivity (if timeline has timestamps)
        hourly_productivity = {}
        for item in timeline.items:
            hour = getattr(item, 'start_time', None).hour if hasattr(item, 'start_time') and item.start_time else 0
            if hour not in hourly_productivity:
                hourly_productivity[hour] = 0
            hourly_productivity[hour] += getattr(item, 'duration_seconds', 0)
        
        most_productive_hour = max(hourly_productivity, key=hourly_productivity.get) if hourly_productivity else None
        
        return {
            "focus_score": summary.focus_score.score,
            "focus_score_trend": None,  # Trend not available in current schema
            "total_focus_time_minutes": round(summary.metrics.total_focus_time / 60),
            "productive_minutes": round(productivity.productive.duration_seconds / 60),
            "neutral_minutes": round(productivity.neutral.duration_seconds / 60),
            "non_productive_minutes": round(productivity.non_productive.duration_seconds / 60),
            "productivity_percentage": round(productivity.productive.percentage),
            "neutral_percentage": round(productivity.neutral.percentage),
            "non_productive_percentage": round(productivity.non_productive.percentage),
            "most_productive_hour": most_productive_hour,
            "most_productive_category": most_productive_category.category if most_productive_category else None,
            "average_uninterrupted_session_minutes": round(average_uninterrupted / 60),
            "uninterrupted_session_count": len(uninterrupted_sessions),
            "most_visited_productive_website": most_visited_productive.domain if most_visited_productive else None,
            "most_visited_productive_website_minutes": round(most_visited_productive.duration_seconds / 60) if most_visited_productive else 0,
            "tab_switch_frequency_per_hour": round(tab_switch_frequency, 1),
            "total_tab_switches": summary.metrics.activity_events,
            "longest_focus_session_minutes": round(longest_session / 60),
            "average_focus_session_minutes": round(average_session / 60),
            "category_distribution": [
                {
                    "category": cat.category,
                    "duration_minutes": round(cat.duration_seconds / 60),
                    "percentage": cat.percentage,
                    "session_count": cat.session_count
                }
                for cat in categories.categories
            ],
            "domain_distribution": [
                {
                    "domain": dom.domain,
                    "duration_minutes": round(dom.duration_seconds / 60),
                    "session_count": dom.session_count
                }
                for dom in domains.domains
            ],
        }
