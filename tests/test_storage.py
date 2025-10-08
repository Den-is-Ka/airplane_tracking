from pathlib import Path
from src.models import Vacancy
from src.storage import JSONSaver


def test_jsonsaver_add_read_delete(tmp_path: Path):
    f = tmp_path / "vac.json"
    s = JSONSaver(f)

    v1 = Vacancy(id="1", title="Dev", url="u1", description="Python", salary_from=100)
    v2 = Vacancy(id="2", title="Analyst", url="u2", description="SQL", salary_to=200)

    s.add([v1, v2, v1])  # дубликат не должен добавиться второй раз
    got = s.read(text="python")
    assert len(got) == 1 and got[0]["id"] == "1"

    assert s.delete("u1") == 1
    assert s.delete(v2) == 1
    assert s.read() == []
