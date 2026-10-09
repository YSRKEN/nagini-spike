"""正の除数に限定して整数の商と余りの境界を検証する。"""

from nagini_contracts.contracts import Requires


def quotient_remainder(numerator: int, divisor: int) -> tuple[int, int]:
    """正の除数で割った商と余りを返す。

    Parameters
    ----------
    numerator : int
        割られる整数。負数も許す。
    divisor : int
        正の除数。

    Returns
    -------
    tuple[int, int]
        商と余り。元の整数を再構成でき、余りは0以上かつ除数未満。

    Raises
    ------
    AssertionError
        通常実行で除数が0以下の場合。
    """
    Requires(divisor > 0)
    assert divisor > 0
    quotient = numerator // divisor
    remainder = numerator % divisor
    assert numerator == quotient * divisor + remainder
    assert 0 <= remainder and remainder < divisor
    return quotient, remainder
