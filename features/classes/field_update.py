"""フィールド: カウンタの increment で値がちょうど1増える。"""

from nagini_contracts.contracts import (
    Acc,  # pyright: ignore[reportUnknownVariableType]
    Ensures,
    Old,
    Requires,
)


class Counter:
    """1つずつ数えるカウンタ。"""

    def __init__(self, initial: int) -> None:
        """初期値 `initial` から数え始める。"""
        self.value: int = initial
        Ensures(Acc(self.value))
        Ensures(self.value == initial)

    def increment(self) -> None:
        """値を1増やす。"""
        Requires(Acc(self.value))
        Ensures(Acc(self.value))
        Ensures(self.value == Old(self.value) + 1)
        self.value += 1


class WrongCounter:
    """増やす幅を間違えたカウンタ。"""

    def __init__(self, initial: int) -> None:
        """初期値 `initial` から数え始める。"""
        self.value: int = initial
        Ensures(Acc(self.value))
        Ensures(self.value == initial)

    def increment(self) -> None:
        """値を2増やしてしまう。"""
        Requires(Acc(self.value))
        Ensures(Acc(self.value))
        Ensures(self.value == Old(self.value) + 1)
        self.value += 2
