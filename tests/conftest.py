import os
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure a test database URL is set before importing the app
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from protonmailer import database, main, scheduler  # noqa: E402
from protonmailer.database import Base
from protonmailer.dependencies import get_db


test_engine = create_engine(
    "sqlite:///:memory:", connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db() -> Generator:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Re-wire database/session for testing
database.engine = test_engine
database.SessionLocal = TestingSessionLocal
scheduler.SessionLocal = TestingSessionLocal
main.init_db = lambda: Base.metadata.create_all(bind=test_engine)
main.start_scheduler = lambda app: None
main.app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def clean_db() -> Generator:
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield


@pytest.fixture
def session() -> Generator:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client() -> TestClient:
    return TestClient(main.app)
