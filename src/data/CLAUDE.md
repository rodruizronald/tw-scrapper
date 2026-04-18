# Data Layer

## Two Storage Backends

### MongoDB (`mongo/`)
- Primary storage for pipeline data (job listings, metrics)
- Dataclass-based models with `to_dict()` / `from_dict()` serialization
- Generic base repository (`base_repo.py`) with TypeVar `T`, abstract methods: `_to_dict()`, `_from_dict()`, `_get_unique_key()`, `_get_id()`, `_set_id()`
- Connection managed by singleton `DatabaseController` in `controller.py`
- Repositories use global singletons (e.g., `job_listing_repository`)
- Error handling: catches `PyMongoError`, logs, returns None/empty (does not raise)

### Supabase (`supebase/`)

Note: the directory is named `supebase` (typo preserved for consistency).

- Backend sync target for processed job data
- Pydantic `BaseModel` models with `StrEnum` fields and validation
- Base repository with comprehensive HTTP/PostgREST error mapping to domain exceptions
- Resilience via `@with_resilience` decorator on all CRUD methods

**Exception hierarchy** (`exceptions.py`):
```
SupabaseBaseException
├── SupabaseConfigError          (non-retryable)
├── SupabaseConnectionError      (retryable)
│   ├── SupabaseTimeoutError
│   └── SupabaseNetworkError
├── SupabaseAuthError            (non-retryable, 401/403)
├── SupabaseNotFoundError        (non-retryable, 404)
├── SupabaseConflictError        (context-dependent, 409)
├── SupabaseValidationError      (non-retryable, 400)
├── SupabaseRateLimitError       (retryable, 429)
├── SupabaseServerError          (retryable, 500+)
├── SupabaseCircuitBreakerError
└── SupabaseRetryExhaustedError
```

**Circuit breaker** (`decorators.py`): pybreaker-based, configured via `SupabaseConfig` (failure threshold, recovery timeout). Combined with tenacity retry as `@with_resilience` = retry (inner) -> circuit breaker (outer). Circuit breaker fails fast when open.

**Conflict handling**: 409 errors for duplicate jobs/technologies are expected and should be skipped silently, not treated as failures.

## Key Differences

| Aspect | MongoDB | Supabase |
|--------|---------|----------|
| Models | Dataclasses | Pydantic BaseModel |
| IDs | BSON ObjectId | Auto-increment integers |
| Errors | Logs and returns None | Raises typed exceptions |
| Resilience | None | Retry + circuit breaker |
| Soft delete | `active` field | `is_active` field |
