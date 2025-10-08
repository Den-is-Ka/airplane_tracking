import os
import time
import requests
import pytest

from src.api import HeadHunterAPI


# ----------------------------- вспомогательные заглушки -----------------------------

class DummyResp:
    """Минимальный ответ requests, которого достаточно для нашего клиента."""
    def __init__(self, payload: dict, status_code: int = 200, url: str = "https://api.hh.ru/vacancies"):
        self._payload = payload
        self.status_code = status_code
        self.url = url
        self.reason = "OK" if status_code < 400 else "Bad Request"

    def json(self):
        return self._payload

    def raise_for_status(self):
        if 400 <= self.status_code < 600:
            raise requests.HTTPError(f"{self.status_code} error", response=self)


# --------------------------------------- тесты --------------------------------------

def test_init_sets_user_agent_and_pings(monkeypatch):
    """Проверяем, что заголовок User-Agent прописывается в Session и делается 'тихий' пинг."""
    ping_calls = {"n": 0}

    class DummySession:
        def __init__(self):
            self.headers = {}

        def get(self, url, **kwargs):
            # конструктор делает GET /dictionaries — вернём 200
            if url.endswith("/dictionaries"):
                ping_calls["n"] += 1
                return DummyResp({}, 200, url=url)
            # на всякий случай
            return DummyResp({}, 200, url=url)

    monkeypatch.setattr("requests.Session", DummySession)

    ua = "my-test-agent/0.1"
    api = HeadHunterAPI(user_agent=ua)
    assert api.session.headers.get("User-Agent") == ua
    assert ping_calls["n"] >= 1  # пинг был


def test_page_request_ok(monkeypatch):
    """Обычный успешный ответ: статус 200, есть items."""
    class DummySession:
        def __init__(self):
            self.headers = {}

        def get(self, url, **kwargs):
            if url.endswith("/dictionaries"):
                return DummyResp({}, 200, url=url)
            if url.endswith("/vacancies"):
                return DummyResp({"items": [{"id": "1"}]}, 200, url=url)
            return DummyResp({}, 200, url=url)

    monkeypatch.setattr("requests.Session", DummySession)

    api = HeadHunterAPI()
    items = api._page_request("python", page=0, per_page=1, prepost_sleep=0.0)
    assert items == [{"id": "1"}]


def test_page_request_403_raises_runtimeerror(monkeypatch):
    """403 должен приводить к понятной RuntimeError с советом про User-Agent/VPN."""
    class DummySession:
        def __init__(self):
            self.headers = {}

        def get(self, url, **kwargs):
            if url.endswith("/dictionaries"):
                return DummyResp({}, 200, url=url)
            if url.endswith("/vacancies"):
                return DummyResp({"items": []}, 403, url=url)
            return DummyResp({}, 200, url=url)

    monkeypatch.setattr("requests.Session", DummySession)

    api = HeadHunterAPI()
    with pytest.raises(RuntimeError) as ei:
        api._page_request("python", page=0, per_page=1, prepost_sleep=0.0)
    assert "403" in str(ei.value)


def test_page_request_429_retries_and_sleeps(monkeypatch):
    """Первый ответ 429 → клиент ждёт и повторяет; второй раз успех."""
    sleeps = {"args": []}

    def fake_sleep(x):
        sleeps["args"].append(x)

    class DummySession:
        def __init__(self):
            self.headers = {}
            self.count = 0

        def get(self, url, **kwargs):
            if url.endswith("/dictionaries"):
                return DummyResp({}, 200, url=url)
            if url.endswith("/vacancies"):
                self.count += 1
                if self.count == 1:
                    return DummyResp({}, 429, url=url)
                return DummyResp({"items": [{"id": "ok"}]}, 200, url=url)
            return DummyResp({}, 200, url=url)

    sess = DummySession()
    monkeypatch.setattr("requests.Session", lambda: sess)
    monkeypatch.setattr(time, "sleep", fake_sleep)

    api = HeadHunterAPI()
    items = api._page_request("python", page=0, per_page=1, prepost_sleep=0.2)
    assert items == [{"id": "ok"}]
    # Был хотя бы один sleep во время обработки 429
    assert any(v >= 1.5 for v in sleeps["args"])  # в коде min 1.5 секунды


def test_get_vacancies_pagination_and_stop_on_empty(monkeypatch):
    """Первая страница с данными, вторая пустая → сбор только первой страницы и останов."""
    class DummySession:
        def __init__(self):
            self.headers = {}
            self.calls = 0

        def get(self, url, **kwargs):
            if url.endswith("/dictionaries"):
                return DummyResp({}, 200, url=url)
            if url.endswith("/vacancies"):
                page = kwargs.get("params", {}).get("page", -1)
                if page == 0:
                    self.calls += 1
                    return DummyResp({"items": [{"id": "p0"}]}, 200, url=url)
                if page == 1:
                    self.calls += 1
                    return DummyResp({"items": []}, 200, url=url)
            return DummyResp({}, 200, url=url)

    sess = DummySession()
    monkeypatch.setattr("requests.Session", lambda: sess)
    monkeypatch.setattr(time, "sleep", lambda *_: None)  # ускоряем тест

    api = HeadHunterAPI()
    items = api.get_vacancies("python", per_page=1, max_pages=5)
    assert items == [{"id": "p0"}]
    assert sess.calls == 2  # p0 и p1


def test_area_param_present_or_absent(monkeypatch):
    """Проверяем, что area пробрасывается по умолчанию и убирается, если area=None."""
    captured_params_default = []
    captured_params_none = []

    class DummySessionDefault:
        def __init__(self):
            self.headers = {}

        def get(self, url, **kwargs):
            if url.endswith("/dictionaries"):
                return DummyResp({}, 200, url=url)
            if url.endswith("/vacancies"):
                captured_params_default.append(kwargs.get("params", {}))
                return DummyResp({"items": []}, 200, url=url)
            return DummyResp({}, 200, url=url)

    class DummySessionNone:
        def __init__(self):
            self.headers = {}

        def get(self, url, **kwargs):
            if url.endswith("/dictionaries"):
                return DummyResp({}, 200, url=url)
            if url.endswith("/vacancies"):
                captured_params_none.append(kwargs.get("params", {}))
                return DummyResp({"items": []}, 200, url=url)
            return DummyResp({}, 200, url=url)

    # по умолчанию area=113 должен быть в params
    monkeypatch.setattr("requests.Session", DummySessionDefault)
    api_def = HeadHunterAPI()
    api_def.get_vacancies("python", per_page=1, max_pages=1)
    assert captured_params_default and captured_params_default[0].get("area") == 113

    # если area=None — параметр не должен отправляться
    monkeypatch.setattr("requests.Session", DummySessionNone)
    api_none = HeadHunterAPI(area=None)
    api_none.get_vacancies("python", per_page=1, max_pages=1)
    assert captured_params_none and "area" not in captured_params_none[0]
