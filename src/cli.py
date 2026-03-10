from __future__ import annotations
from .api import HeadHunterAPI
from .models import Vacancy
from .storage import JSONSaver
from .utils import filter_vacancies, get_vacancies_by_salary, sort_vacancies, get_top_vacancies, print_vacancies


def user_interaction() -> None:
    print("=== Поиск вакансий на hh.ru ===")
    query = input("Введите поисковый запрос (например: Python): ").strip()
    if not query:
        print("Пустой запрос — завершение.")
        return

    top_n = int(input("Сколько показать в ТОП N по зарплате? ").strip() or "20")
    filter_words = input("Ключевые слова для фильтрации (через пробел, можно пусто): ").split()
    salary_range = input("Диапазон зарплат (напр. 120000-200000 или 150000): ").strip()

    print("\nЗагружаю вакансии с hh.ru...")
    with HeadHunterAPI() as hh:
        raw = hh.get_vacancies(query, per_page=100, max_pages=5)

    vacs = Vacancy.cast_to_object_list(raw)
    print(f"Получено: {len(vacs)} вакансий.")

    # Сохраним всё в файл (без дублей)
    saver = JSONSaver()
    saver.add(vacs)

    # Фильтры и сортировка
    filtered = filter_vacancies(vacs, filter_words)
    ranged = get_vacancies_by_salary(filtered, salary_range)
    best = get_top_vacancies(sort_vacancies(ranged), top_n)

    print("\n=== Результаты ===")
    print_vacancies(best)


if __name__ == "__main__":
    user_interaction()
