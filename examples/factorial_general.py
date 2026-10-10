"""独立した再帰階乗モデルと、同じ一般契約の正実装を示す。"""

from nagini_contracts.contracts import Ensures, Pure, Requires, Result


@Pure
def fac(n: int) -> int:
    """非負整数の階乗を実装から独立して再帰定義する。"""
    Requires(n >= 0)
    return 1 if n == 0 else n * fac(n - 1)


def factorial(n: int) -> int:
    """非負整数の階乗を一般モデルとの一致契約で計算する。"""
    Requires(n >= 0)
    Ensures(Result() == fac(n))
    if n == 0:
        return 1
    return n * factorial(n - 1)
