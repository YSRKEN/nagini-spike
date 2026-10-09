"""キーの有無を分けて、整数の辞書から値を読み取る。"""

from nagini_contracts.contracts import (
    Acc,  # pyright: ignore[reportUnknownVariableType]
    Requires,
    dict_pred,
)


def lookup_or_zero(values: dict[int, int], key: int) -> int:
    """キーがあれば対応する値、なければ0を返す。

    Parameters
    ----------
    values : dict[int, int]
        読み取る整数キーと整数値の辞書。
    key : int
        調べるキー。

    Returns
    -------
    int
        対応する値、またはキーが存在しない場合の0。
    """
    Requires(Acc(dict_pred(values), 1 / 2))  # pyright: ignore[reportArgumentType]
    if key in values:
        result = values[key]
    else:
        result = 0
    assert key in values or result == 0
    assert key not in values or result == values[key]
    return result
