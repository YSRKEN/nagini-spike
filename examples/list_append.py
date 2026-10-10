"""整数リストの末尾追加で旧全要素を保存する契約。"""

from nagini_contracts.contracts import (
    Acc,  # pyright: ignore[reportUnknownVariableType]
    Assert,
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
    Ensures(
        Forall(
            int,
            lambda i: Implies(0 <= i and i < Old(len(values)), values[i] == Old(ToSeq(values))[i]),
        )
    )
    Ensures(values[len(values) - 1] == value)
    values.append(value)


def use_append_contract(values: list[int], value: int) -> None:
    """返された契約で全内容を確認してから、権限を使い末尾を更新する。

    Parameters
    ----------
    values : list[int]
        全書き込み権限を持つ任意長の整数リスト。
    value : int
        追加する値。検証後は末尾をその値より1大きくする。
    """
    Requires(Acc(list_pred(values)))
    length = len(values)
    before = ToSeq(values)
    append_preserving(values, value)
    assert len(values) == length + 1
    assert values[len(values) - 1] == value
    Assert(Forall(int, lambda i: Implies(0 <= i and i < length, values[i] == before[i])))
    values[len(values) - 1] = value + 1
