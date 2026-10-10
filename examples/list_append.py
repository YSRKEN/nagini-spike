"""整数リストの末尾追加で旧全要素を保存する契約。"""

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


def append_preserving(values: list[int], value: int) -> None:
    """旧全要素を保ち、末尾へ値を一つだけ追加する。

    Parameters
    ----------
    values : list[int]
        全書き込み権限を持つ整数リスト。長さと要素値に制限はない。
    value : int
        新しい末尾に設定する整数。
    """
    Requires(Acc(list_pred(values)))
    Ensures(Acc(list_pred(values)))
    Ensures(len(values) == Old(len(values)) + 1)
    Ensures(Forall(int, lambda i: Implies(0 <= i and i < Old(len(values)), values[i] == Old(ToSeq(values))[i])))
    Ensures(values[len(values) - 1] == value)
    pass
