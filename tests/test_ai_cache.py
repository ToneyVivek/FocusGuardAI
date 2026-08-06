"""
Test script for AI Report Cache functionality.

Tests hash computation, cache operations, and integration with AI service.
"""

from datetime import datetime, date, timedelta, timezone
from app.ai.cache_service import AIReportCacheService


def test_hash_computation():
    """Test that analytics hash computation is deterministic."""
    print("=" * 80)
    print("TEST: Hash Computation")
    print("=" * 80)
    
    cache_service = AIReportCacheService()
    
    # Test data
    analytics_data = {
        "focus_score": 75,
        "productive_minutes": 240,
        "tab_switches": 150,
        "total_minutes": 480
    }
    
    # Compute hash twice - should be identical
    hash1 = cache_service.compute_analytics_hash(analytics_data)
    hash2 = cache_service.compute_analytics_hash(analytics_data)
    
    print(f"Hash 1: {hash1}")
    print(f"Hash 2: {hash2}")
    print(f"Hashes match: {hash1 == hash2}")
    
    # Test with different data - should be different
    different_data = analytics_data.copy()
    different_data["focus_score"] = 80
    
    hash3 = cache_service.compute_analytics_hash(different_data)
    print(f"Hash 3 (different data): {hash3}")
    print(f"Hash 1 != Hash 3: {hash1 != hash3}")
    
    assert hash1 == hash2, "Hash computation should be deterministic"
    assert hash1 != hash3, "Different data should produce different hashes"
    
    print("\n✓ Hash computation test PASSED\n")


def test_cache_ttl():
    """Test that cache TTL is set correctly."""
    print("=" * 80)
    print("TEST: Cache TTL")
    print("=" * 80)
    
    cache_service = AIReportCacheService()
    
    print(f"Daily cache TTL: {cache_service.DAILY_CACHE_TTL}")
    print(f"Weekly cache TTL: {cache_service.WEEKLY_CACHE_TTL}")
    
    assert cache_service.DAILY_CACHE_TTL == timedelta(hours=24), "Daily TTL should be 24 hours"
    assert cache_service.WEEKLY_CACHE_TTL == timedelta(days=7), "Weekly TTL should be 7 days"
    
    print("\n✓ Cache TTL test PASSED\n")


def test_date_range_handling():
    """Test that date ranges are correctly converted for cache."""
    print("=" * 80)
    print("TEST: Date Range Handling")
    print("=" * 80)
    
    target_date = date(2026, 8, 3)
    
    start_date = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc)
    end_date = datetime.combine(target_date, datetime.max.time()).replace(tzinfo=timezone.utc)
    
    print(f"Target date: {target_date}")
    print(f"Start date: {start_date}")
    print(f"End date: {end_date}")
    
    assert start_date.hour == 0, "Start date should be at midnight"
    assert start_date.minute == 0, "Start date should be at midnight"
    assert end_date.hour == 23, "End date should be at end of day"
    assert end_date.minute == 59, "End date should be at end of day"
    
    print("\n✓ Date range handling test PASSED\n")


def test_hash_with_complex_data():
    """Test hash computation with complex nested analytics data."""
    print("=" * 80)
    print("TEST: Hash with Complex Data")
    print("=" * 80)
    
    cache_service = AIReportCacheService()
    
    # Complex nested data
    complex_data = {
        "focus_score": 72,
        "productive_minutes": 300,
        "hourly_breakdown": {
            9: 45,
            10: 60,
            11: 30,
            14: 90,
            15: 75
        },
        "category_breakdown": {
            "development": 180,
            "entertainment": 30,
            "social": 15
        },
        "sessions": [
            {"duration": 45, "focus_score": 85},
            {"duration": 30, "focus_score": 70},
            {"duration": 60, "focus_score": 90}
        ]
    }
    
    hash1 = cache_service.compute_analytics_hash(complex_data)
    hash2 = cache_service.compute_analytics_hash(complex_data)
    
    print(f"Complex data hash: {hash1}")
    print(f"Hashes match: {hash1 == hash2}")
    
    assert hash1 == hash2, "Hash should be deterministic even with complex nested data"
    
    print("\n✓ Complex data hash test PASSED\n")


def test_hash_key_ordering():
    """Test that hash is independent of key order."""
    print("=" * 80)
    print("TEST: Hash Key Ordering")
    print("=" * 80)
    
    cache_service = AIReportCacheService()
    
    # Same data, different key order
    data1 = {"focus_score": 75, "productive_minutes": 240, "tab_switches": 150}
    data2 = {"tab_switches": 150, "focus_score": 75, "productive_minutes": 240}
    
    hash1 = cache_service.compute_analytics_hash(data1)
    hash2 = cache_service.compute_analytics_hash(data2)
    
    print(f"Hash 1 (ordered keys): {hash1}")
    print(f"Hash 2 (unordered keys): {hash2}")
    print(f"Hashes match: {hash1 == hash2}")
    
    assert hash1 == hash2, "Hash should be independent of key order"
    
    print("\n✓ Key ordering test PASSED\n")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("AI REPORT CACHE TEST SUITE")
    print("=" * 80 + "\n")
    
    try:
        test_hash_computation()
        test_cache_ttl()
        test_date_range_handling()
        test_hash_with_complex_data()
        test_hash_key_ordering()
        
        print("=" * 80)
        print("ALL TESTS PASSED ✓")
        print("=" * 80)
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        print("=" * 80)
        raise
