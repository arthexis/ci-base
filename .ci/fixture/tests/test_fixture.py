from ci_base_fixture import answer


def test_answer() -> None:
    assert answer() == 42
