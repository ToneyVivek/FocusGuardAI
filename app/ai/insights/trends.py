"""
Trend detection for analytics data.

Detects changes over time to identify improving, declining, stable, or volatile patterns.
"""

from typing import List, Dict, Optional
from statistics import mean, stdev
from app.ai.insights.schemas import Trend, TrendAnalysis


class TrendAnalyzer:
    """
    Analyzes trends in productivity metrics over time.
    
    Uses statistical analysis to detect patterns and trends.
    """
    
    @staticmethod
    def analyze_trends(historical_data: List[Dict]) -> TrendAnalysis:
        """
        Analyze trends across all metrics from historical data.
        
        Args:
            historical_data: List of daily metrics, ordered by date (oldest to newest)
            
        Returns:
            TrendAnalysis with trend information for all metrics
        """
        if len(historical_data) < 2:
            # Not enough data for trend analysis
            return TrendAnalysis(
                focus_score_trend=Trend.STABLE,
                productive_time_trend=Trend.STABLE,
                distraction_trend=Trend.STABLE,
                coding_trend=Trend.STABLE,
                overall_trend=Trend.STABLE,
                trend_strength="insufficient_data",
                trend_duration="unknown"
            )
        
        # Extract time series data
        focus_scores = [d.get("focus_score", 0) for d in historical_data]
        productive_minutes = [d.get("productive_minutes", 0) for d in historical_data]
        tab_switches = [d.get("tab_switches", 0) for d in historical_data]
        coding_minutes = [d.get("coding_minutes", 0) for d in historical_data]
        
        # Calculate trends
        focus_score_trend = TrendAnalyzer._detect_trend(focus_scores)
        productive_time_trend = TrendAnalyzer._detect_trend(productive_minutes)
        distraction_trend = TrendAnalyzer._detect_trend(tab_switches, inverse=True)  # Higher = worse
        coding_trend = TrendAnalyzer._detect_trend(coding_minutes)
        
        # Calculate overall trend
        overall_trend = TrendAnalyzer._calculate_overall_trend([
            focus_score_trend,
            productive_time_trend,
            distraction_trend,
            coding_trend
        ])
        
        # Calculate trend strength
        trend_strength = TrendAnalyzer._calculate_trend_strength(focus_scores)
        
        # Calculate trend duration
        trend_duration = TrendAnalyzer._calculate_trend_duration(focus_scores, overall_trend)
        
        return TrendAnalysis(
            focus_score_trend=focus_score_trend,
            productive_time_trend=productive_time_trend,
            distraction_trend=distraction_trend,
            coding_trend=coding_trend,
            overall_trend=overall_trend,
            trend_strength=trend_strength,
            trend_duration=trend_duration,
            recent_focus_scores=focus_scores[-7:] if len(focus_scores) >= 7 else focus_scores,
            recent_productive_minutes=productive_minutes[-7:] if len(productive_minutes) >= 7 else productive_minutes
        )
    
    @staticmethod
    def _detect_trend(values: List[float], inverse: bool = False) -> Trend:
        """
        Detect trend from a list of values.
        
        Args:
            values: List of numeric values over time
            inverse: If True, higher values are considered worse (e.g., distractions)
            
        Returns:
            Trend enum value
        """
        if len(values) < 2:
            return Trend.STABLE
        
        # Calculate linear regression slope
        n = len(values)
        x = list(range(n))
        y = values
        
        # Calculate slope using least squares
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x2 = sum(xi * xi for xi in x)
        
        denominator = n * sum_x2 - sum_x * sum_x
        if denominator == 0:
            return Trend.STABLE
        
        slope = (n * sum_xy - sum_x * sum_y) / denominator
        
        # Calculate volatility (standard deviation)
        if len(values) > 1:
            volatility = stdev(values) / (mean(values) + 1)
        else:
            volatility = 0
        
        # Determine trend
        # High volatility indicates volatile pattern
        if volatility > 0.3:
            return Trend.VOLATILE
        
        # Otherwise, use slope to determine direction
        threshold = mean(values) * 0.05  # 5% change threshold
        
        if inverse:
            # For inverse metrics (higher = worse), flip the slope
            slope = -slope
        
        if slope > threshold:
            return Trend.IMPROVING
        elif slope < -threshold:
            return Trend.DECLINING
        else:
            return Trend.STABLE
    
    @staticmethod
    def _calculate_overall_trend(trends: List[Trend]) -> Trend:
        """
        Calculate overall trend from individual metric trends.
        
        Args:
            trends: List of individual trends
            
        Returns:
            Overall trend
        """
        if not trends:
            return Trend.STABLE
        
        # Count trend types
        improving_count = sum(1 for t in trends if t == Trend.IMPROVING)
        declining_count = sum(1 for t in trends if t == Trend.DECLINING)
        volatile_count = sum(1 for t in trends if t == Trend.VOLATILE)
        stable_count = sum(1 for t in trends if t == Trend.STABLE)
        
        total = len(trends)
        
        # Determine overall trend based on majority
        if volatile_count >= total * 0.5:
            return Trend.VOLATILE
        elif improving_count >= total * 0.6:
            return Trend.IMPROVING
        elif declining_count >= total * 0.6:
            return Trend.DECLINING
        else:
            return Trend.STABLE
    
    @staticmethod
    def _calculate_trend_strength(values: List[float]) -> str:
        """
        Calculate the strength of the current trend.
        
        Args:
            values: List of values over time
            
        Returns:
            String describing trend strength: strong, moderate, weak
        """
        if len(values) < 3:
            return "insufficient_data"
        
        # Calculate the slope of the last 7 days (or all if less)
        recent_values = values[-7:] if len(values) >= 7 else values
        
        # Calculate percentage change
        if len(recent_values) >= 2:
            first_val = recent_values[0]
            last_val = recent_values[-1]
            
            if first_val == 0:
                return "unknown"
            
            percent_change = abs((last_val - first_val) / first_val)
            
            if percent_change >= 0.2:  # 20% change
                return "strong"
            elif percent_change >= 0.1:  # 10% change
                return "moderate"
            else:
                return "weak"
        
        return "unknown"
    
    @staticmethod
    def _calculate_trend_duration(values: List[float], current_trend: Trend) -> str:
        """
        Calculate how long the current trend has been ongoing.
        
        Args:
            values: List of values over time
            current_trend: The current detected trend
            
        Returns:
            String describing duration: short_term, medium_term, long_term
        """
        if len(values) < 3:
            return "insufficient_data"
        
        # Count consecutive days with the same trend direction
        consecutive_count = 0
        
        for i in range(len(values) - 1, 0, -1):
            # Compare current value with previous
            if current_trend == Trend.IMPROVING:
                if values[i] >= values[i-1]:
                    consecutive_count += 1
                else:
                    break
            elif current_trend == Trend.DECLINING:
                if values[i] <= values[i-1]:
                    consecutive_count += 1
                else:
                    break
            else:
                # For stable, check if values are close
                if abs(values[i] - values[i-1]) / (values[i-1] + 1) < 0.05:
                    consecutive_count += 1
                else:
                    break
        
        if consecutive_count >= 7:
            return "long_term"
        elif consecutive_count >= 4:
            return "medium_term"
        elif consecutive_count2 >= 2:
            return "short_term"
        else:
            return "just_started"
    
    @staticmethod
    def detect_focus_score_trend(focus_scores: List[float]) -> Trend:
        """
        Detect trend specifically for focus scores.
        
        Args:
            focus_scores: List of focus scores over time
            
        Returns:
            Trend enum value
        """
        return TrendAnalyzer._detect_trend(focus_scores)
    
    @staticmethod
    def detect_productive_time_trend(productive_minutes: List[int]) -> Trend:
        """
        Detect trend specifically for productive time.
        
        Args:
            productive_minutes: List of productive minutes over time
            
        Returns:
            Trend enum value
        """
        return TrendAnalyzer._detect_trend(productive_minutes)
    
    @staticmethod
    def detect_distraction_trend(tab_switches: List[int]) -> Trend:
        """
        Detect trend specifically for distractions (tab switches).
        
        Args:
            tab_switches: List of tab switches over time
            
        Returns:
            Trend enum value (inverse: higher = worse)
        """
        return TrendAnalyzer._detect_trend(tab_switches, inverse=True)
    
    @staticmethod
    def detect_coding_trend(coding_minutes: List[int]) -> Trend:
        """
        Detect trend specifically for coding activity.
        
        Args:
            coding_minutes: List of coding minutes over time
            
        Returns:
            Trend enum value
        """
        return TrendAnalyzer._detect_trend(coding_minutes)
    
    @staticmethod
    def get_trend_description(trend: Trend) -> str:
        """
        Get human-readable description of a trend.
        
        Args:
            trend: Trend enum value
            
        Returns:
            Human-readable description
        """
        descriptions = {
            Trend.IMPROVING: "Your productivity is improving over time",
            Trend.DECLINING: "Your productivity is declining over time",
            Trend.STABLE: "Your productivity is stable",
            Trend.VOLATILE: "Your productivity is volatile with significant fluctuations"
        }
        return descriptions.get(trend, "Unknown trend")
    
    @staticmethod
    def get_trend_recommendation(trend: Trend, metric_name: str) -> str:
        """
        Get recommendation based on trend.
        
        Args:
            trend: Trend enum value
            metric_name: Name of the metric (e.g., "focus score")
            
        Returns:
            Recommendation string
        """
        if trend == Trend.IMPROVING:
            return f"Your {metric_name} is improving. Keep up the good work!"
        elif trend == Trend.DECLINING:
            return f"Your {metric_name} is declining. Consider reviewing your habits and environment."
        elif trend == Trend.STABLE:
            return f"Your {metric_name} is stable. Look for opportunities to optimize further."
        elif trend == Trend.VOLATILE:
            return f"Your {metric_name} is volatile. Try to establish more consistent routines."
        else:
            return f"Monitor your {metric_name} to identify patterns."
