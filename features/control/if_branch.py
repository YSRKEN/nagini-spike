"""if: 絶対値が非負で、入力と等しいか符号を反転した値になる。"""

from nagini_contracts.contracts import Ensures, Result


def absolute(x: int) -> int:
    """負なら符号を反転して返す。"""
    Ensures(Result() >= 0)
    Ensures(Result() == x or Result() == -x)
    if x < 0:
        return -x
    return x


def wrong_absolute(x: int) -> int:
    """分岐を書き忘れ、負の入力をそのまま返す。"""
    Ensures(Result() >= 0)
    Ensures(Result() == x or Result() == -x)
    return x
