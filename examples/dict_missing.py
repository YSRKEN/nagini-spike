"""不在キーの結果契約から呼び出し側の辞書読取を証明する。"""

from typing import Optional

from nagini_contracts.contracts import (
    Acc,  # pyright: ignore[reportUnknownVariableType]
    Ensures,
    Forall,
    Implies,
    Old,
    Requires,
    Result,
    dict_pred,
)


def lookup(values: dict[int, int], key: int) -> Optional[int]:
    """任意整数キーが不在ならNone、存在ならその値を返す。

    Parameters
    ----------
    values : dict[int, int]
        全権限を持つ任意長の整数辞書。
    key : int
        探す任意整数キー。

    Returns
    -------
    Optional[int]
        不在ならNone、存在なら元の整数値。
    """
    Requires(Acc(dict_pred(values)))
    Ensures(Acc(dict_pred(values)))
    Ensures(len(values) == Old(len(values)))
    Ensures(
        Forall(
            int,
            lambda k: Implies(Old(k in values), k in values and values[k] == Old(values[k])),
        )
    )
    Ensures(Forall(int, lambda k: Implies(k in values, Old(k in values))))
    Ensures((Result() is None) == (key not in values))
    Ensures(Result() is None or Result() == values[key])
    if key not in values:
        return None
    return values[key]


def read_or_default(values: dict[int, int], key: int, default: int) -> int:
    """結果の不在契約から非None分岐の辞書読取を安全に行う。

    Parameters
    ----------
    values : dict[int, int]
        全権限を持つ任意長の整数辞書。
    key : int
        探す任意整数キー。
    default : int
        不在時に返す任意整数。

    Returns
    -------
    int
        不在ならdefault、存在なら辞書から読み直した整数値。
    """
    Requires(Acc(dict_pred(values)))
    Ensures(Acc(dict_pred(values)))
    Ensures(len(values) == Old(len(values)))
    Ensures(
        Forall(
            int,
            lambda k: Implies(Old(k in values), k in values and values[k] == Old(values[k])),
        )
    )
    Ensures(Forall(int, lambda k: Implies(k in values, Old(k in values))))
    Ensures(Implies(key not in values, Result() == default))
    Ensures(Implies(key in values, Result() == values[key]))
    found = lookup(values, key)
    if found is None:
        return default
    return values[key]
