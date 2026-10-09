"""整数だけの小さな関数を、通常のassertで検証する。"""


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
    if x < 0:
        result = -x
    else:
        result = x
    assert result >= 0
    assert result == x or result == -x
    return result
