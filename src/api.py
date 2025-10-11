from __future__ import annotations
from abc import ABC, abstractmethod
import os
import time
import requests


class BaseVacanciesAPI(ABC):
    """Абстрактный API-клиент для платформ с вакансиями."""

    @abstractmethod
    def get_vacancies(self, query: str, *, per_page: int = 100, max_pages: int = 20) -> list[dict]:
        """Вернуть список вакансий (как словари из внешнего API)."""
        raise NotImplementedError


class HeadHunterAPI(BaseVacanciesAPI):
    """
    Клиент к HH API:
      • корректный User-Agent (из HH_USER_AGENT или дефолт)
      • requests.Session() для эффективности
      • обработка 403 (UA/сетевые ограничения) и 429 (rate limit)
      • аккуратная пагинация с выходом по пустой странице
    """

    BASE = "https://api.hh.ru"
    VAC_URL = BASE + "/vacancies"


    def __init__(self, *, user_agent: str | None = None, area: int | None = 113):
        self.user_agent = user_agent or os.getenv(
            "HH_USER_AGENT",
            "coursework-app/1.0 (+your-email@example.com)"
        )
        self.area = area

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": self.user_agent,
            "Accept": "application/json",
        })

        # Лёгкий ping (не падаем, если сети нет)
        try:
            self.session.get(f"{self.BASE}/dictionaries", timeout=10)
        except Exception:
            pass

    def _page_request(self, query: str, page: int, per_page: int, prepost_sleep: float) -> list[dict]:
        # HH допускает per_page до 100
        per_page = max(1, min(int(per_page), 100))
        params = {
            "text": query,
            "per_page": per_page,
            "page": page,
        }
        if self.area is not None:
            params["area"] = self.area  # 113 — Россия

        resp = self.session.get(self.VAC_URL, params=params, timeout=30)

        if resp.status_code == 403:
            raise RuntimeError(
                "HH API вернул 403 Forbidden. Задайте валидный User-Agent "
                "(переменная окружения HH_USER_AGENT) или попробуйте другую сеть/VPN."
            )

        if resp.status_code == 429:  # Too Many Requests
            import time
            time.sleep(max(prepost_sleep, 1.5))
            resp = self.session.get(self.VAC_URL, params=params, timeout=30)

        resp.raise_for_status()
        data = resp.json()
        return data.get("items", []) or []

    def get_vacancies(self, query: str, *, per_page: int = 100, max_pages: int = 20) -> list[dict]:
        results: list[dict] = []
        page = 0
        prepost_sleep = 0.35  # пауза между запросами (тесты могут её замокать)

        import time
        while page < max_pages:
            items = self._page_request(query, page, per_page, prepost_sleep)
            if not items:
                break
            results.extend(items)
            page += 1
            time.sleep(prepost_sleep)

        return results

    def close(self) -> None:
        """Закрыть HTTP-сессию."""
        try:
            self.session.close()
        except Exception:
            pass

    def __enter__(self) -> "HeadHunterAPI":
        """Поддержка with HeadHunterAPI() as hh:"""
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
