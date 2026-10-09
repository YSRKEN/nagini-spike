"""非負の範囲を足す最小のwhileループを検証する。"""

from nagini_contracts.contracts import Invariant, Requires


def sum_range(n: int) -> int:
    """0からn未満までの整数の和を返す。

    Parameters
    ----------
    n : int
        範囲の上限。0以上。

    Returns
    -------
    int
        0からn未満までの整数の和。

    Raises
    ------
    AssertionError
        通常のPython実行でnが負の場合。
    """
    Requires(n >= 0)
    assert n >= 0
    total = 0
    i = 0
    while i < n:
        Invariant(0 <= i and i <= n)
        Invariant(2 * total == i * (i - 1))
        total += i
        i += 1
    assert 2 * total == n * (n - 1)
    return total
