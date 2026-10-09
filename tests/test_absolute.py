"""絶対値の実行結果を独立した組み込み関数と照合する。"""

import pytest

from examples.absolute import absolute


@pytest.mark.parametrize("value", [-10**100, -17, -1, 0, 1, 17, 10**100])
def test_absolute_matches_builtin(value: int) -> None:
    """負数・ゼロ・正数・大きな整数で期待する結果になる。"""
    assert absolute(value) == abs(value)
