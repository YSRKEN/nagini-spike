"""raise: 不正な入力では InvalidAge を投げ、正常なら事後条件を満たす。"""

from nagini_contracts.contracts import Ensures, Exsures, Result


class InvalidAge(Exception):
    """年齢が負であることを表す例外。"""


def check_age(age: int) -> int:
    """負の年齢なら InvalidAge を投げ、それ以外はそのまま返す。"""
    Ensures(Result() == age and age >= 0)
    Exsures(InvalidAge, age < 0)
    if age < 0:
        raise InvalidAge()
    return age


def wrong_check_age(age: int) -> int:
    """境界を1つずらし、0 歳でも InvalidAge を投げてしまう。"""
    Ensures(Result() == age and age >= 0)
    Exsures(InvalidAge, age < 0)
    if age <= 0:
        raise InvalidAge()
    return age
