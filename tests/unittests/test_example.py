import pytest


# The simplest form of test
def test_add():
    assert 2 + 3 == 5


# Exercise 1. Write a test to test divide method od the StupidCalculatorClass
def test_divide_nonzero():
    # Arrange

    # Act

    # Assert
    assert 4 / 2 == 2


# In tests, we can assert if the function produces (expected) error
def test_divide_zero():
    # Arrange

    # Act
    with pytest.raises(ZeroDivisionError):
        # Assert
        result = 1 / 0


# This is parametrized test
# We parametrize input and output parameters - in this case a, b, and expected output
@pytest.mark.parametrize("a,b,expected", [(2, 3, 5), (-1, 1, 0), (0, 0, 0)])
def test_parametrized_add(a: float, b: float, expected: float):

    assert a + b == expected


# This is a decent way to write tests. However, sometimes to do proper tests, we need more global parameters - such as configurations of databases,
# connection to external data sources etc. Instead of repeating those codfigs, we can follow Don't Repeat Yourself rule (DRY) and use fixtures.
# We usually put those fixtures inside a single file - conftest.py
# # test_with_fixture.py
# import pytest


# @pytest.fixture
# def sample_data():
#     return {"username": "alice", "password": "secret"}


def test_sample_user(sample_data):
    assert sample_data["username"] == "alice"
