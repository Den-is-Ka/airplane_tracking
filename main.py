from __future__ import annotations
from dotenv import load_dotenv
load_dotenv()

from src.api import HeadHunterAPI
from src.models import Vacancy
from src.storage import JSONSaver
from src.utils import filter_vacancies, get_vacancies_by_salary, sort_vacancies, get_top_vacancies, print_vacancies


def user_interaction():
    api = HeadHunterAPI()  # UA берётся из HH_USER_AGENT, иначе дефолт
    query = input("Введите поисковый запрос: ").strip()
    top_n = int(input("Введите количество вакансий для вывода в топ N: ").strip() or "10")
    filter_words = input("Ключевые слова для фильтрации (через пробел): ").split()
    salary_range = input("Введите диапазон зарплат (например, 100000-200000): ").strip()

    raw = api.get_vacancies(query, per_page=100, max_pages=20)
    vacancies = Vacancy.cast_to_object_list(raw)

    filtered = filter_vacancies(vacancies, filter_words) if filter_words else vacancies
    ranged = get_vacancies_by_salary(filtered, salary_range) if salary_range else filtered
    sorted_vacancies = sort_vacancies(ranged)

    top_list = get_top_vacancies(sorted_vacancies, top_n)
    print_vacancies(top_list)

    saver = JSONSaver()  # имя файла по умолчанию внутри класса
    for v in top_list:
        saver.add_vacancy(v)


if __name__ == "__main__":
    user_interaction()
