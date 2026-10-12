"""高階関数: 引数で受け取った関数を呼ぶ。"""

from typing import Callable


def apply(function: Callable[[int], int], x: int) -> int:
    """受け取った `function` に `x` を渡した結果を返す。"""
    return function(x)
