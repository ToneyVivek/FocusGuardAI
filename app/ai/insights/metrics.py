"""
Derived metrics calculation.

Converts raw analytics into meaningful derived metrics that AI can reason about.
"""

from typing import Dict, List, Optional
from statistics import mean, stdev
from app.ai.insights.schemas import DerivedMetrics


class MetricsCalculator:
    """
    Calculates derived metrics from raw analytics data.
    
    These metrics are more meaningful for AI reasoning than raw numbers.
    """
    
    @staticmethod
    def calculate_derived_metrics(raw_metrics: Dict) -> DerivedMetrics:
        """
        Calculate all derived metrics from raw analytics.
        
        Args:
            raw_metrics: Dictionary of raw analytics data
            
        Returns:
            DerivedMetrics with calculated metrics
        """
        # Extract raw values
        tab_switches = raw_metrics.get("tab_switches", 0)
        total_minutes = raw_metrics.get("total_minutes", 1)
        productive_minutes = raw_metrics.get("productive_minutes", 0)
        idle_minutes = raw_metrics.get("idle_minutes", 0)
        coding_minutes = raw_metrics.get("coding_minutes", 0)
        ai_tool_minutes = raw_metrics.get("ai_tool_minutes", 0)
        entertainment_minutes = raw_metrics.get("entertainment_minutes", 0)
        social_minutes = raw_metrics.get("social_minutes", 0)
        total_sessions = raw_metrics.get("total_sessions", 1)
        longest_session = raw_metrics.get("longest_focus_session", 0)
        focus_score = raw_metrics.get("focus_score", 0)
        
        session_lengths = raw_metrics.get("session_lengths", [])
        hourly_data = raw_metrics.get("hourly_productivity", {})
        
        # Calculate derived metrics
        tab_switches_per_hour = MetricsCalculator._calculate_tab_switches_per_hour(
            tab_switches, total_minutes
        )
        
        average_session_length = MetricsCalculator._calculate_average_session_length(
            total_minutes, total_sessions
        )
        
        deep_work_ratio = MetricsCalculator._calculate_deep_work_ratio(
            session_lengths, total_minutes
        )
        
        productive_ratio = MetricsCalculator._calculate_productive_ratio(
            productive_minutes, total_minutes
        )
        
        focus_efficiency = MetricsCalculator._calculate_focus_efficiency(
            focus_score, productive_ratio
        )
        
        coding_consistency = MetricsCalculator._calculate_coding_consistency(
            coding_minutes, total_minutes, session_lengths
        )
        
        ai_tool_dependency = MetricsCalculator._calculate_ai_tool_dependency(
            ai_tool_minutes, coding_minutes
        )
        
        entertainment_balance = MetricsCalculator._calculate_entertainment_balance(
            entertainment_minutes, total_minutes
        )
        
        # Advanced qualitative metrics
        context_switching_severity = MetricsCalculator._assess_context_switching_severity(
            tab_switches_per_hour
        )
        
        deep_work_quality = MetricsCalculator._assess_deep_work_quality(
            longest_session, deep_work_ratio
        )
        
        coding_intensity = MetricsCalculator._assess_coding_intensity(
            coding_minutes, total_minutes
        )
        
        attention_fragmentation = MetricsCalculator._assess_attention_fragmentation(
            tab_switches_per_hour, session_lengths
        )
        
        burnout_risk = MetricsCalculator._assess_burnout_risk(
            total_minutes, productive_ratio, focus_score
        )
        
        focus_stability = MetricsCalculator._assess_focus_stability(
            session_lengths
        )
        
        recovery_quality = MetricsCalculator._assess_recovery_quality(
            idle_minutes, total_minutes
        )
        
        session_efficiency = MetricsCalculator._assess_session_efficiency(
            productive_minutes, total_sessions
        )
        
        website_diversity = MetricsCalculator._assess_website_diversity(
            raw_metrics.get("unique_websites", 0)
        )
        
        task_fragmentation = MetricsCalculator._assess_task_fragmentation(
            total_sessions, total_minutes
        )
        
        peak_performance_window = MetricsCalculator._identify_peak_performance_window(
            hourly_data
        )
        
        return DerivedMetrics(
            tab_switches_per_hour=tab_switches_per_hour,
            average_session_length=average_session_length,
            deep_work_ratio=deep_work_ratio,
            productive_ratio=productive_ratio,
            focus_efficiency=focus_efficiency,
            coding_consistency=coding_consistency,
            ai_tool_dependency=ai_tool_dependency,
            entertainment_balance=entertainment_balance,
            context_switching_severity=context_switching_severity,
            deep_work_quality=deep_work_quality,
            coding_intensity=coding_intensity,
            attention_fragmentation=attention_fragmentation,
            burnout_risk=burnout_risk,
            focus_stability=focus_stability,
            recovery_quality=recovery_quality,
            session_efficiency=session_efficiency,
            website_diversity=website_diversity,
            task_fragmentation=task_fragmentation,
            peak_performance_window=peak_performance_window
        )
    
    @staticmethod
    def _calculate_tab_switches_per_hour(tab_switches: int, total_minutes: int) -> float:
        """Calculate tab switches per hour."""
        if total_minutes <= 0:
            return 0.0
        return (tab_switches / total_minutes) * 60
    
    @staticmethod
    def _calculate_average_session_length(total_minutes: int, total_sessions: int) -> float:
        """Calculate average session length in minutes."""
        if total_sessions <= 0:
            return 0.0
        return total_minutes / total_sessions
    
    @staticmethod
    def _calculate_deep_work_ratio(session_lengths: List[int], total_minutes: int) -> float:
        """
        Calculate ratio of deep work time (sessions >= 20 min) to total time.
        """
        if total_minutes <= 0:
            return 0.0
        
        deep_work_minutes = sum(length for length in session_lengths if length >= 20)
        return deep_work_minutes / total_minutes
    
    @staticmethod
    def _calculate_productive_ratio(productive_minutes: int, total_minutes: int) -> float:
        """Calculate ratio of productive time to total time."""
        if total_minutes <= 0:
            return 0.0
        return productive_minutes / total_minutes
    
    @staticmethod
    def _calculate_focus_efficiency(focus_score: float, productive_ratio: float) -> float:
        """
        Calculate focus efficiency score (0-100).
        
        Combines focus score and productive ratio.
        """
        return (focus_score * 0.6 + productive_ratio * 100 * 0.4)
    
    @staticmethod
    def _calculate_coding_consistency(
        coding_minutes: int, 
        total_minutes: int, 
        session_lengths: List[int]
    ) -> float:
        """
        Calculate coding consistency score (0-100).
        
        Based on coding ratio and session consistency.
        """
        if total_minutes <= 0:
            return 0.0
        
        coding_ratio = coding_minutes / total_minutes
        
        # Calculate session variance (lower is more consistent)
        if len(session_lengths) > 1:
            session_variance = stdev(session_lengths) if len(session_lengths) > 1 else 0
            consistency_score = max(0, 100 - session_variance * 2)
        else:
            consistency_score = 50
        
        # Combine coding ratio and consistency
        return (coding_ratio * 100 * 0.7 + consistency_score * 0.3)
    
    @staticmethod
    def _calculate_ai_tool_dependency(ai_tool_minutes: int, coding_minutes: int) -> float:
        """
        Calculate AI tool dependency score (0-100).
        
        Higher score means more dependency on AI tools.
        """
        if coding_minutes <= 0:
            return 0.0
        return (ai_tool_minutes / coding_minutes) * 100
    
    @staticmethod
    def _calculate_entertainment_balance(
        entertainment_minutes: int, 
        total_minutes: int
    ) -> float:
        """
        Calculate entertainment balance score (0-100).
        
        Higher score means more entertainment time.
        """
        if total_minutes <= 0:
            return 0.0
        return (entertainment_minutes / total_minutes) * 100
    
    @staticmethod
    def _assess_context_switching_severity(tab_switches_per_hour: float) -> str:
        """Assess severity of context switching."""
        if tab_switches_per_hour >= 200:
            return "severe"
        elif tab_switches_per_hour >= 100:
            return "high"
        elif tab_switches_per_hour >= 50:
            return "moderate"
        else:
            return "low"
    
    @staticmethod
    def _assess_deep_work_quality(longest_session: int, deep_work_ratio: float) -> str:
        """Assess quality of deep work."""
        if longest_session >= 45 and deep_work_ratio >= 0.6:
            return "excellent"
        elif longest_session >= 30 and deep_work_ratio >= 0.4:
            return "good"
        elif longest_session >= 15 and deep_work_ratio >= 0.2:
            return "fair"
        elif longest_session >= 5:
            return "poor"
        else:
            return "none"
    
    @staticmethod
    def _assess_coding_intensity(coding_minutes: int, total_minutes: int) -> str:
        """Assess intensity of coding activity."""
        if total_minutes <= 0:
            return "none"
        
        coding_ratio = coding_minutes / total_minutes
        
        if coding_ratio >= 0.7:
            return "very_high"
        elif coding_ratio >= 0.5:
            return "high"
        elif coding_ratio >= 0.3:
            return "moderate"
        elif coding_ratio >= 0.1:
            return "low"
        else:
            return "none"
    
    @staticmethod
    def _assess_attention_fragmentation(
        tab_switches_per_hour: float, 
        session_lengths: List[int]
    ) -> str:
        """Assess level of attention fragmentation."""
        if tab_switches_per_hour >= 200:
            return "severe"
        elif tab_switches_per_hour >= 100:
            return "high"
        elif tab_switches_per_hour >= 50:
            return "moderate"
        elif len(session_lengths) > 0 and mean(session_lengths) < 10:
            return "moderate"
        else:
            return "low"
    
    @staticmethod
    def _assess_burnout_risk(
        total_minutes: int, 
        productive_ratio: float, 
        focus_score: float
    ) -> str:
        """Assess risk of burnout."""
        # Long hours with low productivity
        if total_minutes > 480 and productive_ratio < 0.5:
            return "high"
        elif total_minutes > 600:
            return "high"
        elif total_minutes > 480 and productive_ratio < 0.6:
            return "moderate"
        elif focus_score < 40 and productive_ratio < 0.5:
            return "moderate"
        else:
            return "low"
    
    @staticmethod
    def _assess_focus_stability(session_lengths: List[int]) -> str:
        """Assess stability of focus across sessions."""
        if len(session_lengths) <= 1:
            return "unknown"
        
        session_variance = stdev(session_lengths) if len(session_lengths) > 1 else 0
        
        if session_variance < 10:
            return "stable"
        elif session_variance < 20:
            return "moderately_stable"
        elif session_variance < 30:
            return "variable"
        else:
            return "unstable"
    
    @staticmethod
    def _assess_recovery_quality(idle_minutes: int, total_minutes: int) -> str:
        """Assess quality of recovery periods."""
        if total_minutes <= 0:
            return "unknown"
        
        idle_ratio = idle_minutes / total_minutes
        
        # Ideal idle ratio is around 0.1-0.2 (10-20% breaks)
        if 0.1 <= idle_ratio <= 0.2:
            return "good"
        elif idle_ratio < 0.1:
            return "insufficient"
        elif idle_ratio <= 0.3:
            return "adequate"
        else:
            return "excessive"
    
    @staticmethod
    def _assess_session_efficiency(productive_minutes: int, total_sessions: int) -> str:
        """Assess efficiency of sessions."""
        if total_sessions <= 0:
            return "unknown"
        
        productive_per_session = productive_minutes / total_sessions
        
        if productive_per_session >= 30:
            return "high"
        elif productive_per_session >= 20:
            return "good"
        elif productive_per_session >= 10:
            return "moderate"
        else:
            return "low"
    
    @staticmethod
    def _assess_website_diversity(unique_websites: int) -> str:
        """Assess diversity of websites visited."""
        if unique_websites >= 50:
            return "very_high"
        elif unique_websites >= 30:
            return "high"
        elif unique_websites >= 15:
            return "moderate"
        elif unique_websites >= 5:
            return "low"
        else:
            return "very_low"
    
    @staticmethod
    def _assess_task_fragmentation(total_sessions: int, total_minutes: int) -> str:
        """Assess level of task fragmentation."""
        if total_minutes <= 0:
            return "unknown"
        
        sessions_per_hour = (total_sessions / total_minutes) * 60
        
        if sessions_per_hour >= 10:
            return "severe"
        elif sessions_per_hour >= 6:
            return "high"
        elif sessions_per_hour >= 3:
            return "moderate"
        else:
            return "low"
    
    @staticmethod
    def _identify_peak_performance_window(hourly_data: Dict[int, float]) -> str:
        """
        Identify peak performance time window.
        
        Args:
            hourly_data: Dict mapping hour (0-23) to productivity score
            
        Returns:
            String describing peak window
        """
        if not hourly_data:
            return "unknown"
        
        # Find hours with highest productivity
        sorted_hours = sorted(hourly_data.items(), key=lambda x: x[1], reverse=True)
        top_hours = [hour for hour, score in sorted_hours if score >= 0.7]
        
        if not top_hours:
            return "no_clear_peak"
        
        avg_peak = mean(top_hours)
        
        if 5 <= avg_peak < 12:
            return "morning"
        elif 12 <= avg_peak < 17:
            return "afternoon"
        elif 17 <= avg_peak < 21:
            return "evening"
        else:
            return "night"
