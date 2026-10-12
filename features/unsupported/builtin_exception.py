"""組み込みの例外: `Exsures` に `ValueError` を書く。

独自の例外クラスなら書ける（`features/exceptions/raise_error.py`）。
"""

from nagini_contracts.contracts import Ensures, Exsures, Result


def check_age(age: int) -> int:
    """負の年齢なら ValueError を投げ、それ以外はそのまま返す。"""
    Ensures(Result() == age and age >= 0)
    Exsures(ValueError, age < 0)
    if age < 0:
        raise ValueError("age must be nonnegative")
    return age
