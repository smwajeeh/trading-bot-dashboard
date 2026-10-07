import pytest

from assistant import create_app


@pytest.fixture
def app(tmp_path):
    return create_app({"TESTING": True, "DATA_DIR": str(tmp_path), "WEBHOOK_SECRET": "s3cret"})


@pytest.fixture
def client(app):
    return app.test_client()
