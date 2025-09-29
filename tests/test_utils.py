from src.models import Vacancy
from src.utils import filter_vacancies, get_vacancies_by_salary, sort_vacancies, get_top_vacancies

def _v(eff: int, i: str) -> Vacancy:
    return Vacancy(id=i, title=f"t{i}", url=f"u{i}", description="py", salary_to=eff)

def test_filter_and_salary_and_sort_top():
    vacs = [_v(100, "1"), _v(200, "2"), _v(300, "3")]
    flt = filter_vacancies(vacs, ["py"])
    rng = get_vacancies_by_salary(flt, "150-250")
    assert [v.id for v in rng] == ["2"]

    assert [v.id for v in sort_vacancies(vacs)] == ["3", "2", "1"]
    assert [v.id for v in get_top_vacancies(vacs, 2)] == ["3", "2"]
