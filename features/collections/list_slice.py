"""スライス: values[start:stop] の各要素が、もとの対応する要素と等しい。"""

# nagini_contracts の型注釈は Acc の割合を int と宣言しているが、
# Nagini は 1 / 2 のような分数を受け付ける。
# pyright: reportArgumentType=false

from nagini_contracts.contracts import (
    Acc,  # pyright: ignore[reportUnknownVariableType]
    Ensures,
    Forall,
    Implies,
    Requires,
    Result,
    list_pred,
)


def window(values: list[int], start: int, stop: int) -> list[int]:
    """`start` から stop の手前までを切り出す。"""
    Requires(Acc(list_pred(values), 1 / 2))
    Requires(0 <= start and start <= stop and stop <= len(values))
    Ensures(Acc(list_pred(values), 1 / 2))
    Ensures(stop <= len(values))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == stop - start)
    Ensures(
        Forall(
            int,
            lambda i: Implies(0 <= i and i < stop - start, Result()[i] == values[start + i]),
        )
    )
    return values[start:stop]


def wrong_window(values: list[int], start: int, stop: int) -> list[int]:
    """1つ後ろにずれた範囲を切り出してしまう。"""
    Requires(Acc(list_pred(values), 1 / 2))
    Requires(0 <= start and start <= stop and stop < len(values))
    Ensures(Acc(list_pred(values), 1 / 2))
    Ensures(stop <= len(values))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == stop - start)
    Ensures(
        Forall(
            int,
            lambda i: Implies(0 <= i and i < stop - start, Result()[i] == values[start + i]),
        )
    )
    return values[start + 1 : stop + 1]
