"""set.add: 追加した値が in で真になり、もとの要素も残る。"""

from nagini_contracts.contracts import (
    Acc,  # pyright: ignore[reportUnknownVariableType]
    Ensures,
    Forall,
    Implies,
    Old,
    Requires,
    set_pred,
)


def remember(seen: set[int], value: int) -> None:
    """`value` を集合に加える。"""
    Requires(Acc(set_pred(seen)))
    Ensures(Acc(set_pred(seen)))
    Ensures(value in seen)
    Ensures(Forall(int, lambda other: Implies(Old(other in seen), other in seen)))
    seen.add(value)


def wrong_remember(seen: set[int], value: int) -> None:
    """加えたあとで取り除いてしまう。"""
    Requires(Acc(set_pred(seen)))
    Ensures(Acc(set_pred(seen)))
    Ensures(value in seen)
    Ensures(Forall(int, lambda other: Implies(Old(other in seen), other in seen)))
    seen.add(value)
    seen.remove(value)
