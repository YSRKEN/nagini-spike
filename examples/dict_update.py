"""整数辞書の一キー更新に一般的な保存契約を指定する。"""

from nagini_contracts.contracts import (
    Acc,  # pyright: ignore[reportUnknownVariableType]
    Ensures,
    Forall,
    Implies,
    Old,
    Requires,
    dict_pred,
)


def update_preserving(values: dict[int, int], key: int, value: int) -> None:
    """指定キーの値だけを更新し、旧他キーと長さの関係を保つ。

    Parameters
    ----------
    values : dict[int, int]
        全書き込み権限を持つ任意長の整数辞書。
    key : int
        更新する任意整数キー。
    value : int
        設定する任意整数値。
    """
    Requires(Acc(dict_pred(values)))
    Ensures(Acc(dict_pred(values)))
    Ensures(key in values and values[key] == value)
    Ensures(
        Forall(
            int,
            lambda other: Implies(
                Old(other in values) and other != key,
                other in values and values[other] == Old(values[other]),
            ),
        )
    )
    Ensures(
        Forall(int, lambda other: Implies(other in values, Old(other in values) or other == key))
    )
    Ensures(len(values) == Old(len(values)) + (0 if Old(key in values) else 1))
    values[key] = value
