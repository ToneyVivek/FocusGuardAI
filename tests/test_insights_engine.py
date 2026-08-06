"""
Test script for Insights Engine.

Tests the insights generation with sample data.
"""

from app.ai.insights.analyzer import InsightsAnalyzer
from app.ai.insights.schemas import InsightSummary


def test_insights_engine():
    """Test the insights engine with sample data."""
    print("=" * 80)
    print("TESTING INSIGHTS ENGINE")
    print("=" * 80)
    
    analyzer = InsightsAnalyzer()
    
    # Sample raw metrics (simulating a day with high context switching)
    raw_metrics = {
        "focus_score": 56,
        "tab_switches": 498,
        "productive_minutes": 240,
        "idle_minutes": 30,
        "total_minutes": 480,
        "total_sessions": 12,
        "longest_focus_session": 8,
        "coding_minutes": 180,
        "ai_tool_minutes": 90,
        "entertainment_minutes": 60,
        "social_minutes": 30,
        "session_lengths": [5, 8, 12, 6, 10, 15, 7, 9, 11, 8, 14, 6],
        "hourly_productivity": {
            9: 0.6,
            10: 0.7,
            11: 0.5,
            14: 0.8,
            15: 0.6,
            16: 0.7
        },
        "unique_websites": 25
    }
    
    print("\n--- Sample Raw Metrics ---")
    for key, value in raw_metrics.items():
        print(f"{key}: {value}")
    
    # Generate insights
    print("\n--- Generating Insights ---")
    insights = analyzer.analyze_daily_insights(raw_metrics)
    
    print("\n--- Insight Summary ---")
    print(f"Overall: {insights.overall}")
    print(f"Trend: {insights.trend}")
    print(f"Main Issue: {insights.main_issue}")
    print(f"Risk: {insights.risk}")
    print(f"Deep Work: {insights.deep_work}")
    print(f"Attention: {insights.attention}")
    print(f"Coding: {insights.coding}")
    print(f"AI Dependency: {insights.ai_dependency}")
    print(f"Distraction: {insights.distraction}")
    print(f"Energy Pattern: {insights.energy_pattern}")
    print(f"Work Rhythm: {insights.work_rhythm}")
    
    print("\n--- Strengths ---")
    for strength in insights.strengths:
        print(f"- {strength}")
    
    print("\n--- Weaknesses ---")
    for weakness in insights.weaknesses:
        print(f"- {weakness}")
    
    print("\n--- Recommendations ---")
    for rec in insights.recommendations:
        print(f"- {rec}")
    
    print("\n--- Derived Metrics ---")
    print(f"Tab Switches Per Hour: {insights.tab_switches_per_hour:.1f}")
    print(f"Average Session Length: {insights.average_session_length:.1f}m")
    print(f"Deep Work Ratio: {insights.deep_work_ratio:.1%}")
    print(f"Productive Ratio: {insights.productive_ratio:.1%}")
    print(f"Focus Efficiency: {insights.focus_efficiency:.1f}")
    
    print("\n--- Formatted for AI Prompt ---")
    formatted = analyzer.format_insights_for_prompt(insights)
    print(formatted)
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    test_insights_engine()
