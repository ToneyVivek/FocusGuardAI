# Analytics Module: Activity UUID Migration Path

## Overview

This document outlines the migration path from the current duplicate detection strategy to a browser-generated activity UUID approach.

## Current Strategy (Version 1)

### Duplicate Detection
- **Key Fields:** `user_id`, `website_domain`, `session_start_time`, `session_end_time`
- **Enforcement:** Database unique constraint `idx_unique_session`
- **Implementation:** `DuplicateDetectionService.check_duplicate()`

### Limitations
- Timestamp precision issues (microsecond variations)
- Network retry edge cases
- No support for offline-to-online sync
- Complex for multi-device scenarios

### Current Implementation
```python
# Database constraint
UNIQUE INDEX idx_unique_session 
(user_id, website_domain, session_start_time, session_end_time)

# Service layer
duplicate_detection_service.check_duplicate(
    user_id=user.id,
    website_domain=activity_in.website_domain,
    session_start_time=activity_in.session_start_time,
    session_end_time=activity_in.session_end_time,
)
```

---

## Future Strategy (Version 2)

### Duplicate Detection
- **Key Field:** `activity_uuid` (browser-generated UUID)
- **Enforcement:** Database unique constraint on `activity_uuid`
- **Implementation:** `DuplicateDetectionService.check_duplicate()` with UUID priority

### Benefits
- Reliable duplicate detection regardless of timing
- Better support for offline-to-online sync
- Simplified multi-device scenarios
- More robust network retry handling

### Future Implementation
```python
# Database constraint
UNIQUE INDEX idx_activity_uuid (activity_uuid)

# Service layer
duplicate_detection_service.check_duplicate(
    activity_uuid=activity_in.activity_uuid,  # Primary
    user_id=user.id,  # Fallback
    website_domain=activity_in.website_domain,  # Fallback
    session_start_time=activity_in.session_start_time,  # Fallback
    session_end_time=activity_in.session_end_time,  # Fallback
)
```

---

## Migration Path

### Phase 1: Database Preparation
**Timeline:** Week 1-2
**Impact:** Backend only, no extension changes

1. **Add `activity_uuid` column to `browser_activities` table**
   ```sql
   ALTER TABLE browser_activities 
   ADD COLUMN activity_uuid UUID;
   
   CREATE INDEX idx_activity_uuid 
   ON browser_activities (activity_uuid);
   ```

2. **Update `BrowserActivity` model**
   ```python
   activity_uuid = Column(UUID(as_uuid=True), nullable=True, index=True)
   ```

3. **Update `BrowserActivityCreate` schema**
   ```python
   activity_uuid: Optional[str] = Field(None, description="Browser-generated UUID")
   ```

4. **Update `BrowserActivityResponse` schema**
   ```python
   activity_uuid: Optional[str]
   ```

5. **Update `DuplicateDetectionService.check_duplicate()`**
   ```python
   def check_duplicate(cls, db, user_id, website_domain, 
                      session_start_time, session_end_time, 
                      activity_uuid=None):
       # Check by UUID first if provided
       if activity_uuid:
           existing = db.query(BrowserActivity).filter(
               BrowserActivity.activity_uuid == activity_uuid
           ).first()
           if existing:
               return existing
       
       # Fall back to current strategy
       existing = db.query(BrowserActivity).filter(
           BrowserActivity.user_id == user_id,
           BrowserActivity.website_domain == website_domain,
           BrowserActivity.session_start_time == session_start_time,
           BrowserActivity.session_end_time == session_end_time,
       ).first()
       return existing
   ```

### Phase 2: Browser Extension Update
**Timeline:** Week 3-4
**Impact:** Browser extension changes

1. **Update browser extension to generate UUIDs**
   ```javascript
   // Generate UUID when session starts
   const activityUuid = crypto.randomUUID();
   
   // Send UUID with activity data
   {
     activity_uuid: activityUuid,
     browser_name: "Chrome",
     website_url: "https://github.com",
     website_domain: "github.com",
     page_title: "GitHub",
     session_start_time: "2026-07-09T10:00:00Z",
     session_end_time: "2026-07-09T10:05:00Z"
   }
   ```

2. **Update extension to persist UUID during session**
   - Store UUID in extension storage
   - Reuse UUID for retry attempts
   - Generate new UUID for new sessions

3. **Test offline-to-online sync**
   - Generate UUIDs while offline
   - Sync activities when online
   - Verify duplicate detection works

### Phase 3: Backend UUID Storage
**Timeline:** Week 5-6
**Impact:** Backend service layer

1. **Update `record_browser_activity()` service**
   ```python
   def record_browser_activity(db, activity_in, user):
       # Store UUID if provided
       db_activity = BrowserActivity(
           activity_uuid=activity_in.activity_uuid,
           # ... other fields
       )
   ```

2. **Update unique constraint strategy**
   ```python
   # Keep old constraint for backward compatibility
   # Add new constraint for UUID
   CREATE UNIQUE INDEX idx_activity_uuid 
   ON browser_activities (activity_uuid);
   ```

3. **Monitor UUID adoption rate**
   - Track percentage of requests with UUID
   - Monitor duplicate detection accuracy
   - Verify no data loss

### Phase 4: UUID Migration Completion
**Timeline:** Week 7-8
**Impact:** Database constraints

1. **Make `activity_uuid` non-nullable**
   ```sql
   -- First backfill existing records
   UPDATE browser_activities 
   SET activity_uuid = gen_random_uuid()
   WHERE activity_uuid IS NULL;
   
   -- Then make non-nullable
   ALTER TABLE browser_activities 
   ALTER COLUMN activity_uuid SET NOT NULL;
   ```

2. **Deprecate old duplicate detection strategy**
   ```python
   def check_duplicate(cls, db, activity_uuid, user_id=None, 
                      website_domain=None, session_start_time=None, 
                      session_end_time=None):
       # UUID only (old strategy deprecated)
       existing = db.query(BrowserActivity).filter(
           BrowserActivity.activity_uuid == activity_uuid
       ).first()
       return existing
   ```

3. **Remove old unique constraint**
   ```sql
   DROP INDEX idx_unique_session;
   ```

4. **Clean up code**
   - Remove fallback logic in `DuplicateDetectionService`
   - Update documentation
   - Remove old strategy comments

---

## Backward Compatibility Strategy

### During Migration (Phases 1-3)
- **UUID:** Optional field in API
- **Fallback:** Current strategy still works
- **Database:** Both constraints active
- **Extension:** Gradual rollout

### After Migration (Phase 4)
- **UUID:** Required field in API
- **Fallback:** Removed
- **Database:** UUID constraint only
- **Extension:** Full UUID adoption

---

## Rollback Plan

### If Issues Detected During Phase 2
1. Revert browser extension to previous version
2. Continue using current strategy
3. Investigate UUID generation issues

### If Issues Detected During Phase 3
1. Disable UUID storage in backend
2. Continue using current strategy
3. Investigate database constraint issues

### If Issues Detected During Phase 4
1. Make `activity_uuid` nullable again
2. Re-enable old unique constraint
3. Restore fallback logic

---

## Testing Strategy

### Phase 1 Testing
- [ ] Migration script runs successfully
- [ ] Model updates work correctly
- [ ] Schema validation passes
- [ ] Service layer accepts optional UUID

### Phase 2 Testing
- [ ] Extension generates valid UUIDs
- [ ] UUID persists during session
- [ ] Retry attempts reuse UUID
- [ ] Offline sync generates UUIDs

### Phase 3 Testing
- [ ] Backend stores UUID correctly
- [ ] Duplicate detection works with UUID
- [ ] Fallback to old strategy works
- [ ] No data loss during migration

### Phase 4 Testing
- [ ] Backfill completes successfully
- [ ] Non-nullable constraint works
- [ ] Old constraint removal works
- [ ] Cleanup doesn't break functionality

---

## Success Criteria

### Phase 1
- ✅ Database migration completes without errors
- ✅ Model and schema updates pass validation
- ✅ Service layer accepts optional UUID

### Phase 2
- ✅ Extension generates valid UUIDs
- ✅ 100% of extension requests include UUID
- ✅ Offline sync works correctly

### Phase 3
- ✅ Backend stores UUID for all new records
- ✅ Duplicate detection uses UUID primarily
- ✅ Fallback strategy works for edge cases

### Phase 4
- ✅ All existing records have UUID
- ✅ UUID is non-nullable
- ✅ Old strategy completely removed
- ✅ No data loss or corruption

---

## Timeline Summary

| Phase | Duration | Impact | Risk |
|-------|----------|--------|------|
| Phase 1 | 2 weeks | Backend only | Low |
| Phase 2 | 2 weeks | Extension | Medium |
| Phase 3 | 2 weeks | Backend + Extension | Medium |
| Phase 4 | 2 weeks | Database only | High |

**Total Migration Time:** 8 weeks

---

## Current Status

### Completed
- ✅ `DuplicateDetectionService` created with abstraction layer
- ✅ Service layer uses `DuplicateDetectionService`
- ✅ Documentation of migration path

### Pending
- ⏳ Phase 1: Database preparation
- ⏳ Phase 2: Browser extension update
- ⏳ Phase 3: Backend UUID storage
- ⏳ Phase 4: UUID migration completion

---

## Notes

- **No Breaking Changes:** Current API contract remains valid during migration
- **Gradual Rollout:** Extension can adopt UUID gradually
- **Backward Compatible:** Old strategy works until Phase 4
- **Rollback Ready:** Each phase can be rolled back independently
- **Production Safe:** Migration designed for zero downtime

---

## References

- **Service:** `app/services/duplicate_detection.py`
- **Model:** `app/models/analytics.py`
- **Schema:** `app/schemas/analytics_schemas.py`
- **Service Layer:** `app/services/analytics_service.py`
