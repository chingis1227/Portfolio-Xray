from __future__ import annotations


def _csrf_headers(client) -> dict[str, str]:
    client.get("/")
    with client.session_transaction() as sess:
        return {"X-CSRF-Token": sess["csrf_token"]}


def test_config_ui_mutating_routes_require_csrf_token(monkeypatch, tmp_path) -> None:
    from config_ui import app as config_app

    config_path = tmp_path / "config.yml"
    config_path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(config_app, "CONFIG_PATH", config_path)

    response = config_app.app.test_client().post(
        "/generate",
        data={"investor_currency": "USD", "ticker[]": ["VOO"], "current_weight[]": ["100%"]},
    )

    assert response.status_code == 403


def test_config_ui_accepts_mutating_route_with_csrf_token(monkeypatch, tmp_path) -> None:
    from config_ui import app as config_app

    config_path = tmp_path / "config.yml"
    config_path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(config_app, "CONFIG_PATH", config_path)

    client = config_app.app.test_client()
    response = client.post(
        "/generate",
        headers=_csrf_headers(client),
        data={"investor_currency": "USD", "ticker[]": ["VOO"], "current_weight[]": ["100%"]},
    )

    assert response.status_code == 200
    assert response.get_json()["success"] is True


def test_config_ui_rejects_non_local_requests(monkeypatch) -> None:
    from config_ui import app as config_app

    monkeypatch.delenv("PMRI_CONFIG_UI_ALLOW_REMOTE", raising=False)

    response = config_app.app.test_client().get("/", environ_base={"REMOTE_ADDR": "203.0.113.10"})

    assert response.status_code == 403
