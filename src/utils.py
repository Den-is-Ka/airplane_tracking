from __future__ import annotations

from typing import Iterable, List
from .models import Vacancy


def filter_vacancies(vacancies: Iterable[Vacancy], keywords: Iterable[str]) -> list[Vacancy]:
    words = [w.lower() for w in (keywords or [])]
    if not words:
        return list(vacancies)
    def ok(v: Vacancy) -> bool:
        blob = (v.title + " " + v.description).lower()
        return all(w in blob for w in words)
    return [v for v in vacancies if ok(v)]


def get_vacancies_by_salary(vacancies: Iterable[Vacancy], salary_range: str | None) -> list[Vacancy]:
    """salary_range: строка вида '100000-150000' или '120000' (минимум)."""
    if not salary_range:
        return list(vacancies)
    s = salary_range.replace(" ", "")
    if "-" in s:
        lo_s, hi_s = s.split("-", 1)
        lo, hi = int(lo_s or 0), int(hi_s or 10**12)
        def in_range(v: Vacancy) -> bool:
            eff = v.salary_to or v.salary_from
            return lo <= eff <= hi
        return [v for v in vacancies if in_range(v)]
    else:
        lo = int(s or 0)
        return [v for v in vacancies if (v.salary_to or v.salary_from) >= lo]


def sort_vacancies(vacancies: Iterable[Vacancy], *, reverse: bool = True) -> list[Vacancy]:
    return sorted(vacancies, reverse=reverse)


def get_top_vacancies(vacancies: Iterable[Vacancy], n: int) -> list[Vacancy]:
    return list(sort_vacancies(vacancies)[: max(0, int(n))])


def print_vacancies(vacancies: Iterable[Vacancy]) -> str:
    """Возвращает человекочитаемую строку (и заодно её можно print)."""
    lines: list[str] = []
    for v in vacancies:
        money = f"{v.salary_from}-{v.salary_to} {v.currency}" if (v.salary_from or v.salary_to) else "Зарплата не указана"
        lines.append(f"{v.title} | {money}\n{v.url}")
    out = "\n\n".join(lines)
    print(out)  # можно убрать, если не хочется печатать автоматически
    return out
