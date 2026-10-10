"""任意二文字列の連結内容と長さを独立した一般契約で指定する。"""

from nagini_contracts.contracts import Ensures, Result


def concatenate(a: str, b: str) -> str:
    """二文字列を順に連結する。

    Parameters
    ----------
    a : str
        先頭の文字列。
    b : str
        後続の文字列。

    Returns
    -------
    str
        連結内容と長さを満たす文字列。
    """
    Ensures(len(Result()) == len(a) + len(b))
    Ensures(Result() == a + b)
    return a + b
