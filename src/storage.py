from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterable, List, Any
import json

from .models import Vacancy


class VacancyStorage(ABC):
    """Абстракция над хранилищем вакансий."""

    @abstractmethod
    def read(self, **criteria) -> list[dict[str, Any]]:
        """Возвращает список словарей (как в файле) с фильтрацией по критериям."""
        raise NotImplementedError

    @abstractmethod
    def add(self, vacancies: Vacancy | Iterable[Vacancy]) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete(self, vacancy: Vacancy | str) -> int:
        """Удаляет по объекту/ID/URL. Возвращает, сколько записей удалено."""
        raise NotImplementedError


class JSONSaver(VacancyStorage):
    """Хранение вакансий в JSON-файле (без дублей по id/url)."""

    def __init__(self, filename: str | Path = "data/vacancies.json") -> None:
        self.__filename = Path(filename)

    # ---------- внутреннее ----------
    def _load(self) -> list[dict]:
        if not self.__filename.exists():
            return []
        with open(self.__filename, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                return []
        return data if isinstance(data, list) else []

    def _dump(self, rows: list[dict]) -> None:
        self.__filename.parent.mkdir(parents=True, exist_ok=True)
        with open(self.__filename, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)

    # ---------- API ----------
    def read(self, **criteria) -> list[dict]:
        items = self._load()
        text = (criteria.get("text") or "").lower()
        min_salary = int(criteria.get("min_salary") or 0)
        if text:
            items = [r for r in items if text in (r.get("title", "") + " " + r.get("description", "")).lower()]
        if min_salary:
            def eff(r: dict) -> int:
                s_from, s_to = int(r.get("salary_from") or 0), int(r.get("salary_to") or 0)
                return s_to or s_from
            items = [r for r in items if eff(r) >= min_salary]
        return items

    def add(self, vacancies: Vacancy | Iterable[Vacancy]) -> None:
        items = self._load()
        seen = {(r.get("id") or "", r.get("url") or "") for r in items}
        to_add = vacancies if isinstance(vacancies, Iterable) and not isinstance(vacancies, Vacancy) else [vacancies]  # type: ignore

        for v in to_add:  # type: ignore[assignment]
            key = (v.id, v.url)
            if key in seen:
                continue
            items.append({
                "id": v.id,
                "title": v.title,
                "url": v.url,
                "description": v.description,
                "salary_from": v.salary_from,
                "salary_to": v.salary_to,
                "currency": v.currency,
            })
            seen.add(key)
        self._dump(items)

    def delete(self, vacancy: Vacancy | str) -> int:
        items = self._load()
        before = len(items)
        if isinstance(vacancy, Vacancy):
            items = [r for r in items if r.get("id") != vacancy.id and r.get("url") != vacancy.url]
        else:
            key = str(vacancy)
            items = [r for r in items if r.get("id") != key and r.get("url") != key]
        self._dump(items)
        return before - len(items)
