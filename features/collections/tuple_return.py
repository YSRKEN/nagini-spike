"""tuple: 商と余りの組を返し、商 × 除数 + 余り = 被除数 と 0 ≤ 余り < 除数 を満たす。"""

from nagini_contracts.contracts import Ensures, Requires, Result


def divide(numerator: int, divisor: int) -> tuple[int, int]:
    """商と余りを組にして返す。"""
    Requires(divisor > 0)
    Ensures(Result()[0] * divisor + Result()[1] == numerator)
    Ensures(0 <= Result()[1] and Result()[1] < divisor)
    return (numerator // divisor, numerator % divisor)


def wrong_divide(numerator: int, divisor: int) -> tuple[int, int]:
    """商と余りの順を取り違えて返す。"""
    Requires(divisor > 0)
    Ensures(Result()[0] * divisor + Result()[1] == numerator)
    Ensures(0 <= Result()[1] and Result()[1] < divisor)
    return (numerator % divisor, numerator // divisor)
