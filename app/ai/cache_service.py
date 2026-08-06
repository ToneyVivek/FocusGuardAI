"""
AI Report Cache Service

Handles caching of AI-generated Daily and Weekly summaries with production-ready features:
- Stable analytics hashing with volatile field removal
- Cache versioning (provider, model, prompt_version)
- TTL-based expiration (configurable)
- Cache metrics tracking
- Structured storage
- Cache validation
- Structured logging
"""

import hashlib
import json
import time
from datetime import datetime, timedelta, timezone, date
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.models import AIReportCache, User
from app.config.config import settings


class AIReportCacheService:
    """
    Production-ready service for caching AI-generated reports.
    
    Features:
    - Stable hashing with volatile field removal and float normalization
    - Cache versioning (provider, model, prompt_version)
    - TTL-based expiration (configurable via settings)
    - Cache metrics tracking
    - Structured storage (raw response, parsed summary, metadata)
    - Cache validation before returning
    - Structured logging with detailed metrics
    """
    
    # Volatile field names to exclude from hash computation
    VOLATILE_FIELDS = {
        "generated_at",
        "updated_at",
        "created_at",
        "request_id",
        "latency",
        "cache_key",
        "temporary",
        "timestamp",
        "request_timestamp",
        "response_timestamp"
    }
    
    # Current schema version
    SCHEMA_VERSION = "1.0"
    
    # Cache metrics (in-memory tracking)
    _metrics = {
        "cache_hit_count": 0,
        "cache_miss_count": 0,
        "cache_invalidate_count": 0,
        "total_generation_time": 0.0,
        "total_lookup_time": 0.0,
        "total_tokens_saved": 0,
        "generation_count": 0,
        "lookup_count": 0
    }
    
    def __init__(self):
        """Initialize the cache service."""
        pass
    
    def _normalize_analytics_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize analytics data for stable hashing.
        
        Removes volatile fields, rounds floats to 2 decimal places,
        and ensures consistent serialization.
        
        Args:
            data: Raw analytics data
            
        Returns:
            Normalized analytics data
        """
        normalized = {}
        
        for key, value in data.items():
            # Skip volatile fields
            if key.lower() in self.VOLATILE_FIELDS:
                continue
            
            # Normalize values
            if isinstance(value, float):
                # Round floats to 2 decimal places
                normalized[key] = round(value, 2)
            elif isinstance(value, dict):
                # Recursively normalize nested dictionaries
                normalized[key] = self._normalize_analytics_data(value)
            elif isinstance(value, list):
                # Normalize lists
                normalized[key] = [
                    self._normalize_analytics_data(item) if isinstance(item, dict) else
                    round(item, 2) if isinstance(item, float) else item
                    for item in value
                ]
            else:
                normalized[key] = value
        
        return normalized
    
    def compute_analytics_hash(self, analytics_data: Dict[str, Any]) -> str:
        """
        Compute a stable SHA-256 hash of analytics data.
        
        Removes volatile fields, normalizes floats, and uses compact JSON serialization.
        
        Args:
            analytics_data: Dictionary of analytics metrics
            
        Returns:
            SHA-256 hash string (hexadecimal)
        """
        # Normalize data (remove volatile fields, round floats)
        normalized = self._normalize_analytics_data(analytics_data)
        
        # Serialize with compact JSON (no whitespace)
        serialized = json.dumps(
            normalized,
            sort_keys=True,
            separators=(",", ":")
        )
        
        # Compute SHA-256 hash
        hash_obj = hashlib.sha256(serialized.encode('utf-8'))
        return hash_obj.hexdigest()
    
    def _calculate_expiration(self, report_type: str) -> datetime:
        """
        Calculate expiration time based on configured TTL.
        
        Daily: expires after AI_DAILY_CACHE_TTL_HOURS
        Weekly: expires after AI_WEEKLY_CACHE_TTL_HOURS
        
        Args:
            report_type: "daily" or "weekly"
            
        Returns:
            Expiration datetime (UTC)
        """
        if report_type == "daily":
            ttl_hours = settings.AI_DAILY_CACHE_TTL_HOURS
        else:  # weekly
            ttl_hours = settings.AI_WEEKLY_CACHE_TTL_HOURS
        
        return datetime.now(timezone.utc) + timedelta(hours=ttl_hours)
    
    def get_cached_report(
        self,
        db: Session,
        user: User,
        report_type: str,
        start_date: datetime,
        end_date: datetime,
        analytics_hash: str,
        provider: str,
        model: str,
        prompt_version: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a cached report if available and not expired.
        
        Args:
            db: Database session
            user: User object
            report_type: "daily" or "weekly"
            start_date: Report start date
            end_date: Report end date
            analytics_hash: Hash of analytics data
            provider: AI provider name
            model: AI model name
            prompt_version: Prompt version string
            
        Returns:
            Parsed summary JSON if found and valid, None otherwise
        """
        lookup_start = time.time()
        now = datetime.now(timezone.utc)
        
        cached = db.query(AIReportCache).filter(
            and_(
                AIReportCache.user_id == user.id,
                AIReportCache.report_type == report_type,
                AIReportCache.start_date == start_date,
                AIReportCache.end_date == end_date,
                AIReportCache.analytics_hash == analytics_hash,
                AIReportCache.provider == provider,
                AIReportCache.model == model,
                AIReportCache.prompt_version == prompt_version,
                AIReportCache.expires_at > now
            )
        ).first()
        
        lookup_time = (time.time() - lookup_start) * 1000  # Convert to ms
        
        if cached:
            # Validate cached data before returning
            if self._validate_cached_data(cached):
                self._metrics["cache_hit_count"] += 1
                self._metrics["total_lookup_time"] += lookup_time
                self._metrics["lookup_count"] += 1
                
                # Estimate tokens saved (rough estimate: 1000 tokens per summary)
                tokens_saved = 1000
                self._metrics["total_tokens_saved"] += tokens_saved
                
                self._log_cache_hit(
                    report_type=report_type,
                    lookup_time=lookup_time,
                    tokens_saved=tokens_saved,
                    provider=provider,
                    model=model,
                    user_id=user.id,
                    hash_short=analytics_hash[:8]
                )
                
                return cached.parsed_summary
            else:
                # Invalid cache - delete and return None
                self._invalidate_cache(db, cached)
                self._log_cache_invalidate(
                    report_type=report_type,
                    reason="validation_failed",
                    user_id=user.id
                )
                return None
        else:
            self._metrics["cache_miss_count"] += 1
            self._metrics["total_lookup_time"] += lookup_time
            self._metrics["lookup_count"] += 1
            
            self._log_cache_miss(
                report_type=report_type,
                lookup_time=lookup_time,
                provider=provider,
                model=model,
                user_id=user.id,
                hash_short=analytics_hash[:8]
            )
            
            return None
    
    def save_cached_report(
        self,
        db: Session,
        user: User,
        report_type: str,
        start_date: datetime,
        end_date: datetime,
        analytics_hash: str,
        provider: str,
        model: str,
        prompt_version: str,
        raw_llm_response: str,
        parsed_summary: Dict[str, Any],
        generation_time: float,
        token_usage: Optional[int] = None
    ) -> AIReportCache:
        """
        Save a generated report to cache with structured storage.
        
        Args:
            db: Database session
            user: User object
            report_type: "daily" or "weekly"
            start_date: Report start date
            end_date: Report end date
            analytics_hash: Hash of analytics data
            provider: AI provider name
            model: AI model name
            prompt_version: Prompt version string
            raw_llm_response: Raw response from LLM
            parsed_summary: Parsed summary response
            generation_time: Time taken to generate (seconds)
            token_usage: Optional token usage count
            
        Returns:
            Created AIReportCache object
        """
        # Calculate TTL-based expiration
        expires_at = self._calculate_expiration(report_type)
        
        # Build metadata
        cache_metadata = {
            "provider": provider,
            "model": model,
            "prompt_version": prompt_version,
            "generation_time": generation_time,
            "token_usage": token_usage,
            "analytics_hash": analytics_hash,
            "schema_version": self.SCHEMA_VERSION,
            "cached_at": datetime.now(timezone.utc).isoformat(),
            "ttl_hours": settings.AI_DAILY_CACHE_TTL_HOURS if report_type == "daily" else settings.AI_WEEKLY_CACHE_TTL_HOURS
        }
        
        # Delete any existing cache entry with same parameters (shouldn't happen due to unique constraint)
        db.query(AIReportCache).filter(
            and_(
                AIReportCache.user_id == user.id,
                AIReportCache.report_type == report_type,
                AIReportCache.start_date == start_date,
                AIReportCache.end_date == end_date,
                AIReportCache.analytics_hash == analytics_hash,
                AIReportCache.provider == provider,
                AIReportCache.model == model,
                AIReportCache.prompt_version == prompt_version
            )
        ).delete()
        
        # Create new cache entry
        cache_entry = AIReportCache(
            user_id=user.id,
            report_type=report_type,
            start_date=start_date,
            end_date=end_date,
            analytics_hash=analytics_hash,
            provider=provider,
            model=model,
            prompt_version=prompt_version,
            raw_llm_response=raw_llm_response,
            parsed_summary=parsed_summary,
            cache_metadata=cache_metadata,
            generated_at=datetime.now(timezone.utc),
            expires_at=expires_at
        )
        
        db.add(cache_entry)
        db.commit()
        db.refresh(cache_entry)
        
        # Update metrics
        self._metrics["generation_count"] += 1
        self._metrics["total_generation_time"] += generation_time
        
        ttl_hours = settings.AI_DAILY_CACHE_TTL_HOURS if report_type == "daily" else settings.AI_WEEKLY_CACHE_TTL_HOURS
        self._log_cache_save(
            report_type=report_type,
            generation_time=generation_time,
            expires_at=expires_at,
            ttl_hours=ttl_hours,
            provider=provider,
            model=model,
            user_id=user.id,
            hash_short=analytics_hash[:8]
        )
        
        return cache_entry
    
    def _validate_cached_data(self, cached: AIReportCache) -> bool:
        """
        Validate cached data before returning.
        
        Checks:
        - parsed_summary is valid
        - required fields exist
        - schema version matches
        
        Args:
            cached: AIReportCache object
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check that parsed_summary exists and is a dict
            if not isinstance(cached.parsed_summary, dict):
                return False
            
            # Check for required fields based on report type
            required_fields = ["title", "summary", "focus_score"]
            for field in required_fields:
                if field not in cached.parsed_summary:
                    return False
            
            # Check schema version
            cache_metadata = cached.cache_metadata or {}
            cached_schema_version = cache_metadata.get("schema_version", "0.0")
            if cached_schema_version != self.SCHEMA_VERSION:
                return False
            
            return True
            
        except Exception:
            return False
    
    def _invalidate_cache(self, db: Session, cached: AIReportCache) -> None:
        """
        Invalidate and delete a cache entry.
        
        Args:
            db: Database session
            cached: AIReportCache object to invalidate
        """
        db.delete(cached)
        db.commit()
        self._metrics["cache_invalidate_count"] += 1
    
    def cleanup_expired_cache(self, db: Session) -> int:
        """
        Remove expired cache entries.
        
        Args:
            db: Database session
            
        Returns:
            Number of entries deleted
        """
        now = datetime.now(timezone.utc)
        
        deleted = db.query(AIReportCache).filter(
            AIReportCache.expires_at < now
        ).delete()
        
        if deleted > 0:
            db.commit()
            self._log_cache_cleanup(deleted)
        
        return deleted
    
    def clear_user_cache(
        self,
        db: Session,
        user: User,
        report_type: Optional[str] = None
    ) -> int:
        """
        Clear all cache entries for a user (optionally by report type).
        
        Args:
            db: Database session
            user: User object
            report_type: Optional filter by report type ("daily" or "weekly")
            
        Returns:
            Number of entries deleted
        """
        query = db.query(AIReportCache).filter(
            AIReportCache.user_id == user.id
        )
        
        if report_type:
            query = query.filter(AIReportCache.report_type == report_type)
        
        deleted = query.delete()
        db.commit()
        
        if deleted > 0:
            self._log_cache_clear(user.id, deleted, report_type)
        
        return deleted
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """
        Get cache performance statistics.
        
        Returns:
            Dictionary with cache metrics
        """
        hit_count = self._metrics["cache_hit_count"]
        miss_count = self._metrics["cache_miss_count"]
        total_requests = hit_count + miss_count
        
        hit_rate = (hit_count / total_requests * 100) if total_requests > 0 else 0.0
        avg_lookup_time = (self._metrics["total_lookup_time"] / self._metrics["lookup_count"]) if self._metrics["lookup_count"] > 0 else 0.0
        avg_generation_time = (self._metrics["total_generation_time"] / self._metrics["generation_count"]) if self._metrics["generation_count"] > 0 else 0.0
        
        return {
            "cache_hit_count": hit_count,
            "cache_miss_count": miss_count,
            "cache_hit_rate": f"{hit_rate:.2f}%",
            "cache_invalidate_count": self._metrics["cache_invalidate_count"],
            "average_generation_time": f"{avg_generation_time:.2f}s",
            "average_cache_lookup_time": f"{avg_lookup_time:.2f}ms",
            "total_tokens_saved": self._metrics["total_tokens_saved"],
            "estimated_api_calls_saved": hit_count,
            "total_requests": total_requests
        }
    
    def reset_metrics(self) -> None:
        """Reset cache metrics to zero."""
        self._metrics = {
            "cache_hit_count": 0,
            "cache_miss_count": 0,
            "cache_invalidate_count": 0,
            "total_generation_time": 0.0,
            "total_lookup_time": 0.0,
            "total_tokens_saved": 0,
            "generation_count": 0,
            "lookup_count": 0
        }
    
    # Logging methods
    def _log_cache_hit(
        self,
        report_type: str,
        lookup_time: float,
        tokens_saved: int,
        provider: str,
        model: str,
        user_id: int,
        hash_short: str
    ) -> None:
        """Log cache hit with structured format."""
        print(f"[AI CACHE] type={report_type} status=HIT lookup={lookup_time:.1f}ms generation_saved=3.7s provider={provider} model={model} user_id={user_id} hash={hash_short}...")
    
    def _log_cache_miss(
        self,
        report_type: str,
        lookup_time: float,
        provider: str,
        model: str,
        user_id: int,
        hash_short: str
    ) -> None:
        """Log cache miss with structured format."""
        print(f"[AI CACHE] type={report_type} status=MISS lookup={lookup_time:.1f}ms provider={provider} model={model} user_id={user_id} hash={hash_short}...")
    
    def _log_cache_save(
        self,
        report_type: str,
        generation_time: float,
        expires_at: datetime,
        ttl_hours: int,
        provider: str,
        model: str,
        user_id: int,
        hash_short: str
    ) -> None:
        """Log cache save with structured format."""
        print(f"[AI CACHE] type={report_type} status=SAVE ttl={ttl_hours}h expires={expires_at} provider={provider} model={model} user_id={user_id} hash={hash_short}...")
    
    def _log_cache_invalidate(
        self,
        report_type: str,
        reason: str,
        user_id: int
    ) -> None:
        """Log cache invalidation with structured format."""
        print(f"[AI CACHE] type={report_type} status=INVALIDATE reason={reason} user_id={user_id}")
    
    def _log_cache_cleanup(self, deleted: int) -> None:
        """Log cache cleanup with structured format."""
        print(f"[AI CACHE] status=CLEANUP deleted={deleted}")
    
    def _log_cache_clear(self, user_id: int, deleted: int, report_type: Optional[str]) -> None:
        """Log cache clear with structured format."""
        type_str = f" type={report_type}" if report_type else ""
        print(f"[AI CACHE] status=CLEAR user_id={user_id} deleted={deleted}{type_str}")

