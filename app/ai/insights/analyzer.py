"""
Insights Analyzer - Orchestrates insights generation.

Converts raw analytics into meaningful insights for AI reasoning.
"""

from typing import Dict, List, Optional
from datetime import date, timedelta
from app.ai.insights.schemas import (
    InsightSummary,
    DerivedMetrics,
    TrendAnalysis,
    MainIssue,
    Trend,
    RiskLevel,
    DeepWorkQuality,
    AttentionPattern,
    CodingIntensity,
    AIDependency,
    DistractionLevel,
    EnergyPattern,
    WorkRhythm
)
from app.ai.insights.metrics import MetricsCalculator
from app.ai.insights.rules import BusinessRules
from app.ai.insights.trends import TrendAnalyzer


class InsightsAnalyzer:
    """
    Main analyzer that orchestrates insights generation from raw analytics.
    
    This is the entry point for the insights engine.
    """
    
    def __init__(self):
        """Initialize the analyzer with sub-components."""
        self.metrics_calculator = MetricsCalculator()
        self.business_rules = BusinessRules()
        self.trend_analyzer = TrendAnalyzer()
    
    def analyze_daily_insights(
        self,
        raw_metrics: Dict,
        historical_data: Optional[List[Dict]] = None
    ) -> InsightSummary:
        """
        Generate comprehensive insights for a single day.
        
        Args:
            raw_metrics: Raw analytics data for the day
            historical_data: Optional historical data for trend analysis (last 7-30 days)
            
        Returns:
            InsightSummary with all insights
        """
        print(f"[INSIGHTS ANALYZER] Analyzing daily insights")
        
        # Calculate derived metrics
        derived_metrics = self.metrics_calculator.calculate_derived_metrics(raw_metrics)
        print(f"[INSIGHTS ANALYZER] Derived metrics calculated")
        
        # Determine qualitative insights using business rules
        main_issue = self.business_rules.determine_main_issue(raw_metrics)
        deep_work = self.business_rules.determine_deep_work_quality(raw_metrics)
        attention = self.business_rules.determine_attention_pattern(raw_metrics)
        coding = self.business_rules.determine_coding_intensity(raw_metrics)
        ai_dependency = self.business_rules.determine_ai_dependency(raw_metrics)
        distraction = self.business_rules.determine_distraction_level(raw_metrics)
        
        # Determine patterns
        hourly_productivity = raw_metrics.get("hourly_productivity", {})
        energy_pattern = self.business_rules.determine_energy_pattern(hourly_productivity)
        work_rhythm = self.business_rules.determine_work_rhythm(raw_metrics)
        
        # Analyze trends if historical data available
        if historical_data and len(historical_data) >= 2:
            trend_analysis = self.trend_analyzer.analyze_trends(historical_data)
            overall_trend = trend_analysis.overall_trend
        else:
            overall_trend = Trend.STABLE
        
        # Determine risk level
        risk = self.business_rules.determine_risk_level(raw_metrics, overall_trend.value)
        
        # Generate strengths and weaknesses
        strengths = self.business_rules.generate_strengths(raw_metrics)
        weaknesses = self.business_rules.generate_weaknesses(raw_metrics)
        
        # Generate recommendations
        recommendations = self.business_rules.generate_recommendations(raw_metrics, main_issue)
        
        # Determine overall assessment
        overall = self._determine_overall_assessment(raw_metrics, risk)
        
        # Build insight summary
        insight_summary = InsightSummary(
            overall=overall,
            trend=overall_trend,
            main_issue=main_issue,
            risk=risk,
            deep_work=deep_work,
            attention=attention,
            coding=coding,
            ai_dependency=ai_dependency,
            distraction=distraction,
            energy_pattern=energy_pattern,
            work_rhythm=work_rhythm,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
            tab_switches_per_hour=derived_metrics.tab_switches_per_hour,
            average_session_length=derived_metrics.average_session_length,
            deep_work_ratio=derived_metrics.deep_work_ratio,
            productive_ratio=derived_metrics.productive_ratio,
            focus_efficiency=derived_metrics.focus_efficiency
        )
        
        print(f"[INSIGHTS ANALYZER] Insight summary generated: {overall} assessment, {main_issue.value} main issue")
        return insight_summary
    
    def analyze_weekly_insights(
        self,
        daily_metrics: List[Dict]
    ) -> InsightSummary:
        """
        Generate insights for a week by aggregating daily data.
        
        Args:
            daily_metrics: List of daily metrics for the week
            
        Returns:
            InsightSummary with weekly insights
        """
        print(f"[INSIGHTS ANALYZER] Analyzing weekly insights from {len(daily_metrics)} days")
        
        if not daily_metrics:
            raise ValueError("No daily metrics provided for weekly analysis")
        
        # Aggregate daily metrics
        aggregated_metrics = self._aggregate_daily_metrics(daily_metrics)
        
        # Use historical data for trend analysis
        trend_analysis = self.trend_analyzer.analyze_trends(daily_metrics)
        
        # Generate insights using aggregated data
        return self.analyze_daily_insights(aggregated_metrics, daily_metrics)
    
    def get_derived_metrics(self, raw_metrics: Dict) -> DerivedMetrics:
        """
        Get derived metrics without full insight analysis.
        
        Args:
            raw_metrics: Raw analytics data
            
        Returns:
            DerivedMetrics with calculated metrics
        """
        return self.metrics_calculator.calculate_derived_metrics(raw_metrics)
    
    def get_trend_analysis(self, historical_data: List[Dict]) -> TrendAnalysis:
        """
        Get trend analysis without full insight analysis.
        
        Args:
            historical_data: Historical metrics data
            
        Returns:
            TrendAnalysis with trend information
        """
        return self.trend_analyzer.analyze_trends(historical_data)
    
    def _determine_overall_assessment(
        self,
        metrics: Dict,
        risk: RiskLevel
    ) -> str:
        """
        Determine overall assessment (good, fair, poor).
        
        Args:
            metrics: Raw metrics
            risk: Risk level
            
        Returns:
            Overall assessment string
        """
        focus_score = metrics.get("focus_score", 0)
        productive_ratio = metrics.get("productive_ratio", 0)
        
        if risk == RiskLevel.CRITICAL:
            return "poor"
        elif risk == RiskLevel.HIGH:
            return "poor"
        elif risk == RiskLevel.MEDIUM:
            if focus_score >= 60 and productive_ratio >= 0.6:
                return "fair"
            else:
                return "poor"
        else:  # Low risk
            if focus_score >= 80 and productive_ratio >= 0.8:
                return "good"
            elif focus_score >= 60 and productive_ratio >= 0.6:
                return "fair"
            else:
                return "poor"
    
    def _aggregate_daily_metrics(self, daily_metrics: List[Dict]) -> Dict:
        """
        Aggregate daily metrics into weekly metrics.
        
        Args:
            daily_metrics: List of daily metrics
            
        Returns:
            Aggregated metrics dictionary
        """
        if not daily_metrics:
            return {}
        
        # Sum numeric fields
        aggregated = {
            "tab_switches": sum(d.get("tab_switches", 0) for d in daily_metrics),
            "productive_minutes": sum(d.get("productive_minutes", 0) for d in daily_metrics),
            "idle_minutes": sum(d.get("idle_minutes", 0) for d in daily_metrics),
            "coding_minutes": sum(d.get("coding_minutes", 0) for d in daily_metrics),
            "ai_tool_minutes": sum(d.get("ai_tool_minutes", 0) for d in daily_metrics),
            "entertainment_minutes": sum(d.get("entertainment_minutes", 0) for d in daily_metrics),
            "social_minutes": sum(d.get("social_minutes", 0) for d in daily_metrics),
            "total_sessions": sum(d.get("total_sessions", 0) for d in daily_metrics),
            "total_minutes": sum(d.get("total_minutes", 0) for d in daily_metrics),
        }
        
        # Average numeric fields
        aggregated["focus_score"] = sum(d.get("focus_score", 0) for d in daily_metrics) / len(daily_metrics)
        aggregated["longest_focus_session"] = max(d.get("longest_focus_session", 0) for d in daily_metrics)
        
        # Collect session lengths
        session_lengths = []
        for d in daily_metrics:
            session_lengths.extend(d.get("session_lengths", []))
        aggregated["session_lengths"] = session_lengths
        
        # Aggregate hourly productivity
        hourly_productivity = {}
        for d in daily_metrics:
            day_hourly = d.get("hourly_productivity", {})
            for hour, score in day_hourly.items():
                if hour not in hourly_productivity:
                    hourly_productivity[hour] = []
                hourly_productivity[hour].append(score)
        
        # Average hourly productivity
        aggregated["hourly_productivity"] = {
            hour: sum(scores) / len(scores)
            for hour, scores in hourly_productivity.items()
        }
        
        # Calculate derived ratios
        aggregated["productive_ratio"] = aggregated["productive_minutes"] / max(aggregated["total_minutes"], 1)
        aggregated["deep_work_ratio"] = sum(
            length for length in session_lengths if length >= 20
        ) / max(aggregated["total_minutes"], 1)
        
        # Calculate session variance
        if len(session_lengths) > 1:
            from statistics import stdev
            aggregated["session_variance"] = stdev(session_lengths)
        else:
            aggregated["session_variance"] = 0
        
        # Count unique websites
        unique_websites = set()
        for d in daily_metrics:
            unique_websites.update(d.get("unique_websites", []))
        aggregated["unique_websites"] = len(unique_websites)
        
        return aggregated
    
    def format_insights_for_prompt(self, insights: InsightSummary) -> str:
        """
        Format insights for inclusion in AI prompt.
        
        Args:
            insights: InsightSummary to format
            
        Returns:
            Formatted string for AI prompt
        """
        lines = [
            "=== PRODUCTIVITY INSIGHTS ===",
            f"Overall Assessment: {insights.overall.upper()}",
            f"Trend: {insights.trend}",
            f"Main Issue: {insights.main_issue.replace('_', ' ').title()}",
            f"Risk Level: {insights.risk}",
            "",
            "=== QUALITY METRICS ===",
            f"Deep Work: {insights.deep_work}",
            f"Attention Pattern: {insights.attention}",
            f"Coding Intensity: {insights.coding}",
            f"AI Dependency: {insights.ai_dependency}",
            f"Distraction Level: {insights.distraction}",
            "",
            "=== PATTERNS ===",
            f"Energy Pattern: {insights.energy_pattern}",
            f"Work Rhythm: {insights.work_rhythm}",
            "",
            "=== STRENGTHS ===",
        ]
        
        for strength in insights.strengths:
            lines.append(f"- {strength}")
        
        lines.append("")
        lines.append("=== WEAKNESSES ===")
        
        for weakness in insights.weaknesses:
            lines.append(f"- {weakness}")
        
        lines.append("")
        lines.append("=== RECOMMENDATIONS ===")
        
        for rec in insights.recommendations:
            lines.append(f"- {rec}")
        
        lines.append("")
        lines.append("=== DERIVED METRICS ===")
        
        if insights.tab_switches_per_hour is not None:
            lines.append(f"Tab Switches Per Hour: {insights.tab_switches_per_hour:.1f}")
        if insights.average_session_length is not None:
            lines.append(f"Average Session Length: {insights.average_session_length:.1f}m")
        if insights.deep_work_ratio is not None:
            lines.append(f"Deep Work Ratio: {insights.deep_work_ratio:.1%}")
        if insights.productive_ratio is not None:
            lines.append(f"Productive Ratio: {insights.productive_ratio:.1%}")
        if insights.focus_efficiency is not None:
            lines.append(f"Focus Efficiency: {insights.focus_efficiency:.1f}")
        
        return "\n".join(lines)
