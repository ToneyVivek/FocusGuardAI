"""
AI Context Builder

Converts aggregated analytics metrics into AI-friendly context for LLM consumption.
This ensures the AI receives structured, relevant information instead of raw data.
"""

from datetime import date
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.models import User
from app.ai.analytics_aggregator import AnalyticsAggregator


class AIContextBuilder:
    """
    Builds AI-friendly context from aggregated analytics metrics.
    
    Instead of sending thousands of raw browser events to the AI,
    this service transforms aggregated metrics into meaningful context.
    """
    
    def __init__(self):
        """Initialize with analytics aggregator."""
        self.aggregator = AnalyticsAggregator()
    
    def build_daily_context(
        self,
        db: Session,
        user: User,
        target_date: Optional[date] = None
    ) -> str:
        """
        Build context for daily AI analysis.
        
        Args:
            db: Database session
            user: Authenticated user
            target_date: Optional date to analyze (defaults to today)
            
        Returns:
            Formatted context string for AI
        """
        # Get aggregated metrics
        metrics = self.aggregator.aggregate_daily_metrics(db, user, target_date)
        
        # Check if analytics are available
        if not metrics.get('has_sufficient_data', True):
            return "No activity was recorded for this day. Unable to generate productivity context."
        
        # Format into readable context
        context = f"""Today's Productivity

Focus Score: {metrics['focus_score']}

Productive Time: {self._format_minutes(metrics['productive_minutes'])}

Entertainment: {self._format_minutes(metrics['entertainment_minutes'])}

Social Media: {self._format_minutes(metrics['social_minutes'])}

Coding: {self._format_minutes(metrics['coding_minutes'])}

Longest Focus Session: {metrics['longest_focus_session_minutes']} minutes

Average Focus Session: {metrics['average_focus_session_minutes']} minutes

Top Websites:
{self._format_list(metrics['top_domains'][:5])}

Top Categories:
{self._format_list(metrics['top_categories'][:5])}

Tab Switches: {metrics['tab_switches']}

Completed Sessions: {metrics['completed_sessions']}

Idle Time: {self._format_minutes(metrics['idle_time_minutes'])}

Productivity Percentage: {metrics['productivity_percentage']}%
"""
        return context.strip()
    
    def build_weekly_context(
        self,
        db: Session,
        user: User,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> str:
        """
        Build context for weekly AI analysis.
        
        Args:
            db: Database session
            user: Authenticated user
            start_date: Optional start date
            end_date: Optional end date
            
        Returns:
            Formatted context string for AI
        """
        # Get aggregated metrics
        metrics = self.aggregator.aggregate_weekly_metrics(db, user, start_date, end_date)
        
        # Check if analytics are available
        if not metrics.get('has_sufficient_data', True):
            return "No activity was recorded for this week. Unable to generate productivity context."
        
        # Format into readable context
        context = f"""Weekly Productivity

Focus Score: {metrics['focus_score']}

Average Focus Score: {metrics['average_focus_score']}

Total Productive Time: {self._format_minutes(metrics['productive_minutes'])}

Total Entertainment: {self._format_minutes(metrics['entertainment_minutes'])}

Total Social Media: {self._format_minutes(metrics['social_minutes'])}

Total Coding: {self._format_minutes(metrics['coding_minutes'])}

Longest Focus Session: {metrics['longest_focus_session_minutes']} minutes

Average Focus Session: {metrics['average_focus_session_minutes']} minutes

Top Websites:
{self._format_list(metrics['top_domains'][:10])}

Top Categories:
{self._format_list(metrics['top_categories'][:10])}

Tab Switches: {metrics['tab_switches']}

Completed Sessions: {metrics['completed_sessions']}

Idle Time: {self._format_minutes(metrics['idle_time_minutes'])}

Productivity Percentage: {metrics['productivity_percentage']}%
"""
        
        # Add best/worst day if available
        if metrics['best_day']:
            context += f"""
Best Day: {metrics['best_day']['date']} (Focus Score: {metrics['best_day']['focus_score']})

Worst Day: {metrics['worst_day']['date']} (Focus Score: {metrics['worst_day']['focus_score']})
"""
        
        return context.strip()
    
    def build_insights_context(
        self,
        db: Session,
        user: User,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> str:
        """
        Build context for AI-powered insights and recommendations.
        
        Args:
            db: Database session
            user: Authenticated user
            start_date: Optional start date
            end_date: Optional end date
            
        Returns:
            Formatted context string for AI insights
        """
        # Get aggregated metrics
        metrics = self.aggregator.aggregate_insights_metrics(db, user, start_date, end_date)
        
        # Format into readable context
        context = f"""Productivity Insights

Focus Score: {metrics['focus_score']}
Focus Score Trend: {metrics['focus_score_trend']}

Total Focus Time: {self._format_minutes(metrics['total_focus_time_minutes'])}

Time Distribution:
- Productive: {self._format_minutes(metrics['productive_minutes'])} ({metrics['productivity_percentage']}%)
- Neutral: {self._format_minutes(metrics['neutral_minutes'])}
- Non-Productive: {self._format_minutes(metrics['non_productive_minutes'])}

Most Productive Hour: {metrics['most_productive_hour']}:00

Most Productive Category: {metrics['most_productive_category'] or 'N/A'}

Average Uninterrupted Session: {metrics['average_uninterrupted_session_minutes']} minutes

Uninterrupted Sessions: {metrics['uninterrupted_session_count']}

Most Visited Productive Website: {metrics['most_visited_productive_website'] or 'N/A'} ({self._format_minutes(metrics['most_visited_productive_website_minutes'])})

Tab Switch Frequency: {metrics['tab_switch_frequency_per_hour']} per hour

Longest Focus Session: {metrics['longest_focus_session_minutes']} minutes

Average Focus Session: {metrics['average_focus_session_minutes']} minutes

Category Distribution:
{self._format_category_distribution(metrics['category_distribution'][:10])}

Domain Distribution:
{self._format_domain_distribution(metrics['domain_distribution'][:15])}
"""
        return context.strip()
    
    def _format_minutes(self, minutes: int) -> str:
        """Format minutes into hours and minutes."""
        if minutes < 60:
            return f"{minutes}m"
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours}h {mins}m" if mins > 0 else f"{hours}h"
    
    def _format_list(self, items: list) -> str:
        """Format list into bullet points."""
        return "\n".join([f"- {item}" for item in items])
    
    def _format_category_distribution(self, categories: list) -> str:
        """Format category distribution for context."""
        return "\n".join([
            f"- {cat['category']}: {self._format_minutes(cat['duration_minutes'])} ({cat['percentage']}%)"
            for cat in categories
        ])
    
    def _format_domain_distribution(self, domains: list) -> str:
        """Format domain distribution for context."""
        return "\n".join([
            f"- {dom['domain']}: {self._format_minutes(dom['duration_minutes'])} ({dom['session_count']} sessions)"
            for dom in domains
        ])
