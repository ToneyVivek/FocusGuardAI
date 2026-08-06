"""
AI Insights Engine

Converts raw analytics into meaningful insights for AI reasoning.
"""

from app.ai.insights.analyzer import InsightsAnalyzer
from app.ai.insights.schemas import (
    InsightSummary,
    MainIssue,
    Trend,
    RiskLevel,
    DeepWorkQuality,
    AttentionPattern,
    CodingIntensity,
    AIDependency,
    DistractionLevel
)

__all__ = [
    "InsightsAnalyzer",
    "InsightSummary",
    "MainIssue",
    "Trend",
    "RiskLevel",
    "DeepWorkQuality",
    "AttentionPattern",
    "CodingIntensity",
    "AIDependency",
    "DistractionLevel"
]
