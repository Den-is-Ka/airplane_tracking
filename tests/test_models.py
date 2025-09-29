from src.models import Vacancy


def test_from_hh_and_ordering():
    raw = {
        "id": "42",
        "name": "Engineer",
        "alternate_url": "https://hh.ru/vacancy/42",
        "salary": {"from": 100000, "to": 200000, "currency": "RUR"},
        "snippet": {"requirement": "req", "responsibility": "resp"},
    }
    v = Vacancy.from_hh(raw)
    assert v.id == "42" and v.sort_index == 150000

    a = Vacancy(id="1", title="A", url="u1", description="", salary_from=10)
    b = Vacancy(id="2", title="B", url="u2", description="", salary_to=20)
    assert b > a  # сравнение по зарплате
