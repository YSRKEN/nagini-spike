"""for: リストの最大値が全要素以上で、どれかの要素と等しい。"""

# nagini_contracts の型注釈は Acc の割合を int と宣言しているが、
# Nagini は 1 / 2 のような分数を受け付ける。
# pyright: reportArgumentType=false

from nagini_contracts.contracts import (
    Acc,  # pyright: ignore[reportUnknownVariableType]
    Ensures,
    Forall,
    Invariant,
    Previous,
    Requires,
    Result,
    ToSeq,
    list_pred,
)


def maximum(values: list[int]) -> int:
    """全要素を走査して最大値を返す。"""
    Requires(Acc(list_pred(values), 1 / 2))
    Requires(len(values) > 0)
    Ensures(Acc(list_pred(values), 1 / 2))
    Ensures(Forall(ToSeq(values), lambda value: value <= Result()))
    Ensures(Result() in ToSeq(values))
    best = values[0]
    for value in values:
        Invariant(Forall(Previous(value), lambda seen: seen <= best))
        Invariant(best in ToSeq(values))
        if value > best:
            best = value
    return best


def wrong_maximum(values: list[int]) -> int:
    """比較の向きを逆にし、最小値を返してしまう。"""
    Requires(Acc(list_pred(values), 1 / 2))
    Requires(len(values) > 0)
    Ensures(Acc(list_pred(values), 1 / 2))
    Ensures(Forall(ToSeq(values), lambda value: value <= Result()))
    Ensures(Result() in ToSeq(values))
    best = values[0]
    for value in values:
        Invariant(best in ToSeq(values))
        if value < best:
            best = value
    return best
