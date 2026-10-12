"""Optional: 負なら None、非負ならその値を返し、呼び出し側は None で分けたあと安全に使える。"""

from typing import Optional

from nagini_contracts.contracts import Ensures, Result


def nonnegative_or_none(value: int) -> Optional[int]:
    """負なら None を、非負なら value を返す。"""
    Ensures((Result() is None) == (value < 0))
    Ensures(Result() is None or Result() == value)
    if value < 0:
        return None
    return value


def increment_nonnegative(value: int) -> int:
    """`None` で分けてから、値に1を足す。"""
    Ensures(value >= 0 or Result() == 0)
    Ensures(value < 0 or Result() == value + 1)
    selected = nonnegative_or_none(value)
    if selected is None:
        return 0
    return selected + 1


def wrong_increment_nonnegative(value: int) -> int:
    """`None` の場合を取り違え、負の入力で1を返してしまう。"""
    Ensures(value >= 0 or Result() == 0)
    Ensures(value < 0 or Result() == value + 1)
    selected = nonnegative_or_none(value)
    if selected is None:
        return 1
    return selected + 1
