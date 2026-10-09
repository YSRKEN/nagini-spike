"""リストへの書き込みの保証と権限を呼び出し側へ返す。"""

from nagini_contracts.contracts import (
    Acc,  # pyright: ignore[reportUnknownVariableType]
    Ensures,
    Old,
    Requires,
    list_pred,
)


def replace_head(values: list[int], value: int) -> None:
    """非空のリストの先頭を指定値に置き換える。

    Parameters
    ----------
    values : list[int]
        書き込み可能で非空の整数リスト。
    value : int
        新しい先頭の値。
    """
    Requires(Acc(list_pred(values)))
    Requires(len(values) > 0)
    Ensures(Acc(list_pred(values)))
    Ensures(len(values) == Old(len(values)))
    Ensures(values[0] == value)
    values[0] = value


def caller(values: list[int], value: int) -> None:
    """契約の保証を使い、呼び出し後にもリストを書き換える。

    Parameters
    ----------
    values : list[int]
        書き込み可能で非空の整数リスト。
    value : int
        最初に設定する値。
    """
    Requires(Acc(list_pred(values)))
    Requires(len(values) > 0)
    length = len(values)
    replace_head(values, value)
    assert len(values) == length
    assert values[0] == value
    values[0] = value + 1
    assert values[0] == value + 1
