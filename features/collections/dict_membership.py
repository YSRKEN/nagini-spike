"""dict の in: キーの有無を確かめてからなら、安全に読める。"""

# nagini_contracts の型注釈は Acc の割合を int と宣言しているが、
# Nagini は 1 / 2 のような分数を受け付ける。
# pyright: reportArgumentType=false

from nagini_contracts.contracts import (
    Acc,  # pyright: ignore[reportUnknownVariableType]
    Ensures,
    Implies,
    Requires,
    Result,
    dict_pred,
)


def get_or_default(values: dict[int, int], key: int, default: int) -> int:
    """`key` があればその値を、無ければ default を返す。読むだけなので権限は半分でよい。"""
    Requires(Acc(dict_pred(values), 1 / 2))
    Ensures(Acc(dict_pred(values), 1 / 2))
    Ensures(Implies(key in values, Result() == values[key]))
    Ensures(Implies(key not in values, Result() == default))
    if key in values:
        return values[key]
    return default


def wrong_get_or_default(values: dict[int, int], key: int, default: int) -> int:
    """有無を確かめずに読んでしまう。"""
    Requires(Acc(dict_pred(values), 1 / 2))
    Ensures(Acc(dict_pred(values), 1 / 2))
    Ensures(Implies(key in values, Result() == values[key]))
    Ensures(Implies(key not in values, Result() == default))
    return values[key]
