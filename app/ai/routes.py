"""
AI API Routes

API endpoints for AI-powered productivity features.
"""

from datetime import date, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query, status, Request
from sqlalchemy.orm import Session

from app.dependencies.deps import get_current_user, get_db
from app.middleware.rate_limit import limiter
from app.models.models import User
from app.ai.service import AIService
from app.ai.provider_manager import ProviderManager
from app.ai.schemas import (
    DailySummaryResponse,
    WeeklySummaryResponse,
    InsightsResponse,
    RecommendationsResponse,
    ChatResponse,
    ChatRequest,
    ConversationResponse,
)

router = APIRouter(prefix="/ai", tags=["AI"])
ai_service = AIService()
provider_manager = ProviderManager()


@router.get("/test")
async def test_gemini():
    """
    Diagnostic endpoint to test Gemini provider directly.
    
    Calls Gemini with a minimal prompt to isolate the provider
    from analytics, context builder, and schemas.
    
    No authentication required for testing.
    """
    from app.ai.providers.gemini_provider import GeminiProvider
    
    print("[TEST] Gemini diagnostic endpoint called")
    
    try:
        provider = GeminiProvider()
        print("[TEST] GeminiProvider initialized")
        
        prompt = "Reply with exactly: Gemini is working."
        print(f"[TEST] Sending prompt: {prompt}")
        
        response = await provider.generate_completion(prompt=prompt)
        print(f"[TEST] Response received: {response}")
        
        return {
            "success": True,
            "provider": "gemini",
            "model": provider.model_name,
            "response": response
        }
    except Exception as e:
        print(f"[TEST] Exception: {type(e).__name__}: {str(e)}")
        import traceback
        print(f"[TEST] Traceback:\n{traceback.format_exc()}")
        return {
            "success": False,
            "error": str(e),
            "exception_type": type(e).__name__
        }


@router.get("/provider/status")
async def get_provider_status(current_user: User = Depends(get_current_user)):
    """
    Get AI provider status and statistics.
    
    Returns information about:
    - Current active provider
    - Provider health status
    - Request statistics
    - Quota failures
    - Average latency
    
    Authentication: JWT token required (admin only in production)
    """
    # TODO: Add admin role check for production
    return provider_manager.get_status()


@router.get("/summary/daily", response_model=DailySummaryResponse)
@limiter.limit("10/minute")
async def get_daily_summary(
    request: Request,
    target_date: Optional[str] = Query(
        default=None,
        description="Target date in ISO format (YYYY-MM-DD). Defaults to today."
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate a daily productivity summary using AI.
    
    Analyzes the user's productivity data for a specific day and provides:
    - Concise summary of the day
    - Key highlights
    - Recommendations for tomorrow
    - Overall assessment
    
    Authentication: JWT token required
    Rate Limiting: 10 requests per minute
    """
    parsed_date = None
    if target_date:
        try:
            parsed_date = date.fromisoformat(target_date)
        except ValueError:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid date format: {target_date}. Use ISO format (YYYY-MM-DD)."
            )
    else:
        parsed_date = date.today()
    
    return await ai_service.generate_daily_summary(db, current_user, parsed_date)


@router.get("/summary/weekly", response_model=WeeklySummaryResponse)
@limiter.limit("10/minute")
async def get_weekly_summary(
    request: Request,
    start_date: Optional[str] = Query(
        default=None,
        description="Start date in ISO format (YYYY-MM-DD). Defaults to 7 days ago."
    ),
    end_date: Optional[str] = Query(
        default=None,
        description="End date in ISO format (YYYY-MM-DD). Defaults to today."
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate a weekly productivity review using AI.
    
    Analyzes the user's productivity data for a week and provides:
    - Weekly summary
    - Key highlights from the week
    - Strategic recommendations for next week
    - Overall assessment
    - Specific goal for next week
    
    Authentication: JWT token required
    Rate Limiting: 10 requests per minute
    """
    parsed_start = None
    parsed_end = None
    
    if start_date:
        try:
            parsed_start = date.fromisoformat(start_date)
        except ValueError:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid start_date format: {start_date}. Use ISO format (YYYY-MM-DD)."
            )
    else:
        # Default to Monday of current week
        today = date.today()
        parsed_start = today - timedelta(days=today.weekday())
    
    if end_date:
        try:
            parsed_end = date.fromisoformat(end_date)
        except ValueError:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid end_date format: {end_date}. Use ISO format (YYYY-MM-DD)."
            )
    else:
        # Default to today
        parsed_end = date.today()
    
    return await ai_service.generate_weekly_summary(db, current_user, parsed_start, parsed_end)


@router.get("/insights", response_model=InsightsResponse)
@limiter.limit("10/minute")
async def get_insights(
    request: Request,
    start_date: Optional[str] = Query(
        default=None,
        description="Start date in ISO format (YYYY-MM-DD)."
    ),
    end_date: Optional[str] = Query(
        default=None,
        description="End date in ISO format (YYYY-MM-DD)."
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate AI-powered productivity insights.
    
    Analyzes productivity patterns and provides:
    - Key insights about productivity patterns
    - Identification of time sinks and distractions
    - Analysis of category balance
    - Recommendations to improve focus score
    - Suggestions for better time allocation
    
    Authentication: JWT token required
    Rate Limiting: 10 requests per minute
    """
    parsed_start = None
    parsed_end = None
    
    if start_date:
        try:
            parsed_start = date.fromisoformat(start_date)
        except ValueError:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid start_date format: {start_date}. Use ISO format (YYYY-MM-DD)."
            )
    
    if end_date:
        try:
            parsed_end = date.fromisoformat(end_date)
        except ValueError:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid end_date format: {end_date}. Use ISO format (YYYY-MM-DD)."
            )
    
    return await ai_service.generate_insights(db, current_user, parsed_start, parsed_end)


@router.get("/recommendations", response_model=RecommendationsResponse)
@limiter.limit("10/minute")
async def get_recommendations(
    request: Request,
    start_date: Optional[str] = Query(
        default=None,
        description="Start date in ISO format (YYYY-MM-DD)."
    ),
    end_date: Optional[str] = Query(
        default=None,
        description="End date in ISO format (YYYY-MM-DD)."
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate personalized AI recommendations.
    
    Provides prioritized, actionable recommendations based on:
    - Productivity patterns
    - Time allocation
    - Category balance
    - Focus score analysis
    
    Each recommendation includes:
    - Title and expected impact
    - Implementation steps
    - Expected outcome
    
    Authentication: JWT token required
    Rate Limiting: 10 requests per minute
    """
    parsed_start = None
    parsed_end = None
    
    if start_date:
        try:
            parsed_start = date.fromisoformat(start_date)
        except ValueError:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid start_date format: {start_date}. Use ISO format (YYYY-MM-DD)."
            )
    
    if end_date:
        try:
            parsed_end = date.fromisoformat(end_date)
        except ValueError:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid end_date format: {end_date}. Use ISO format (YYYY-MM-DD)."
            )
    
    return await ai_service.generate_recommendations(db, current_user, parsed_start, parsed_end)


@router.post("/chat", response_model=ChatResponse)
@limiter.limit("20/minute")
async def chat(
    request: Request,
    chat_request: ChatRequest,
    start_date: Optional[str] = Query(
        default=None,
        description="Start date for context in ISO format (YYYY-MM-DD)."
    ),
    end_date: Optional[str] = Query(
        default=None,
        description="End date for context in ISO format (YYYY-MM-DD)."
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Chat with AI productivity coach.
    
    Allows users to ask questions about their productivity and receive
    personalized advice based on their actual data.
    
    The AI uses the user's productivity context to provide relevant,
    data-backed responses.
    
    Authentication: JWT token required
    Rate Limiting: 20 requests per minute
    """
    parsed_start = None
    parsed_end = None
    
    if start_date:
        try:
            parsed_start = date.fromisoformat(start_date)
        except ValueError:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid start_date format: {start_date}. Use ISO format (YYYY-MM-DD)."
            )
    
    if end_date:
        try:
            parsed_end = date.fromisoformat(end_date)
        except ValueError:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid end_date format: {end_date}. Use ISO format (YYYY-MM-DD)."
            )
    
    response = await ai_service.chat(db, current_user, chat_request.message, parsed_start, parsed_end)

    # Save conversation to database
    print(f"[POST CHAT] Saving conversation for user {current_user.id}")
    print(f"[POST CHAT] User message: {chat_request.message[:50]}...")
    print(f"[POST CHAT] AI response: {response.message[:50]}...")
    ai_service.save_conversation(db, current_user, chat_request.message, response.message, response.suggestions)
    print(f"[POST CHAT] Conversation saved successfully")

    return response


@router.get("/conversation", response_model=ConversationResponse)
async def get_conversation(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get the user's latest AI chat conversation.

    Returns the most recent conversation history and suggested questions
    for restoration after page refresh.

    Authentication: JWT token required
    """
    print(f"[GET CONVERSATION] Fetching conversation for user {current_user.id}")
    result = ai_service.get_latest_conversation(db, current_user)
    print(f"[GET CONVERSATION] Conversation ID returned: {result.id if hasattr(result, 'id') else 'N/A'}")
    print(f"[GET CONVERSATION] Message count returned: {len(result.messages)}")
    return result


@router.delete("/conversation")
async def clear_conversation(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Clear the user's AI chat conversation.
    
    Deletes the stored conversation history.
    
    Authentication: JWT token required
    """
    ai_service.clear_conversation(db, current_user)
    return {"message": "Conversation cleared"}
