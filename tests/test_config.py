import pytest

from app import config


def test_explicit_override_wins_regardless_of_dist(monkeypatch):
    monkeypatch.setattr(config, "_FRONTEND_URL_OVERRIDE", "https://example.com/")
    monkeypatch.setattr(config, "FRONTEND_DIST", config.FRONTEND_DIST.__class__("/does/not/matter"))
    assert config.resolve_frontend_base_url("http://127.0.0.1:8000/") == "https://example.com"


def test_explicit_override_wins_even_over_untrusted_host(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "_FRONTEND_URL_OVERRIDE", "https://example.com/")
    monkeypatch.setattr(config, "FRONTEND_DIST", tmp_path)  # exists
    assert config.resolve_frontend_base_url("http://attacker.tld/") == "https://example.com"


def test_dist_present_echoes_request_origin(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "_FRONTEND_URL_OVERRIDE", None)
    monkeypatch.setattr(config, "FRONTEND_DIST", tmp_path)  # exists
    assert config.resolve_frontend_base_url("http://127.0.0.1:8000/") == "http://127.0.0.1:8000"


def test_dist_present_allows_localhost(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "_FRONTEND_URL_OVERRIDE", None)
    monkeypatch.setattr(config, "FRONTEND_DIST", tmp_path)  # exists
    assert config.resolve_frontend_base_url("http://localhost:8000/") == "http://localhost:8000"


def test_dist_present_allows_private_lan_ip(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "_FRONTEND_URL_OVERRIDE", None)
    monkeypatch.setattr(config, "FRONTEND_DIST", tmp_path)  # exists
    assert config.resolve_frontend_base_url("http://192.168.1.42:8000/") == "http://192.168.1.42:8000"


def test_dist_present_allows_ipv6_loopback(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "_FRONTEND_URL_OVERRIDE", None)
    monkeypatch.setattr(config, "FRONTEND_DIST", tmp_path)  # exists
    assert config.resolve_frontend_base_url("http://[::1]:8000/") == "http://[::1]:8000"


def test_dist_present_rejects_public_host(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "_FRONTEND_URL_OVERRIDE", None)
    monkeypatch.setattr(config, "FRONTEND_DIST", tmp_path)  # exists
    with pytest.raises(config.UntrustedRequestOriginError):
        config.resolve_frontend_base_url("http://attacker.tld/")


def test_dist_present_rejects_unresolvable_lan_hostname(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "_FRONTEND_URL_OVERRIDE", None)
    monkeypatch.setattr(config, "FRONTEND_DIST", tmp_path)  # exists
    with pytest.raises(config.UntrustedRequestOriginError):
        config.resolve_frontend_base_url("http://mylaptop.local:8000/")


def test_dist_missing_falls_back_to_dev_port(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "_FRONTEND_URL_OVERRIDE", None)
    monkeypatch.setattr(config, "FRONTEND_DIST", tmp_path / "does-not-exist")
    assert config.resolve_frontend_base_url("http://127.0.0.1:8000/") == "http://localhost:5173"


def test_dist_missing_uses_trusted_origin_header(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "_FRONTEND_URL_OVERRIDE", None)
    monkeypatch.setattr(config, "FRONTEND_DIST", tmp_path / "does-not-exist")
    assert (
        config.resolve_frontend_base_url("http://127.0.0.1:8000/", "http://localhost:5174")
        == "http://localhost:5174"
    )


def test_dist_missing_ignores_untrusted_origin_header(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "_FRONTEND_URL_OVERRIDE", None)
    monkeypatch.setattr(config, "FRONTEND_DIST", tmp_path / "does-not-exist")
    assert (
        config.resolve_frontend_base_url("http://127.0.0.1:8000/", "http://attacker.tld")
        == "http://localhost:5173"
    )
