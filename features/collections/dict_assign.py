"""dict の代入: 代入したキー以外の値は保たれる。"""

from nagini_contracts.contracts import (
    Acc,  # pyright: ignore[reportUnknownVariableType]
    Ensures,
    Forall,
    Implies,
    Old,
    Requires,
    dict_pred,
)


def put(values: dict[int, int], key: int, value: int) -> None:
    """values[key] に value を入れる。"""
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
    values[key] = value


def wrong_put(values: dict[int, int], key: int, value: int) -> None:
    """先に別のキーを入れてから、そのキーを上書きしてしまう。"""
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
    values[key + 1] = value
    values[key] = value
