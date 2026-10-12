"""list.append: 長さが1増え、既存の要素は保たれ、末尾が新しい値になる。"""

from nagini_contracts.contracts import (
    Acc,  # pyright: ignore[reportUnknownVariableType]
    Ensures,
    Forall,
    Implies,
    Old,
    Requires,
    ToSeq,
    list_pred,
)


def push(values: list[int], value: int) -> None:
    """末尾に value を足す。"""
    Requires(Acc(list_pred(values)))
    Ensures(Acc(list_pred(values)))
    Ensures(len(values) == Old(len(values)) + 1)
    Ensures(
        Forall(
            int,
            lambda i: Implies(0 <= i and i < Old(len(values)), values[i] == Old(ToSeq(values))[i]),
        )
    )
    Ensures(values[len(values) - 1] == value)
    values.append(value)


def wrong_push(values: list[int], value: int) -> None:
    """足す値を1つずらしてしまう。"""
    Requires(Acc(list_pred(values)))
    Ensures(Acc(list_pred(values)))
    Ensures(len(values) == Old(len(values)) + 1)
    Ensures(
        Forall(
            int,
            lambda i: Implies(0 <= i and i < Old(len(values)), values[i] == Old(ToSeq(values))[i]),
        )
    )
    Ensures(values[len(values) - 1] == value)
    values.append(value + 1)
