"""整数リストの任意有効添字だけを更新する一般契約。"""

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


def update_preserving(values: list[int], index: int, value: int) -> None:
    """指定位置だけを更新し、長さと全他要素を保つ。

    Parameters
    ----------
    values : list[int]
        全書き込み権限を持つ任意長整数リスト。
    index : int
        0以上、長さ未満の更新位置。
    value : int
        設定する任意整数値。
    """
    Requires(Acc(list_pred(values)))
    Requires(0 <= index and index < len(values))
    Ensures(Acc(list_pred(values)))
    Ensures(len(values) == Old(len(values)))
    Ensures(values[index] == value)
    Ensures(
        Forall(
            int,
            lambda other: Implies(
                0 <= other and other < Old(len(values)) and other != index,
                values[other] == Old(ToSeq(values))[other],
            ),
        )
    )
    pass
