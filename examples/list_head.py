"""空の場合を分けて、整数リストの先頭だけを読み取る。"""

from nagini_contracts.contracts import (
    Acc,  # pyright: ignore[reportUnknownVariableType]
    Requires,
    list_pred,
)


def first_or_zero(values: list[int]) -> int:
    """空リストなら0、要素があれば先頭の値を返す。

    Parameters
    ----------
    values : list[int]
        読み取る整数のリスト。

    Returns
    -------
    int
        空なら0、それ以外なら先頭の値。
    """
    # 配布物のAccは引数の型注釈がなく、Pyrightがratioをintと推論する。
    Requires(Acc(list_pred(values), 1 / 2))  # pyright: ignore[reportArgumentType]
    if len(values) == 0:
        result = 0
    else:
        result = values[0]
    assert len(values) != 0 or result == 0
    assert len(values) == 0 or result == values[0]
    return result
