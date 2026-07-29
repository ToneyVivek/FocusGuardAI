"""
Focus score calculation utilities.

Provides reusable focus score calculation logic.
"""
from typing import Tuple


def calculate_focus_score(productive_time: int, total_active_time: int) -> float:
    """
    Calculate focus score.
    
    Formula:
    Focus Score = (Productive Time / Total Active Time) × 100
    
    Where Total Active Time = Productive + Neutral + Non Productive
    (Idle time is NOT included in the denominator)
    
    Args:
        productive_time: Productive time in seconds
        total_active_time: Total active time in seconds (productive + neutral + non-productive)
        
    Returns:
        Focus score (0-100)
    """
    if total_active_time == 0:
        return 0.0
    
    score = (productive_time / total_active_time) * 100
    return round(score, 2)
