"""空非空の結果契約から呼び出し側の先頭読取を証明する。"""

from nagini_contracts.contracts import (
    Acc,  # pyright: ignore[reportUnknownVariableType]
    Ensures,
    Implies,
    Old,
    Requires,
    Result,
    ToSeq,
    list_pred,
)


def has_head(values: list[int]) -> bool:
    """先頭要素が存在するかを返し、入力列を保存する。

    Parameters
    ----------
    values : list[int]
        全権限を持つ空を含む任意整数リスト。

    Returns
    -------
    bool
        非空ならTrue、空ならFalse。
    """
    Requires(Acc(list_pred(values)))
    Ensures(Acc(list_pred(values)))
    Ensures(len(values) == Old(len(values)))
    Ensures(ToSeq(values) == Old(ToSeq(values)))
    Ensures(Result() == (len(values) > 0))
    return len(values) > 0


def read_or_default(values: list[int], default: int) -> int:
    """結果の非空契約だけから分岐後の先頭を安全に読む。

    Parameters
    ----------
    values : list[int]
        全権限を持つ空を含む任意整数リスト。
    default : int
        空の場合に返す任意整数。

    Returns
    -------
    int
        非空なら入力の先頭、空ならdefault。
    """
    Requires(Acc(list_pred(values)))
    Ensures(Acc(list_pred(values)))
    Ensures(len(values) == Old(len(values)))
    Ensures(ToSeq(values) == Old(ToSeq(values)))
    Ensures(Implies(len(values) == 0, Result() == default))
    Ensures(Implies(len(values) > 0, Result() == values[0]))
    found = has_head(values)
    if found:
        return values[0]
    return default
