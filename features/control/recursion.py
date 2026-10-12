"""再帰: 再帰で定義した階乗と、実装の返り値が一致する。"""

from nagini_contracts.contracts import Decreases, Ensures, Pure, Requires, Result


@Pure
def fac(n: int) -> int:
    """階乗の定義。実装とは別に書く。"""
    Requires(n >= 0)
    Decreases(n)
    return 1 if n == 0 else n * fac(n - 1)


def factorial(n: int) -> int:
    """再帰呼び出しで階乗を計算する。"""
    Requires(n >= 0)
    Ensures(Result() == fac(n))
    if n == 0:
        return 1
    return n * factorial(n - 1)


def wrong_factorial(n: int) -> int:
    """再帰の足し場を間違え、n * (n-1)! ではなく n + (n-1)! を返す。"""
    Requires(n >= 0)
    Ensures(Result() == fac(n))
    if n == 0:
        return 1
    return n + wrong_factorial(n - 1)
