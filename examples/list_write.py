"""空の場合を分けて、整数リストの先頭だけを書き換える。"""

from nagini_contracts.contracts import (
    Acc,  # pyright: ignore[reportUnknownVariableType]
    Requires,
    list_pred,
)


def replace_first(values: list[int], value: int) -> None:
    """要素があれば先頭を書き換え、空なら何もしない。

    Parameters
    ----------
    values : list[int]
        書き換える整数のリスト。
    value : int
        先頭に設定する値。
    """
    Requires(Acc(list_pred(values)))
    length = len(values)
    if len(values) > 0:
        values[0] = value
    assert len(values) == length
    assert len(values) == 0 or values[0] == value
