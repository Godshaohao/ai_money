import pytest

from src.data.eastmoney_http import EastMoneyHTTPClient, EastMoneyHTTPError


class FakeResponse:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload

    def json(self) -> dict:
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeSession:
    def __init__(self, responses: list[FakeResponse]):
        self.headers: dict[str, str] = {}
        self.responses = responses
        self.calls: list[dict] = []

    def get(self, url: str, **kwargs):
        self.calls.append({"url": url, **kwargs})
        return self.responses.pop(0)


def test_eastmoney_http_client_retries_5xx_and_returns_json() -> None:
    session = FakeSession([FakeResponse(500, {"error": "busy"}), FakeResponse(200, {"data": {"ok": True}})])
    sleeps: list[float] = []
    client = EastMoneyHTTPClient(session=session, min_interval=0, sleep_fn=sleeps.append, jitter_fn=lambda: 0)

    payload = client.get_json("https://push2ex.eastmoney.com/getTopicZTPool", params={"date": "20260710"})

    assert payload == {"data": {"ok": True}}
    assert len(session.calls) == 2
    assert session.calls[0]["params"] == {"date": "20260710"}
    assert "User-Agent" in session.headers


def test_eastmoney_http_client_does_not_retry_403() -> None:
    session = FakeSession([FakeResponse(403, {"message": "blocked"})])
    client = EastMoneyHTTPClient(session=session, min_interval=0, sleep_fn=lambda _: None, jitter_fn=lambda: 0)

    with pytest.raises(EastMoneyHTTPError, match="403"):
        client.get_json("https://push2.eastmoney.com/api")

    assert len(session.calls) == 1


def test_eastmoney_http_client_serial_throttles_requests() -> None:
    session = FakeSession([FakeResponse(200, {"ok": 1}), FakeResponse(200, {"ok": 2})])
    sleeps: list[float] = []
    times = iter([10.0, 10.2, 10.2])
    client = EastMoneyHTTPClient(
        session=session,
        min_interval=1.0,
        sleep_fn=sleeps.append,
        jitter_fn=lambda: 0.25,
        now_fn=lambda: next(times),
    )

    client.get_json("https://push2.eastmoney.com/first")
    client.get_json("https://push2.eastmoney.com/second")

    assert sleeps == [pytest.approx(1.05)]
