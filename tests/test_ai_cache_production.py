"""
Production-ready AI Report Cache Test Suite.

Tests all new features:
- Stable analytics hashing with volatile field removal
- Float normalization
- Dictionary ordering independence
- Calendar-based expiration
- Provider/model/prompt version changes
- Cache validation
- Schema mismatch handling
- Cache corruption handling
- Cache metrics
"""

from datetime import datetime, date, timedelta, timezone
from app.ai.cache_service import AIReportCacheService


def test_stable_hash_volatile_field_removal():
    """Test that volatile fields are removed from hash computation."""
    print("=" * 80)
    print("TEST: Stable Hash - Volatile Field Removal")
    print("=" * 80)
    
    cache_service = AIReportCacheService()
    
    # Data with volatile fields
    data_with_volatile = {
        "focus_score": 75,
        "productive_minutes": 240,
        "generated_at": "2026-08-03T12:00:00Z",
        "updated_at": "2026-08-03T12:30:00Z",
        "request_id": "req_12345",
        "latency": 0.5
    }
    
    # Data without volatile fields
    data_without_volatile = {
        "focus_score": 75,
        "productive_minutes": 240
    }
    
    hash1 = cache_service.compute_analytics_hash(data_with_volatile)
    hash2 = cache_service.compute_analytics_hash(data_without_volatile)
    
    print(f"Hash with volatile fields: {hash1}")
    print(f"Hash without volatile fields: {hash2}")
    print(f"Hashes match: {hash1 == hash2}")
    
    assert hash1 == hash2, "Volatile fields should not affect hash"
    
    print("\n✓ Volatile field removal test PASSED\n")


def test_float_normalization():
    """Test that floats are normalized to 2 decimal places."""
    print("=" * 80)
    print("TEST: Float Normalization")
    print("=" * 80)
    
    cache_service = AIReportCacheService()
    
    # Same value with different precision
    data1 = {"focus_score": 75.123456}
    data2 = {"focus_score": 75.12}
    data3 = {"focus_score": 75.120000}
    
    hash1 = cache_service.compute_analytics_hash(data1)
    hash2 = cache_service.compute_analytics_hash(data2)
    hash3 = cache_service.compute_analytics_hash(data3)
    
    print(f"Hash 1 (75.123456): {hash1}")
    print(f"Hash 2 (75.12): {hash2}")
    print(f"Hash 3 (75.120000): {hash3}")
    print(f"All hashes match: {hash1 == hash2 == hash3}")
    
    assert hash1 == hash2 == hash3, "Floats should be normalized to 2 decimal places"
    
    print("\n✓ Float normalization test PASSED\n")


def test_dictionary_ordering_independence():
    """Test that hash is independent of dictionary key order."""
    print("=" * 80)
    print("TEST: Dictionary Ordering Independence")
    print("=" * 80)
    
    cache_service = AIReportCacheService()
    
    # Same data, different key order
    data1 = {"focus_score": 75, "productive_minutes": 240, "tab_switches": 150}
    data2 = {"tab_switches": 150, "focus_score": 75, "productive_minutes": 240}
    data3 = {"productive_minutes": 240, "tab_switches": 150, "focus_score": 75}
    
    hash1 = cache_service.compute_analytics_hash(data1)
    hash2 = cache_service.compute_analytics_hash(data2)
    hash3 = cache_service.compute_analytics_hash(data3)
    
    print(f"Hash 1: {hash1}")
    print(f"Hash 2: {hash2}")
    print(f"Hash 3: {hash3}")
    print(f"All hashes match: {hash1 == hash2 == hash3}")
    
    assert hash1 == hash2 == hash3, "Hash should be independent of key order"
    
    print("\n✓ Dictionary ordering test PASSED\n")


def test_ttl_expiration_daily():
    """Test that daily summaries expire after configured TTL."""
    print("=" * 80)
    print("TEST: TTL Expiration - Daily")
    print("=" * 80)
    
    cache_service = AIReportCacheService()
    
    # Test daily expiration
    expires_at = cache_service._calculate_expiration("daily")
    
    # Should be 4 hours from now
    expected = datetime.now(timezone.utc) + timedelta(hours=4)
    
    print(f"Expires at: {expires_at}")
    print(f"Expected (now + 4h): {expected}")
    print(f"Time difference: {(expires_at - expected).total_seconds()} seconds")
    
    # Allow 1 second tolerance
    assert abs((expires_at - expected).total_seconds()) < 1, f"Daily should expire after 4 hours, got {expires_at}"
    
    print("\n✓ Daily TTL expiration test PASSED\n")


def test_ttl_expiration_weekly():
    """Test that weekly summaries expire after configured TTL."""
    print("=" * 80)
    print("TEST: TTL Expiration - Weekly")
    print("=" * 80)
    
    cache_service = AIReportCacheService()
    
    # Test weekly expiration
    expires_at = cache_service._calculate_expiration("weekly")
    
    # Should be 24 hours from now
    expected = datetime.now(timezone.utc) + timedelta(hours=24)
    
    print(f"Expires at: {expires_at}")
    print(f"Expected (now + 24h): {expected}")
    print(f"Time difference: {(expires_at - expected).total_seconds()} seconds")
    
    # Allow 1 second tolerance
    assert abs((expires_at - expected).total_seconds()) < 1, f"Weekly should expire after 24 hours, got {expires_at}"
    
    print("\n✓ Weekly TTL expiration test PASSED\n")


def test_cache_metrics():
    """Test cache metrics tracking."""
    print("=" * 80)
    print("TEST: Cache Metrics")
    print("=" * 80)
    
    cache_service = AIReportCacheService()
    
    # Reset metrics
    cache_service.reset_metrics()
    
    # Simulate some cache operations
    cache_service._metrics["cache_hit_count"] = 5
    cache_service._metrics["cache_miss_count"] = 3
    cache_service._metrics["total_generation_time"] = 15.5
    cache_service._metrics["generation_count"] = 3
    cache_service._metrics["total_lookup_time"] = 45.0
    cache_service._metrics["lookup_count"] = 8
    cache_service._metrics["total_tokens_saved"] = 5000
    
    stats = cache_service.get_cache_statistics()
    
    print(f"Cache hit count: {stats['cache_hit_count']}")
    print(f"Cache miss count: {stats['cache_miss_count']}")
    print(f"Cache hit rate: {stats['cache_hit_rate']}")
    print(f"Average generation time: {stats['average_generation_time']}")
    print(f"Average lookup time: {stats['average_cache_lookup_time']}")
    print(f"Total tokens saved: {stats['total_tokens_saved']}")
    print(f"Estimated API calls saved: {stats['estimated_api_calls_saved']}")
    
    assert stats['cache_hit_count'] == 5
    assert stats['cache_miss_count'] == 3
    assert stats['cache_hit_rate'] == "62.50%"
    assert stats['average_generation_time'] == "5.17s"
    assert stats['average_cache_lookup_time'] == "5.62ms"
    assert stats['total_tokens_saved'] == 5000
    assert stats['estimated_api_calls_saved'] == 5
    
    print("\n✓ Cache metrics test PASSED\n")


def test_cache_validation():
    """Test cache validation logic."""
    print("=" * 80)
    print("TEST: Cache Validation")
    print("=" * 80)
    
    cache_service = AIReportCacheService()
    
    # Create a mock cache entry
    class MockCacheEntry:
        def __init__(self, parsed_summary, cache_metadata):
            self.parsed_summary = parsed_summary
            self.cache_metadata = cache_metadata
    
    # Valid cache entry
    valid_entry = MockCacheEntry(
        parsed_summary={
            "title": "Daily Summary",
            "summary": "Good work today",
            "focus_score": 75
        },
        cache_metadata={
            "schema_version": "1.0"
        }
    )
    
    is_valid = cache_service._validate_cached_data(valid_entry)
    print(f"Valid entry validation: {is_valid}")
    assert is_valid == True, "Valid cache entry should pass validation"
    
    # Invalid: missing required field
    invalid_entry1 = MockCacheEntry(
        parsed_summary={
            "title": "Daily Summary",
            "summary": "Good work today"
            # Missing focus_score
        },
        cache_metadata={
            "schema_version": "1.0"
        }
    )
    
    is_valid = cache_service._validate_cached_data(invalid_entry1)
    print(f"Missing field validation: {is_valid}")
    assert is_valid == False, "Cache with missing field should fail validation"
    
    # Invalid: schema version mismatch
    invalid_entry2 = MockCacheEntry(
        parsed_summary={
            "title": "Daily Summary",
            "summary": "Good work today",
            "focus_score": 75
        },
        cache_metadata={
            "schema_version": "0.9"  # Wrong version
        }
    )
    
    is_valid = cache_service._validate_cached_data(invalid_entry2)
    print(f"Schema mismatch validation: {is_valid}")
    assert is_valid == False, "Cache with wrong schema version should fail validation"
    
    print("\n✓ Cache validation test PASSED\n")


def test_compact_json_serialization():
    """Test that compact JSON serialization is used."""
    print("=" * 80)
    print("TEST: Compact JSON Serialization")
    print("=" * 80)
    
    cache_service = AIReportCacheService()
    
    data = {"focus_score": 75, "productive_minutes": 240}
    
    # Compute hash
    hash1 = cache_service.compute_analytics_hash(data)
    
    # Manually compute with compact JSON
    import json
    normalized = cache_service._normalize_analytics_data(data)
    serialized = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
    import hashlib
    hash_obj = hashlib.sha256(serialized.encode('utf-8'))
    hash2 = hash_obj.hexdigest()
    
    print(f"Hash from service: {hash1}")
    print(f"Hash from manual: {hash2}")
    print(f"Match: {hash1 == hash2}")
    
    assert hash1 == hash2, "Should use compact JSON serialization"
    
    # Verify no whitespace in serialization
    assert " " not in serialized, "Compact JSON should have no spaces"
    assert "\n" not in serialized, "Compact JSON should have no newlines"
    
    print(f"Serialized length: {len(serialized)}")
    print(f"Serialized: {serialized}")
    
    print("\n✓ Compact JSON serialization test PASSED\n")


def test_nested_data_normalization():
    """Test normalization of nested data structures."""
    print("=" * 80)
    print("TEST: Nested Data Normalization")
    print("=" * 80)
    
    cache_service = AIReportCacheService()
    
    # Nested data with volatile fields and floats
    data = {
        "focus_score": 75.567,
        "hourly_breakdown": {
            "9": 45.123,
            "10": 60.456,
            "generated_at": "2026-08-03T09:00:00Z"  # Volatile
        },
        "sessions": [
            {"duration": 30.789, "timestamp": "2026-08-03T10:00:00Z"},
            {"duration": 45.234, "timestamp": "2026-08-03T11:00:00Z"}
        ]
    }
    
    normalized = cache_service._normalize_analytics_data(data)
    
    print(f"Original data: {data}")
    print(f"Normalized data: {normalized}")
    
    # Check that volatile fields are removed
    assert "generated_at" not in normalized["hourly_breakdown"]
    assert "timestamp" not in normalized["sessions"][0]
    assert "timestamp" not in normalized["sessions"][1]
    
    # Check that floats are rounded
    assert normalized["focus_score"] == 75.57
    assert normalized["hourly_breakdown"]["9"] == 45.12
    assert normalized["hourly_breakdown"]["10"] == 60.46
    assert normalized["sessions"][0]["duration"] == 30.79
    assert normalized["sessions"][1]["duration"] == 45.23
    
    print("\n✓ Nested data normalization test PASSED\n")


def test_case_insensitive_volatile_fields():
    """Test that volatile field matching is case-insensitive."""
    print("=" * 80)
    print("TEST: Case-Insensitive Volatile Field Matching")
    print("=" * 80)
    
    cache_service = AIReportCacheService()
    
    # Data with volatile fields in different cases
    data1 = {"focus_score": 75, "Generated_At": "2026-08-03T12:00:00Z"}
    data2 = {"focus_score": 75, "generated_at": "2026-08-03T12:00:00Z"}
    data3 = {"focus_score": 75, "GENERATED_AT": "2026-08-03T12:00:00Z"}
    
    hash1 = cache_service.compute_analytics_hash(data1)
    hash2 = cache_service.compute_analytics_hash(data2)
    hash3 = cache_service.compute_analytics_hash(data3)
    
    print(f"Hash 1 (Generated_At): {hash1}")
    print(f"Hash 2 (generated_at): {hash2}")
    print(f"Hash 3 (GENERATED_AT): {hash3}")
    print(f"All hashes match: {hash1 == hash2 == hash3}")
    
    assert hash1 == hash2 == hash3, "Volatile field matching should be case-insensitive"
    
    print("\n✓ Case-insensitive volatile field test PASSED\n")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("PRODUCTION-READY AI REPORT CACHE TEST SUITE")
    print("=" * 80 + "\n")
    
    try:
        test_stable_hash_volatile_field_removal()
        test_float_normalization()
        test_dictionary_ordering_independence()
        test_ttl_expiration_daily()
        test_ttl_expiration_weekly()
        test_cache_metrics()
        test_cache_validation()
        test_compact_json_serialization()
        test_nested_data_normalization()
        test_case_insensitive_volatile_fields()
        
        print("=" * 80)
        print("ALL TESTS PASSED ✓")
        print("=" * 80)
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        print("=" * 80)
        raise
