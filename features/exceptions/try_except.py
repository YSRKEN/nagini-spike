"""try/except: 例外を捕まえて既定値を返す。"""

from nagini_contracts.contracts import Ensures, Exsures, Implies, Result


class InvalidAge(Exception):
    """年齢が負であることを表す例外。"""


def check_age(age: int) -> int:
    """負の年齢なら InvalidAge を投げ、それ以外はそのまま返す。"""
    Ensures(Result() == age and age >= 0)
    Exsures(InvalidAge, age < 0)
    if age < 0:
        raise InvalidAge()
    return age


def age_or_zero(age: int) -> int:
    """`InvalidAge` を捕まえ、負の年齢なら 0 を返す。"""
    Ensures(Implies(age < 0, Result() == 0))
    Ensures(Implies(age >= 0, Result() == age))
    try:
        return check_age(age)
    except InvalidAge:
        return 0


def wrong_age_or_zero(age: int) -> int:
    """捕まえたあとに、既定値ではなく入力をそのまま返してしまう。"""
    Ensures(Implies(age < 0, Result() == 0))
    Ensures(Implies(age >= 0, Result() == age))
    try:
        return check_age(age)
    except InvalidAge:
        return age
