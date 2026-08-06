"""
Deterministic business rules for insights generation.

No AI involved - pure logic-based rules for converting metrics into insights.
"""

from typing import Dict, List, Optional
from app.ai.insights.schemas import (
    MainIssue,
    DeepWorkQuality,
    AttentionPattern,
    CodingIntensity,
    AIDependency,
    DistractionLevel,
    EnergyPattern,
    WorkRhythm,
    RiskLevel
)


class BusinessRules:
    """
    Deterministic business rules for converting raw metrics into insights.
    
    All rules are threshold-based and deterministic - no AI involved.
    """
    
    # Thresholds
    HIGH_TAB_SWITCHES = 300
    VERY_HIGH_TAB_SWITCHES = 500
    LOW_SESSION_LENGTH = 5
    GOOD_SESSION_LENGTH = 20
    HIGH_PRODUCTIVE_RATIO = 0.8
    LOW_PRODUCTIVE_RATIO = 0.4
    HIGH_DEEP_WORK_RATIO = 0.6
    LOW_DEEP_WORK_RATIO = 0.2
    
    @staticmethod
    def determine_main_issue(metrics: Dict) -> MainIssue:
        """
        Determine the primary productivity issue based on metrics.
        
        Priority order:
        1. High context switching
        2. Low deep work
        3. High distraction
        4. Low coding intensity
        5. High entertainment
        6. Burnout risk
        7. Poor time management
        8. Inconsistent schedule
        """
        tab_switches = metrics.get("tab_switches", 0)
        longest_session = metrics.get("longest_focus_session", 0)
        productive_ratio = metrics.get("productive_ratio", 0)
        deep_work_ratio = metrics.get("deep_work_ratio", 0)
        coding_minutes = metrics.get("coding_minutes", 0)
        entertainment_minutes = metrics.get("entertainment_minutes", 0)
        total_minutes = metrics.get("total_minutes", 1)
        
        # High context switching (highest priority)
        if tab_switches > BusinessRules.VERY_HIGH_TAB_SWITCHES:
            return MainIssue.HIGH_CONTEXT_SWITCHING
        elif tab_switches > BusinessRules.HIGH_TAB_SWITCHES:
            # Check if other issues are more severe
            if longest_session < BusinessRules.LOW_SESSION_LENGTH:
                return MainIssue.LOW_DEEP_WORK
            return MainIssue.HIGH_CONTEXT_SWITCHING
        
        # Low deep work
        if longest_session < BusinessRules.LOW_SESSION_LENGTH:
            return MainIssue.LOW_DEEP_WORK
        
        # High distraction
        if productive_ratio < BusinessRules.LOW_PRODUCTIVE_RATIO:
            return MainIssue.HIGH_DISTRACTION
        
        # Low coding intensity
        if coding_minutes / total_minutes < 0.3 and total_minutes > 60:
            return MainIssue.LOW_CODING_INTENSITY
        
        # High entertainment
        if entertainment_minutes / total_minutes > 0.4 and total_minutes > 60:
            return MainIssue.HIGH_ENTERTAINMENT
        
        # Burnout risk (long hours with low productivity)
        if total_minutes > 480 and productive_ratio < 0.5:
            return MainIssue.BURNOUT_RISK
        
        # Poor time management
        if productive_ratio < 0.6:
            return MainIssue.POOR_TIME_MANAGEMENT
        
        return MainIssue.NO_SIGNIFICANT_ISSUE
    
    @staticmethod
    def determine_deep_work_quality(metrics: Dict) -> DeepWorkQuality:
        """
        Determine deep work quality based on session length and consistency.
        """
        longest_session = metrics.get("longest_focus_session", 0)
        average_session = metrics.get("average_session_length", 0)
        deep_work_ratio = metrics.get("deep_work_ratio", 0)
        
        if longest_session >= 45 and average_session >= 25 and deep_work_ratio >= BusinessRules.HIGH_DEEP_WORK_RATIO:
            return DeepWorkQuality.EXCELLENT
        elif longest_session >= 30 and average_session >= 15 and deep_work_ratio >= 0.4:
            return DeepWorkQuality.GOOD
        elif longest_session >= 15 and average_session >= 10 and deep_work_ratio >= BusinessRules.LOW_DEEP_WORK_RATIO:
            return DeepWorkQuality.FAIR
        elif longest_session >= BusinessRules.LOW_SESSION_LENGTH:
            return DeepWorkQuality.POOR
        else:
            return DeepWorkQuality.NONE
    
    @staticmethod
    def determine_attention_pattern(metrics: Dict) -> AttentionPattern:
        """
        Determine attention pattern based on tab switches and session consistency.
        """
        tab_switches = metrics.get("tab_switches", 0)
        total_minutes = metrics.get("total_minutes", 1)
        tab_switches_per_hour = (tab_switches / total_minutes) * 60 if total_minutes > 0 else 0
        
        session_variance = metrics.get("session_variance", 0)
        
        if tab_switches_per_hour < 50 and session_variance < 10:
            return AttentionPattern.FOCUSED
        elif tab_switches_per_hour < 100 and session_variance < 20:
            return AttentionPattern.CONSISTENT
        elif tab_switches_per_hour < 200:
            return AttentionPattern.FRAGMENTED
        else:
            return AttentionPattern.SCATTERED
    
    @staticmethod
    def determine_coding_intensity(metrics: Dict) -> CodingIntensity:
        """
        Determine coding intensity based on coding time and consistency.
        """
        coding_minutes = metrics.get("coding_minutes", 0)
        total_minutes = metrics.get("total_minutes", 1)
        coding_ratio = coding_minutes / total_minutes if total_minutes > 0 else 0
        
        coding_sessions = metrics.get("coding_sessions", 0)
        
        if coding_ratio >= 0.7 and coding_sessions >= 5:
            return CodingIntensity.HIGH
        elif coding_ratio >= 0.4 and coding_sessions >= 3:
            return CodingIntensity.MEDIUM
        elif coding_ratio >= 0.2:
            return CodingIntensity.LOW
        else:
            return CodingIntensity.NONE
    
    @staticmethod
    def determine_ai_dependency(metrics: Dict) -> AIDependency:
        """
        Determine AI tool dependency based on AI tool usage.
        """
        ai_tool_minutes = metrics.get("ai_tool_minutes", 0)
        coding_minutes = metrics.get("coding_minutes", 1)
        
        if coding_minutes == 0:
            return AIDependency.NONE
        
        ai_ratio = ai_tool_minutes / coding_minutes
        
        if ai_ratio >= 0.5:
            return AIDependency.HIGH
        elif ai_ratio >= 0.3:
            return AIDependency.MEDIUM
        elif ai_ratio >= 0.1:
            return AIDependency.LOW
        else:
            return AIDependency.NONE
    
    @staticmethod
    def determine_distraction_level(metrics: Dict) -> DistractionLevel:
        """
        Determine distraction level based on entertainment and non-productive time.
        """
        entertainment_minutes = metrics.get("entertainment_minutes", 0)
        social_minutes = metrics.get("social_minutes", 0)
        total_minutes = metrics.get("total_minutes", 1)
        
        distraction_ratio = (entertainment_minutes + social_minutes) / total_minutes if total_minutes > 0 else 0
        
        if distraction_ratio >= 0.6:
            return DistractionLevel.SEVERE
        elif distraction_ratio >= 0.4:
            return DistractionLevel.HIGH
        elif distraction_ratio >= 0.2:
            return DistractionLevel.MEDIUM
        else:
            return DistractionLevel.LOW
    
    @staticmethod
    def determine_energy_pattern(hourly_productivity: Dict[int, float]) -> EnergyPattern:
        """
        Determine peak energy pattern based on hourly productivity.
        
        Args:
            hourly_productivity: Dict mapping hour (0-23) to productivity score
        """
        if not hourly_productivity:
            return EnergyPattern.UNPREDICTABLE
        
        # Find peak hours
        peak_hours = [hour for hour, score in hourly_productivity.items() if score >= 0.8]
        
        if not peak_hours:
            return EnergyPattern.UNPREDICTABLE
        
        avg_peak_hour = sum(peak_hours) / len(peak_hours)
        
        if 5 <= avg_peak_hour < 12:
            return EnergyPattern.MORNING_PEAK
        elif 12 <= avg_peak_hour < 17:
            return EnergyPattern.AFTERNOON_PEAK
        elif 17 <= avg_peak_hour < 21:
            return EnergyPattern.EVENING_PEAK
        elif 21 <= avg_peak_hour or avg_peak_hour < 5:
            return EnergyPattern.NIGHT_PEAK
        else:
            return EnergyPattern.CONSISTENT
    
    @staticmethod
    def determine_work_rhythm(metrics: Dict) -> WorkRhythm:
        """
        Determine work rhythm based on session distribution and consistency.
        """
        session_variance = metrics.get("session_variance", 0)
        total_sessions = metrics.get("total_sessions", 0)
        total_minutes = metrics.get("total_minutes", 1)
        
        avg_session_length = total_minutes / total_sessions if total_sessions > 0 else 0
        
        if session_variance < 15 and avg_session_length >= 20:
            return WorkRhythm.SUSTAINED
        elif session_variance < 30 and avg_session_length >= 10:
            return WorkRhythm.BURST
        elif session_variance < 50:
            return WorkRhythm.IRREGULAR
        else:
            return WorkRhythm.DECLINING
    
    @staticmethod
    def determine_risk_level(metrics: Dict, trend: str) -> RiskLevel:
        """
        Determine overall risk level based on metrics and trend.
        """
        focus_score = metrics.get("focus_score", 100)
        productive_ratio = metrics.get("productive_ratio", 1)
        main_issue = BusinessRules.determine_main_issue(metrics)
        
        # Critical risk
        if focus_score < 30 or productive_ratio < 0.2:
            return RiskLevel.CRITICAL
        
        # High risk
        if focus_score < 50 or productive_ratio < 0.4 or main_issue in [
            MainIssue.BURNOUT_RISK,
            MainIssue.HIGH_CONTEXT_SWITCHING
        ]:
            return RiskLevel.HIGH
        
        # High risk if declining trend
        if trend == "declining" and focus_score < 60:
            return RiskLevel.HIGH
        
        # Medium risk
        if focus_score < 70 or productive_ratio < 0.6 or main_issue != MainIssue.NO_SIGNIFICANT_ISSUE:
            return RiskLevel.MEDIUM
        
        # Low risk
        return RiskLevel.LOW
    
    @staticmethod
    def generate_strengths(metrics: Dict) -> List[str]:
        """
        Generate list of identified strengths.
        """
        strengths = []
        
        productive_ratio = metrics.get("productive_ratio", 0)
        deep_work_ratio = metrics.get("deep_work_ratio", 0)
        coding_ratio = metrics.get("coding_minutes", 0) / max(metrics.get("total_minutes", 1), 1)
        entertainment_ratio = metrics.get("entertainment_minutes", 0) / max(metrics.get("total_minutes", 1), 1)
        tab_switches = metrics.get("tab_switches", 0)
        total_minutes = metrics.get("total_minutes", 1)
        tab_switches_per_hour = (tab_switches / total_minutes) * 60 if total_minutes > 0 else 0
        
        if productive_ratio >= BusinessRules.HIGH_PRODUCTIVE_RATIO:
            strengths.append("high productivity")
        
        if deep_work_ratio >= BusinessRules.HIGH_DEEP_WORK_RATIO:
            strengths.append("strong deep work")
        
        if coding_ratio >= 0.5:
            strengths.append("consistent coding")
        
        if entertainment_ratio <= 0.2:
            strengths.append("low entertainment")
        
        if tab_switches_per_hour < 50:
            strengths.append("minimal context switching")
        
        if metrics.get("longest_focus_session", 0) >= 45:
            strengths.append("long focus sessions")
        
        if not strengths:
            strengths.append("room for improvement in all areas")
        
        return strengths
    
    @staticmethod
    def generate_weaknesses(metrics: Dict) -> List[str]:
        """
        Generate list of identified weaknesses.
        """
        weaknesses = []
        
        tab_switches = metrics.get("tab_switches", 0)
        longest_session = metrics.get("longest_focus_session", 0)
        productive_ratio = metrics.get("productive_ratio", 1)
        deep_work_ratio = metrics.get("deep_work_ratio", 1)
        coding_ratio = metrics.get("coding_minutes", 0) / max(metrics.get("total_minutes", 1), 1)
        entertainment_ratio = metrics.get("entertainment_minutes", 0) / max(metrics.get("total_minutes", 1), 1)
        
        if tab_switches > BusinessRules.HIGH_TAB_SWITCHES:
            weaknesses.append("rapid tab switching")
        
        if longest_session < BusinessRules.LOW_SESSION_LENGTH:
            weaknesses.append("short focus sessions")
        
        if productive_ratio < BusinessRules.LOW_PRODUCTIVE_RATIO:
            weaknesses.append("low productive time")
        
        if deep_work_ratio < BusinessRules.LOW_DEEP_WORK_RATIO:
            weaknesses.append("insufficient deep work")
        
        if coding_ratio < 0.3 and metrics.get("total_minutes", 0) > 60:
            weaknesses.append("low coding activity")
        
        if entertainment_ratio > 0.4:
            weaknesses.append("high entertainment usage")
        
        if not weaknesses:
            weaknesses.append("minor areas for optimization")
        
        return weaknesses
    
    @staticmethod
    def generate_recommendations(metrics: Dict, main_issue: MainIssue) -> List[str]:
        """
        Generate actionable recommendations based on main issue and metrics.
        """
        recommendations = []
        
        if main_issue == MainIssue.HIGH_CONTEXT_SWITCHING:
            recommendations.append("use website blockers during focus sessions")
            recommendations.append("group similar tasks together")
            recommendations.append("set specific times for checking notifications")
        
        elif main_issue == MainIssue.LOW_DEEP_WORK:
            recommendations.append("schedule 2-hour deep work blocks")
            recommendations.append("eliminate distractions during peak hours")
            recommendations.append("use the Pomodoro technique for longer sessions")
        
        elif main_issue == MainIssue.HIGH_DISTRACTION:
            recommendations.append("identify and block distracting websites")
            recommendations.append("use focus mode on your devices")
            recommendations.append("schedule distraction-free periods")
        
        elif main_issue == MainIssue.LOW_CODING_INTENSITY:
            recommendations.append("set daily coding time goals")
            recommendations.append("join coding challenges or projects")
            recommendations.append("schedule dedicated coding sessions")
        
        elif main_issue == MainIssue.HIGH_ENTERTAINMENT:
            recommendations.append("set time limits on entertainment sites")
            recommendations.append("replace entertainment with learning activities")
            recommendations.append("use entertainment as a reward after work")
        
        elif main_issue == MainIssue.BURNOUT_RISK:
            recommendations.append("take regular breaks and rest days")
            recommendations.append("reduce daily work hours")
            recommendations.append("prioritize sleep and recovery")
        
        elif main_issue == MainIssue.POOR_TIME_MANAGEMENT:
            recommendations.append("use time-blocking for your day")
            recommendations.append("prioritize tasks using the Eisenhower matrix")
            recommendations.append("set clear daily goals")
        
        elif main_issue == MainIssue.INCONSISTENT_SCHEDULE:
            recommendations.append("establish a consistent daily routine")
            recommendations.append("set fixed work hours")
            recommendations.append("create morning and evening rituals")
        
        # General recommendations
        tab_switches = metrics.get("tab_switches", 0)
        if tab_switches > 200:
            recommendations.append("reduce tab switching by using browser extensions")
        
        productive_ratio = metrics.get("productive_ratio", 1)
        if productive_ratio < 0.6:
            recommendations.append("increase productive time by eliminating low-value activities")
        
        if not recommendations:
            recommendations.append("maintain current productive habits")
        
        return recommendations
