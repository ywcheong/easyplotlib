from typing import List
from pydantic import BaseModel, ValidationError, model_validator
from src.backend.request_format import CodeReject, ErrorModel, pretty_validation_error


class Point(BaseModel):
    x: float
    y: float


class Circle(BaseModel):
    name: str
    center: Point
    elses: List[Point]


my_circle = {
    "name": "MyName",
    "center": {"x": "what", "y": 12},
    "elses": [{"x": 2, "y": 3}, "bruh", {"p": 5, "q": "r"}],
}

expected_pretty = [
    ErrorModel(
        loc="request.center.x",
        msg="Input should be a valid number, unable to parse string as a number",
    ),
    ErrorModel(
        loc="request.elses[1]",
        msg="Input should be a valid dictionary or instance of Point",
    ),
    ErrorModel(loc="request.elses[2].x", msg="Field required"),
    ErrorModel(loc="request.elses[2].y", msg="Field required"),
]


def test_pretty():
    try:
        Circle.model_validate(my_circle)
    except ValidationError as e:
        assert pretty_validation_error(e) == expected_pretty
