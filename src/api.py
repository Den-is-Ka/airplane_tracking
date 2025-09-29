from __future__ import annotations
from abc import ABC, abstractmethod
import os
import time
import requests


class BaseVacanciesAPI(ABC):
    """Абстрактный API-клиент для платформ с вакансиями."""

    @abstractmethod
    def get_vacancies(self, query: str, *, per_page: int = 100, max_pages: int = 20) -> list[dict]:
        """Вернуть список вакансий (как словари)."""
        raise NotImplementedError


class HeadHunterAPI(BaseVacanciesAPI):
    """
    Клиент для HH API:
      - корректный User-Agent (из HH_USER_AGENT или дефолт)
      - requests.Session() для эффективности
      - обработка 403/429
      - мягкая пагинация с выходом по пустой странице
    """

    BASE = "https://api.hh.ru"
    VAC_URL = BASE + "/vacancies"

    def __init__(self, *, user_agent: str | None = None, area: int | None = 113):
        # корректный UA обязателен для hh.ru
        self.user_agent = user_agent or os.getenv(
            "HH_USER_AGENT",
            "coursework-app/1.0 (+you@example.com)"
        )
        self.area = area

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": self.user_agent,
            "Accept": "application/json",
        })

        # Лёгкий ping (не валим конструктор, если сеть закрыта)
        try:
            self.session.get(f"{self.BASE}/dictionaries", timeout=10)
        except Exception:
            pass

    def _page_request(self, query: str, page: int, per_page: int, prepost_sleep: float) -> list[dict]:
        params = {
            "text": query,
            "per_page": per_page,
            "page": page,
        }
        if self.area is not None:
            params["area"] = self.area  # 113 = Россия

        resp = self.session.get(self.VAC_URL, params=params, timeout=30)

        # 403 — чаще всего из-за отсутствия нормального User-Agent или блокировки сети
        if resp.status_code == 403:
            raise RuntimeError(
                "HH API вернул 403 Forbidden. "
                "Задайте корректный User-Agent (переменная окружения HH_USER_AGENT) "
                "или попробуйте другую сеть/VPN."
            )

        # 429 — много запросов; подождём и попробуем повторить
        if resp.status_code == 429:
            time.sleep(max(prepost_sleep, 1.5))
            resp = self.session.get(self.VAC_URL, params=params, timeout=30)

        resp.raise_for_status()
        data = resp.json()
        items = data.get("items", [])
        return items

    def get_vacancies(self, query: str, *, per_page: int = 100, max_pages: int = 20) -> list[dict]:
        results: list[dict] = []
        page = 0
        # небольшая пауза между запросами, чтобы не ловить 429
        prepost_sleep = 0.35

        while page < max_pages:
            items = self._page_request(query, page, per_page, prepost_sleep)
            if not items:
                break
            results.extend(items)
            page += 1
            time.sleep(prepost_sleep)

        return results
