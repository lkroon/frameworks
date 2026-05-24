import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from webtest import TestApp

import app.database as database
import app.models  # noqa: F401  (register User on Base.metadata)
from app.database import Base


@pytest.fixture
def testapp():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    database.SessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=engine
    )
    Base.metadata.create_all(bind=engine)

    from app import main

    return TestApp(main())
