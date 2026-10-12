"""list の添字代入: 指定した位置だけが変わり、他の要素は保たれる。"""

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


def set_at(values: list[int], index: int, value: int) -> None:
    """values[index] を value に置き換える。"""
    Requires(Acc(list_pred(values)))
    Requires(0 <= index and index < len(values))
    Ensures(Acc(list_pred(values)))
    Ensures(len(values) == Old(len(values)))
    Ensures(values[index] == value)
    Ensures(
        Forall(
            int,
            lambda i: Implies(
                0 <= i and i < len(values) and i != index, values[i] == Old(ToSeq(values))[i]
            ),
        )
    )
    values[index] = value


def wrong_set_at(values: list[int], index: int, value: int) -> None:
    """先頭も一緒に書き換えてしまう。"""
    Requires(Acc(list_pred(values)))
    Requires(0 <= index and index < len(values))
    Ensures(Acc(list_pred(values)))
    Ensures(len(values) == Old(len(values)))
    Ensures(values[index] == value)
    Ensures(
        Forall(
            int,
            lambda i: Implies(
                0 <= i and i < len(values) and i != index, values[i] == Old(ToSeq(values))[i]
            ),
        )
    )
    values[0] = value
    values[index] = value
