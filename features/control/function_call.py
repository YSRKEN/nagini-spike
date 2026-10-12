"""関数呼び出し: 呼び出し先の契約だけで、呼び出し側の性質が示せる。"""

from nagini_contracts.contracts import Ensures, Requires, Result


def clamp(x: int, low: int, high: int) -> int:
    """`x` を low 以上 high 以下に収める。"""
    Requires(low <= high)
    Ensures(low <= Result() and Result() <= high)
    if x < low:
        return low
    if x > high:
        return high
    return x


def percent(x: int) -> int:
    """`clamp` の契約だけを頼りに、0 以上 100 以下を保証する。"""
    Ensures(0 <= Result() and Result() <= 100)
    return clamp(x, 0, 100)


def wrong_percent(x: int) -> int:
    """引数の順を取り違え、上限と下限を逆に渡す。"""
    Ensures(0 <= Result() and Result() <= 100)
    return clamp(x, 100, 0)
