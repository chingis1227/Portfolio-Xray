from __future__ import annotations


def _csrf_headers(client) -> dict[str, str]:
    client.get("/")
    with client.session_transaction() as sess:
        return {"X-CSRF-Token": sess["csrf_token"]}


def test_config_ui_does_not_render_removed_rc_cap_field(monkeypatch, tmp_path) -> None:
    from config_ui import app as config_app

    config_path = tmp_path / "config.yml"
    config_path.write_text(
        "investor_currency: USD\n"
        "initial_investable_amount: 1000\n"
        "tickers:\n"
        "  - VOO\n"
        "weights: {}\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(config_app, "CONFIG_PATH", config_path)

    response = config_app.app.test_client().get("/")

    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert 'name="rc_asset_cap_pct"' not in html
    assert "Max RC per Asset" not in html


def test_config_ui_generate_does_not_write_removed_rc_cap_field(monkeypatch, tmp_path) -> None:
    from config_ui import app as config_app

    config_path = tmp_path / "config.yml"
    config_path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(config_app, "CONFIG_PATH", config_path)

    client = config_app.app.test_client()
    response = client.post(
        "/generate",
        headers=_csrf_headers(client),
        data={
            "investor_currency": "USD",
            "initial_investable_amount": "1000",
            "ticker[]": ["VOO"],
            "weight[]": ["100%"],
            "rc_asset_cap_pct": "25%",
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["success"] is True
    assert "rc_asset_cap_pct" not in payload["yaml"]
