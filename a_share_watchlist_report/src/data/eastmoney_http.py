import random
import time
from typing import Any, Callable

try:
    from curl_cffi import requests as curl_requests
except ImportError:  # pragma: no cover - covered by dependency smoke checks
    curl_requests = None


UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
RETRY_STATUS_CODES = {429, 500, 502, 503, 504}


class EastMoneyHTTPError(RuntimeError):
    """Raised when an EastMoney HTTP endpoint cannot return usable JSON."""


class EastMoneyHTTPClient:
    """EastMoney HTTP client adapted from a-stock-data's em_get pattern.

    The original project uses Apache-2.0 licensed ideas: shared session,
    serial throttling, jitter, and bounded retries for EastMoney endpoints.
    This implementation keeps our project-specific error and test contracts.
    """

    def __init__(
        self,
        session: Any | None = None,
        min_interval: float = 1.0,
        retries: int = 2,
        timeout: int = 15,
        sleep_fn: Callable[[float], None] = time.sleep,
        jitter_fn: Callable[[], float] | None = None,
        now_fn: Callable[[], float] = time.time,
    ) -> None:
        if session is None:
            if curl_requests is None:
                raise EastMoneyHTTPError("curl_cffi is not installed; install requirements.txt before running the report")
            session = curl_requests.Session()
        self.session = session
        self.min_interval = min_interval
        self.retries = retries
        self.timeout = timeout
        self.sleep_fn = sleep_fn
        self.jitter_fn = jitter_fn or (lambda: random.uniform(0.1, 0.5))
        self.now_fn = now_fn
        self._last_call: float | None = None
        self.session.headers.update({"User-Agent": UA})

    def get_json(
        self,
        url: str,
        params: dict | None = None,
        headers: dict | None = None,
        timeout: int | None = None,
        **kwargs: Any,
    ) -> dict:
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            self._throttle()
            response = None
            try:
                response = self.session.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=timeout or self.timeout,
                    **kwargs,
                )
                response.raise_for_status()
                return response.json()
            except Exception as exc:  # noqa: BLE001 - normalize transport/status/json errors
                last_error = exc
                status_code = getattr(response, "status_code", None)
                should_retry = status_code in RETRY_STATUS_CODES or status_code is None
                if status_code == 403 or attempt >= self.retries or not should_retry:
                    detail = f"status {status_code}: {exc}" if status_code else str(exc)
                    raise EastMoneyHTTPError(f"EastMoney request failed for {url}: {detail}") from exc
            finally:
                self._last_call = self.now_fn()

        raise EastMoneyHTTPError(f"EastMoney request failed for {url}: {last_error}")

    def _throttle(self) -> None:
        if self._last_call is None:
            return
        wait = self.min_interval - (self.now_fn() - self._last_call)
        if wait > 0:
            self.sleep_fn(wait + self.jitter_fn())


DEFAULT_EASTMONEY_CLIENT = EastMoneyHTTPClient()


def em_get_json(url: str, params: dict | None = None, headers: dict | None = None, timeout: int = 15, **kwargs: Any) -> dict:
    return DEFAULT_EASTMONEY_CLIENT.get_json(url, params=params, headers=headers, timeout=timeout, **kwargs)
