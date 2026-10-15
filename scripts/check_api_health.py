from __future__ import annotations

import json
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def request_json(url: str, payload: dict[str, object] | None = None) -> dict[str, object]:
    body = json.dumps(payload).encode() if payload is not None else None
    request = Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"} if body else {},
        method="POST" if body else "GET",
    )
    with urlopen(request, timeout=90) as response:
        if not 200 <= response.status < 300:
            raise RuntimeError(f"{url} returned HTTP {response.status}")
        return json.loads(response.read().decode())


def check_api(base_url: str) -> None:
    base_url = base_url.rstrip("/")
    health = request_json(f"{base_url}/health")
    if health.get("status") != "ok":
        raise RuntimeError(f"Unexpected health response: {health}")

    simulation = request_json(
        f"{base_url}/simulate",
        {
            "players": [
                {"id": "p1", "team_id": "team_a", "position": {"x": 10, "y": 34}},
                {"id": "p2", "team_id": "team_a", "position": {"x": 40, "y": 34}},
                {"id": "p3", "team_id": "team_b", "position": {"x": 25, "y": 34}},
            ],
            "ball_carrier_id": "p1",
            "pass_type": "ground",
            "target": {
                "type": "receiver",
                "receiver_id": "p2",
                "position": {"x": 40, "y": 34},
            },
            "parameters": {"ball_speed": 18},
        },
    )
    interceptors = simulation.get("interceptors")
    if (
        simulation.get("pass_type") != "ground"
        or simulation.get("risk") != "high"
        or not isinstance(simulation.get("risk_percent"), int)
        or simulation.get("interceptor_id") != "p3"
        or not isinstance(interceptors, list)
        or not interceptors
        or interceptors[0].get("player_id") != "p3"
    ):
        raise RuntimeError(f"Unexpected simulation response: {simulation}")


def main() -> int:
    if len(sys.argv) != 2 or not sys.argv[1].strip():
        print("Usage: python scripts/check_api_health.py https://api.example.com", file=sys.stderr)
        return 2

    last_error: Exception | None = None
    for attempt in range(1, 4):
        try:
            check_api(sys.argv[1])
            print("API health and simulation smoke test passed")
            return 0
        except (HTTPError, URLError, TimeoutError, RuntimeError, json.JSONDecodeError) as error:
            last_error = error
            print(f"Attempt {attempt}/3 failed: {error}", file=sys.stderr)
            if attempt < 3:
                time.sleep(20)

    print(f"API smoke test failed: {last_error}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
