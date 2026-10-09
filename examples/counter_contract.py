"""整数の属性を持つクラスの初期化と更新を契約で検証する。"""

from nagini_contracts.contracts import (
    Acc,  # pyright: ignore[reportUnknownVariableType]
    Ensures,
    Old,
    Requires,
)


class Counter:
    """値を保持し、1ずつ増やすカウンター。"""

    def __init__(self, initial: int) -> None:
        """初期値と属性を読み書きする権限を保証する。

        Parameters
        ----------
        initial : int
            最初に保持する整数。
        """
        self.value: int = initial
        Ensures(Acc(self.value))
        Ensures(self.value == initial)

    def increment(self) -> None:
        """値を1増やし、属性の権限を呼び出し側へ返す。"""
        Requires(Acc(self.value))
        Ensures(Acc(self.value))
        Ensures(self.value == Old(self.value) + 1)
        self.value += 1


def caller(initial: int) -> None:
    """初期化と二回の更新の保証を契約から利用する。

    Parameters
    ----------
    initial : int
        最初に保持する整数。
    """
    counter = Counter(initial)
    assert counter.value == initial
    counter.increment()
    assert counter.value == initial + 1
    counter.increment()
    assert counter.value == initial + 2
