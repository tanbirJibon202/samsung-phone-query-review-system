import pytest
from pydantic import ValidationError

from app.api.schemas import AskRequest, ReviewRequest


def test_inputs_are_trimmed() -> None:
    assert AskRequest(question="  Compare S23 and S22  ").question == "Compare S23 and S22"
    assert ReviewRequest(phone_name="  S23  ").phone_name == "S23"


@pytest.mark.parametrize("value", ["", " ", "x"])
def test_too_short_questions_are_rejected(value: str) -> None:
    with pytest.raises(ValidationError):
        AskRequest(question=value)
