import os
import threading
from http.server import ThreadingHTTPServer

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import database
import app.models  # noqa: F401  (register User on Base.metadata)
from app.server import Handler


@pytest.fixture
def base_url():
    engine = create_engine(os.environ["DATABASE_URL"])
    database.SessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=engine
    )
    database.Base.metadata.drop_all(engine)
    database.Base.metadata.create_all(engine)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.shutdown()
        engine.dispose()
