"""while: 0 から n-1 までの和が n(n-1)/2 になる。"""

from nagini_contracts.contracts import Ensures, Invariant, Requires, Result


def sum_below(n: int) -> int:
    """0 から n-1 までを1つずつ足す。"""
    Requires(n >= 0)
    Ensures(2 * Result() == n * (n - 1))
    total = 0
    i = 0
    while i < n:
        Invariant(0 <= i and i <= n)
        Invariant(2 * total == i * (i - 1))
        total += i
        i += 1
    return total


def wrong_sum_below(n: int) -> int:
    """終わりの条件を1つずらし、n まで足してしまう。"""
    Requires(n >= 0)
    Ensures(2 * Result() == n * (n - 1))
    total = 0
    i = 0
    while i <= n:
        Invariant(0 <= i and i <= n + 1)
        Invariant(2 * total == i * (i - 1))
        total += i
        i += 1
    return total
