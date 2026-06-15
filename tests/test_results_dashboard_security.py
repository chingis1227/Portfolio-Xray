from __future__ import annotations


def test_results_dashboard_rejects_output_dir_outside_project(monkeypatch, tmp_path) -> None:
    from results_dashboard import app as dashboard_app

    project_root = tmp_path / "project"
    project_root.mkdir()
    config_path = project_root / "config.yml"
    config_path.write_text("output_dir_final: ../outside\n", encoding="utf-8")
    monkeypatch.setattr(dashboard_app, "PROJECT_ROOT", project_root)
    monkeypatch.setattr(dashboard_app, "CONFIG_PATH", config_path)

    vm = dashboard_app.build_view_model()

    assert vm["has_data"] is False
    assert "inside the project root" in vm["error"]


def test_results_dashboard_report_route_rejects_output_dir_outside_project(monkeypatch, tmp_path) -> None:
    from results_dashboard import app as dashboard_app

    project_root = tmp_path / "project"
    project_root.mkdir()
    config_path = project_root / "config.yml"
    config_path.write_text("output_dir_final: ../outside\n", encoding="utf-8")
    monkeypatch.setattr(dashboard_app, "PROJECT_ROOT", project_root)
    monkeypatch.setattr(dashboard_app, "CONFIG_PATH", config_path)

    response = dashboard_app.app.test_client().get("/report")

    assert response.status_code == 400
    assert b"inside the project root" in response.data
