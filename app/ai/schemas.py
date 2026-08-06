"""
AI Response Schemas

Structured response schemas for AI endpoints.
Ensures consistent JSON responses for frontend consumption.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class DailySummaryResponse(BaseModel):
    """Response schema for daily productivity summary."""
    
    title: str = Field(..., description="Summary title")
    summary: str = Field(..., description="Concise summary of the day")
    highlights: List[str] = Field(..., description="Key highlights from the day")
    recommendations: List[str] = Field(..., description="Recommendations for tomorrow")
    assessment: str = Field(..., description="Overall assessment (positive/neutral/needs_improvement)")
    focus_score: float = Field(..., ge=0, le=100, description="Focus score for the day")
    date: Optional[str] = Field(None, description="Date of the summary (ISO format)")
    
    model_config = {"json_schema_extra": {"example": {
        "title": "Daily Productivity Summary",
        "summary": "You had a productive day with strong focus on development work.",
        "highlights": [
            "6.5 hours of productive work",
            "Focus score of 87",
            "Completed 42 coding sessions"
        ],
        "recommendations": [
            "Take more frequent breaks to maintain focus",
            "Reduce time on social media during work hours"
        ],
        "assessment": "positive",
        "focus_score": 87,
        "date": "2026-07-30"
    }}}


class WeeklySummaryResponse(BaseModel):
    """Response schema for weekly productivity review."""
    
    title: str = Field(..., description="Summary title")
    summary: str = Field(..., description="Concise weekly summary")
    highlights: List[str] = Field(..., description="Key highlights from the week")
    recommendations: List[str] = Field(..., description="Recommendations for next week")
    assessment: str = Field(..., description="Overall assessment (excellent/good/fair/needs_improvement)")
    next_week_goal: str = Field(..., description="Specific goal for next week")
    focus_score: float = Field(..., ge=0, le=100, description="Average focus score for the week")
    start_date: Optional[str] = Field(None, description="Start date of the week (ISO format)")
    end_date: Optional[str] = Field(None, description="End date of the week (ISO format)")
    
    model_config = {"json_schema_extra": {"example": {
        "title": "Weekly Productivity Review",
        "summary": "You had a strong week with consistent focus on development tasks.",
        "highlights": [
            "32 hours of productive work",
            "Average focus score of 85",
            "Improved time allocation compared to last week"
        ],
        "recommendations": [
            "Maintain current work schedule",
            "Explore new learning resources",
            "Schedule regular review sessions"
        ],
        "assessment": "good",
        "next_week_goal": "Increase focus score to 90 by reducing distractions",
        "focus_score": 85,
        "start_date": "2026-07-24",
        "end_date": "2026-07-30"
    }}}


class InsightItem(BaseModel):
    """Individual insight item."""
    
    category: str = Field(..., description="Category of insight (pattern/distraction/balance/improvement)")
    insight: str = Field(..., description="The insight description")
    data_point: Optional[str] = Field(None, description="Supporting data point")


class InsightsResponse(BaseModel):
    """Response schema for productivity insights."""
    
    title: str = Field(..., description="Insights title")
    insights: List[InsightItem] = Field(..., description="List of insights")
    patterns: List[str] = Field(..., description="Identified productivity patterns")
    distractions: List[str] = Field(..., description="Top distractions identified")
    category_balance: str = Field(..., description="Analysis of category balance")
    focus_score_recommendations: List[str] = Field(..., description="Recommendations to improve focus score")
    time_allocation_suggestions: List[str] = Field(..., description="Suggestions for better time allocation")
    
    model_config = {"json_schema_extra": {"example": {
        "title": "Productivity Insights",
        "insights": [
            {
                "category": "pattern",
                "insight": "You are most productive in the morning hours",
                "data_point": "Peak productivity between 9 AM - 12 PM"
            }
        ],
        "patterns": [
            "Consistent morning productivity",
            "Higher focus on weekdays vs weekends"
        ],
        "distractions": [
            "Social media usage peaks in afternoon",
            "Email checking interrupts deep work sessions"
        ],
        "category_balance": "Good balance between development and learning activities",
        "focus_score_recommendations": [
            "Reduce context switching",
            "Schedule focused work blocks"
        ],
        "time_allocation_suggestions": [
            "Allocate more time to strategic planning",
            "Reduce time on low-priority tasks"
        ]
    }}}


class RecommendationItem(BaseModel):
    """Individual recommendation item."""
    
    title: str = Field(..., description="Recommendation title")
    impact: str = Field(..., description="Expected impact (high/medium/low)")
    implementation_steps: List[str] = Field(..., description="Steps to implement the recommendation")
    expected_outcome: str = Field(..., description="Expected outcome")


class RecommendationsResponse(BaseModel):
    """Response schema for personalized recommendations."""
    
    title: str = Field(..., description="Recommendations title")
    recommendations: List[RecommendationItem] = Field(..., description="Prioritized recommendations")
    priority_order: List[str] = Field(..., description="Recommendation titles in priority order")
    
    model_config = {"json_schema_extra": {"example": {
        "title": "Personalized Recommendations",
        "recommendations": [
            {
                "title": "Implement time blocking",
                "impact": "high",
                "implementation_steps": [
                    "Schedule 2-hour focused work blocks",
                    "Block calendar for deep work",
                    "Disable notifications during blocks"
                ],
                "expected_outcome": "Increase focus score by 10-15 points"
            }
        ],
        "priority_order": [
            "Implement time blocking",
            "Reduce social media usage",
            "Optimize meeting schedule"
        ]
    }}}


class ChatMessage(BaseModel):
    """Chat message in conversation."""
    
    role: str = Field(..., description="Message role (user/assistant)")
    content: str = Field(..., description="Message content")
    timestamp: Optional[datetime] = Field(None, description="Message timestamp")


class ChatResponse(BaseModel):
    """Response schema for AI chat interactions."""
    
    message: str = Field(..., description="AI response message")
    context_used: bool = Field(..., description="Whether productivity context was used")
    suggestions: List[str] = Field(default_factory=list, description="Additional suggestions or follow-up questions")
    
    model_config = {"json_schema_extra": {"example": {
        "message": "Based on your productivity data, you're spending 30% of your time on social media. Consider setting time limits for these platforms.",
        "context_used": True,
        "suggestions": [
            "Would you like tips on reducing social media usage?",
            "Should I analyze your peak productivity hours?"
        ]
    }}}


class ChatRequest(BaseModel):
    """Request schema for AI chat."""
    
    message: str = Field(..., min_length=1, max_length=1000, description="User message")
    conversation_history: Optional[List[ChatMessage]] = Field(default_factory=list, description="Conversation history")


class ConversationResponse(BaseModel):
    """Response schema for conversation load/save operations."""
    
    messages: List[ChatMessage] = Field(..., description="Conversation messages")
    suggested_questions: List[str] = Field(default_factory=list, description="Suggested follow-up questions")
    last_message_at: Optional[datetime] = Field(None, description="Timestamp of last message")
