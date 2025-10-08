from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, List, Optional


@dataclass(slots=True, order=True)
class Vacancy:
    """Модель вакансии с поддержкой сравнения по зарплате (средней)."""

    sort_index: int = field(init=False, repr=False)  # для order=True
    id: str
    title: str
    url: str
    description: str
    salary_from: int = 0
    salary_to: int = 0
    currency: str = "RUR"

    def __post_init__(self) -> None:
        self.salary_from = int(self.salary_from or 0)
        self.salary_to = int(self.salary_to or 0)
        self.currency = (self.currency or "RUR").upper()
        # средняя зарплата для сортировки
        effective = self.salary_to or self.salary_from
        if self.salary_from and self.salary_to:
            effective = (self.salary_from + self.salary_to) // 2
        self.sort_index = effective

    # ---------- фабрики ----------
    @classmethod
    def from_hh(cls, item: dict[str, Any]) -> "Vacancy":
        """Создаёт Vacancy из элемента ответа hh.ru."""
        vid = str(item.get("id", ""))
        name = str(item.get("name", "") or "")
        url = str(item.get("alternate_url") or item.get("url") or "")
        desc = str(item.get("snippet", {}).get("requirement") or "") + " " + str(
            item.get("snippet", {}).get("responsibility") or ""
        )

        sal = item.get("salary") or {}
        s_from = sal.get("from") or 0
        s_to = sal.get("to") or 0
        cur = sal.get("currency") or "RUR"
        return cls(id=vid, title=name, url=url, description=desc.strip(), salary_from=s_from, salary_to=s_to, currency=cur)

    @classmethod
    def cast_to_object_list(cls, raw_items: Iterable[dict[str, Any]]) -> List["Vacancy"]:
        return [cls.from_hh(x) for x in raw_items or []]
