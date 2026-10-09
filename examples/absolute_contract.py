"""返り値の契約と、呼び出し側での利用を検証する。"""

from nagini_contracts.contracts import Ensures, ResultT


def absolute(x: int) -> int:
    """整数の絶対値を返す。

    Parameters
    ----------
    x : int
        符号付きの整数。

    Returns
    -------
    int
        非負で、入力かその符号を反転した値。
    """
    Ensures(ResultT(int) >= 0)
    Ensures(ResultT(int) == x or ResultT(int) == -x)
    if x < 0:
        return -x
    return x


def caller(x: int) -> None:
    """実装の中身ではなく、返り値の契約を利用する。

    Parameters
    ----------
    x : int
        符号付きの整数。
    """
    result = absolute(x)
    assert result >= 0
    assert result == x or result == -x
