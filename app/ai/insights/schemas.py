"""
Pydantic schemas for insights engine.

Defines the data structures for insights, trends, and recommendations.
"""

from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field


class MainIssue(str, Enum):
    """Primary productivity issues identified."""
    HIGH_CONTEXT_SWITCHING = "high_context_switching"
    LOW_DEEP_WORK = "low_deep_work"
    POOR_TIME_MANAGEMENT = "poor_time_management"
    HIGH_DISTRACTION = "high_distraction"
    INCONSISTENT_SCHEDULE = "inconsistent_schedule"
    BURNOUT_RISK = "burnout_risk"
    LOW_CODING_INTENSITY = "low_coding_intensity"
    HIGH_ENTERTAINMENT = "high_entertainment"
    NO_SIGNIFICANT_ISSUE = "no_significant_issue"


class Trend(str, Enum):
    """Productivity trends over time."""
    IMPROVING = "improving"
    DECLINING = "declining"
    STABLE = "stable"
    VOLATILE = "volatile"


class RiskLevel(str, Enum):
    """Risk level for productivity decline."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DeepWorkQuality(str, Enum):
    """Quality of deep work sessions."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    NONE = "none"


class AttentionPattern(str, Enum):
    """Pattern of user attention."""
    FOCUSED = "focused"
    FRAGMENTED = "fragmented"
    SCATTERED = "scattered"
    CONSISTENT = "consistent"


class CodingIntensity(str, Enum):
    """Intensity of coding activity."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class AIDependency(str, Enum):
    """Dependency on AI tools."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class DistractionLevel(str, Enum):
    """Level of distractions."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    SEVERE = "severe"


class EnergyPattern(str, Enum):
    """Peak energy patterns."""
    MORNING_PEAK = "morning_peak"
    AFTERNOON_PEAK = "afternoon_peak"
    EVENING_PEAK = "evening_peak"
    NIGHT_PEAK = "night_peak"
    CONSISTENT = "consistent"
    UNPREDICTABLE = "unpredictable"


class WorkRhythm(str, Enum):
    """Work rhythm patterns."""
    SUSTAINED = "sustained"
    BURST = "burst"
    IRREGULAR = "irregular"
    DECLINING = "declining"


class InsightSummary(BaseModel):
    """Summary of insights derived from analytics."""
    
    overall: str = Field(..., description="Overall assessment: good, fair, or poor")
    trend: Trend = Field(..., description="Productivity trend over time")
    main_issue: MainIssue = Field(..., description="Primary issue identified")
    risk: RiskLevel = Field(..., description="Risk level for productivity decline")
    
    # Quality metrics
    deep_work: DeepWorkQuality = Field(..., description="Quality of deep work")
    attention: AttentionPattern = Field(..., description="Attention pattern")
    coding: CodingIntensity = Field(..., description="Coding intensity")
    ai_dependency: AIDependency = Field(..., description="AI tool dependency")
    distraction: DistractionLevel = Field(..., description="Distraction level")
    
    # Patterns
    energy_pattern: EnergyPattern = Field(..., description="Peak energy pattern")
    work_rhythm: WorkRhythm = Field(..., description="Work rhythm pattern")
    
    # Lists
    strengths: List[str] = Field(default_factory=list, description="Identified strengths")
    weaknesses: List[str] = Field(default_factory=list, description="Identified weaknesses")
    recommendations: List[str] = Field(default_factory=list, description="Actionable recommendations")
    
    # Derived metrics
    tab_switches_per_hour: Optional[float] = Field(None, description="Tab switches per hour")
    average_session_length: Optional[float] = Field(None, description="Average session length in minutes")
    deep_work_ratio: Optional[float] = Field(None, description="Ratio of deep work time to total time")
    productive_ratio: Optional[float] = Field(None, description="Ratio of productive time to total time")
    focus_efficiency: Optional[float] = Field(None, description="Focus efficiency score")
    
    class Config:
        use_enum_values = True


class DerivedMetrics(BaseModel):
    """Derived metrics calculated from raw analytics."""
    
    tab_switches_per_hour: float = Field(..., description="Tab switches per hour")
    average_session_length: float = Field(..., description="Average session length in minutes")
    deep_work_ratio: float = Field(..., description="Ratio of deep work time to total time")
    productive_ratio: float = Field(..., description="Ratio of productive time to total time")
    focus_efficiency: float = Field(..., description="Focus efficiency score (0-100)")
    coding_consistency: float = Field(..., description="Coding consistency score (0-100)")
    ai_tool_dependency: float = Field(..., description="AI tool dependency score (0-100)")
    entertainment_balance: float = Field(..., description="Entertainment balance score (0-100)")
    
    # Advanced metrics
    context_switching_severity: str = Field(..., description="Severity of context switching")
    deep_work_quality: str = Field(..., description="Quality of deep work")
    coding_intensity: str = Field(..., description="Intensity of coding activity")
    attention_fragmentation: str = Field(..., description="Level of attention fragmentation")
    burnout_risk: str = Field(..., description="Risk of burnout")
    focus_stability: str = Field(..., description="Stability of focus")
    recovery_quality: str = Field(..., description="Quality of recovery periods")
    session_efficiency: str = Field(..., description="Efficiency of sessions")
    website_diversity: str = Field(..., description="Diversity of websites visited")
    task_fragmentation: str = Field(..., description="Level of task fragmentation")
    peak_performance_window: str = Field(..., description="Peak performance time window")


class TrendAnalysis(BaseModel):
    """Analysis of trends over time."""
    
    focus_score_trend: Trend = Field(..., description="Trend in focus score")
    productive_time_trend: Trend = Field(..., description="Trend in productive time")
    distraction_trend: Trend = Field(..., description="Trend in distractions")
    coding_trend: Trend = Field(..., description="Trend in coding activity")
    
    overall_trend: Trend = Field(..., description="Overall productivity trend")
    trend_strength: str = Field(..., description="Strength of the trend: strong, moderate, weak")
    trend_duration: str = Field(..., description="Duration of current trend")
    
    # Recent values
    recent_focus_scores: List[float] = Field(default_factory=list, description="Recent focus scores")
    recent_productive_minutes: List[int] = Field(default_factory=list, description="Recent productive minutes")
