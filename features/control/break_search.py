"""break: 線形探索が返す位置の要素は探す値で、それより前には無い。"""

# nagini_contracts の型注釈は Acc の割合を int と宣言しているが、
# Nagini は 1 / 2 のような分数を受け付ける。
# pyright: reportArgumentType=false

from nagini_contracts.contracts import (
    Acc,  # pyright: ignore[reportUnknownVariableType]
    Ensures,
    Forall,
    Implies,
    Invariant,
    Requires,
    ResultT,
    list_pred,
)


def find_first(values: list[int], target: int) -> int:
    """`target` が最初に現れる位置を返す。無ければ len(values) を返す。"""
    Requires(Acc(list_pred(values), 1 / 2))
    Ensures(Acc(list_pred(values), 1 / 2))
    Ensures(0 <= ResultT(int) and ResultT(int) <= len(values))
    Ensures(Implies(ResultT(int) < len(values), values[ResultT(int)] == target))
    Ensures(Forall(int, lambda j: Implies(0 <= j and j < ResultT(int), values[j] != target)))
    index = 0
    while index < len(values):
        Invariant(Acc(list_pred(values), 1 / 2))
        Invariant(0 <= index and index <= len(values))
        Invariant(Forall(int, lambda j: Implies(0 <= j and j < index, values[j] != target)))
        if values[index] == target:
            break
        index += 1
    return index


def wrong_find_first(values: list[int], target: int) -> int:
    """見つけても止まらず、最後に見つけた位置を返してしまう。"""
    Requires(Acc(list_pred(values), 1 / 2))
    Ensures(Acc(list_pred(values), 1 / 2))
    Ensures(0 <= ResultT(int) and ResultT(int) <= len(values))
    Ensures(Implies(ResultT(int) < len(values), values[ResultT(int)] == target))
    Ensures(Forall(int, lambda j: Implies(0 <= j and j < ResultT(int), values[j] != target)))
    found = len(values)
    index = 0
    while index < len(values):
        Invariant(Acc(list_pred(values), 1 / 2))
        Invariant(0 <= index and index <= len(values))
        Invariant(0 <= found and found <= len(values))
        Invariant(Implies(found < len(values), values[found] == target))
        if values[index] == target:
            found = index
        index += 1
    return found
