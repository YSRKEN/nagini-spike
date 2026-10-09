"""非負整数のリストを読み取り、和の非負性を検証する。"""

from nagini_contracts.contracts import (
    Acc,  # pyright: ignore[reportUnknownVariableType]
    Forall,
    Invariant,
    Requires,
    list_pred,
)


def sum_nonnegative(values: list[int]) -> int:
    """非負整数のリストの合計を返す。

    Parameters
    ----------
    values : list[int]
        各要素が0以上の整数リスト。

    Returns
    -------
    int
        リストの合計。静的仕様では非負性を保証する。

    Raises
    ------
    AssertionError
        通常実行で負の要素を読んだ場合。
    """
    Requires(Acc(list_pred(values), 1 / 2))  # pyright: ignore[reportArgumentType]
    Requires(Forall(values, lambda value: value >= 0))
    total = 0
    i = 0
    while i < len(values):
        Invariant(Acc(list_pred(values), 1 / 2))  # pyright: ignore[reportArgumentType]
        Invariant(Forall(values, lambda value: value >= 0))
        Invariant(0 <= i and i <= len(values))
        Invariant(total >= 0)
        assert values[i] >= 0
        total += values[i]
        i += 1
    assert total >= 0
    return total
