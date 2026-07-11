import os
import tempfile
from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database.session import Base

# Import all models so their tables are registered with Base.metadata
# before create_all() is called. SQLAlchemy only knows about tables
# whose model classes have been imported at least once.
import app.models.models  # noqa: F401 — registers User, Organization, Invitation, AuditLog
import app.models.analytics  # noqa: F401 — registers BrowserActivity

from app.main import app
from app.middleware.rate_limit import limiter

# Disable rate limiting for all tests to prevent flaky 429 errors from slowapi
limiter.enabled = False


# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def db_engine():
    """Create a fresh database engine for each test."""
    from sqlalchemy.pool import StaticPool
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(db_engine) -> Generator[Session, None, None]:
    """Create a fresh database session for each test."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database session override."""
    from fastapi.testclient import TestClient
    
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    from app.dependencies.deps import get_db
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
    """Provide test user data."""
    return {
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "SecurePassword123!",
    }


@pytest.fixture
def test_organization_data():
    """Provide test organization data."""
    return {
        "organization_name": "Test Organization",
    }
