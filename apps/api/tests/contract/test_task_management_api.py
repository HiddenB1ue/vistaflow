from __future__ import annotations

from app.main import app
from app.tasks.constants import TASK_TYPES


def test_task_management_routes_exist() -> None:
    route_map: dict[str, set[str]] = {}
    for route in app.routes:
        path = getattr(route, "path", None)
        methods = getattr(route, "methods", None)
        if path is None or methods is None:
            continue
        route_map.setdefault(path, set()).update(methods)

    assert "GET" in route_map["/task-types"]
    assert {"GET", "POST"}.issubset(route_map["/tasks"])
    assert {"GET", "PATCH", "DELETE"}.issubset(route_map["/tasks/{task_id}"])
    assert "POST" in route_map["/tasks/{task_id}/run"]
    assert "GET" in route_map["/tasks/{task_id}/runs"]
    assert "GET" in route_map["/task-runs/{run_id}"]
    assert "GET" in route_map["/task-runs/{run_id}/logs"]
    assert "POST" in route_map["/task-runs/{run_id}/terminate"]


def test_openapi_exposes_railway_task_contracts() -> None:
    schema = app.openapi()
    task_type_props = schema["components"]["schemas"]["TaskTypeResponse"]["properties"]
    assert "paramSchema" in task_type_props
    assert "payload" in schema["components"]["schemas"]["TaskCreateRequest"]["properties"]
    assert "progressSnapshot" in schema["components"]["schemas"]["TaskRunResponse"]["properties"]
    assert {"fetch-trains", "fetch-train-stops", "fetch-train-runs"}.issubset(TASK_TYPES.keys())
