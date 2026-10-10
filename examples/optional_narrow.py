"""Optional整数をNone分岐で絞り込む一般契約を示す。"""

from typing import Optional

from nagini_contracts.contracts import Ensures, Result


def increment_or_default(value: Optional[int]) -> int:
    """Noneなら0、整数なら1を加えた値を返す。

    Parameters
    ----------
    value : Optional[int]
        制限のない整数またはNone。

    Returns
    -------
    int
        Noneなら0、それ以外なら入力値に1を加えた値。
    """
    Ensures(value is not None or Result() == 0)
    Ensures(value is None or Result() == value + 1)
    return 0
