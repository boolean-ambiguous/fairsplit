from app import config


def test_explicit_override_wins_regardless_of_dist(monkeypatch):
    monkeypatch.setattr(config, "_FRONTEND_URL_OVERRIDE", "https://example.com/")
    monkeypatch.setattr(config, "FRONTEND_DIST", config.FRONTEND_DIST.__class__("/does/not/matter"))
    assert config.resolve_frontend_base_url("http://127.0.0.1:8000/") == "https://example.com"


def test_dist_present_echoes_request_origin(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "_FRONTEND_URL_OVERRIDE", None)
    monkeypatch.setattr(config, "FRONTEND_DIST", tmp_path)  # exists
    assert config.resolve_frontend_base_url("http://127.0.0.1:8000/") == "http://127.0.0.1:8000"


def test_dist_missing_falls_back_to_dev_port(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "_FRONTEND_URL_OVERRIDE", None)
    monkeypatch.setattr(config, "FRONTEND_DIST", tmp_path / "does-not-exist")
    assert config.resolve_frontend_base_url("http://127.0.0.1:8000/") == "http://localhost:5173"
