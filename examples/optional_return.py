"""任意整数からOptional整数を返す一般契約を示す。"""

from typing import Optional

from nagini_contracts.contracts import Ensures, Result


def nonnegative_or_none(value: int) -> Optional[int]:
    """負整数ならNone、非負整数なら入力を返す。

    Parameters
    ----------
    value : int
        制限のない整数。

    Returns
    -------
    Optional[int]
        負整数ならNone、それ以外なら入力。
    """
    Ensures((Result() is None) == (value < 0))
    Ensures(Result() is None or Result() == value)
    if value < 0:
        return None
    return value


def increment_nonnegative(value: int) -> int:
    """戻り契約を利用して欠損なら0、非負なら入力に1を加える。

    Parameters
    ----------
    value : int
        制限のない整数。

    Returns
    -------
    int
        負整数なら0、それ以外なら入力に1を加えた値。
    """
    Ensures(value >= 0 or Result() == 0)
    Ensures(value < 0 or Result() == value + 1)
    selected = nonnegative_or_none(value)
    if selected is None:
        return 0
    return selected + 1
