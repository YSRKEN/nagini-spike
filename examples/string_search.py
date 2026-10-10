"""任意文字列の部分文字列存在を組込み演算に対する契約で指定する。"""

from nagini_contracts.contracts import Ensures, Result


def contains_substring(text: str, needle: str) -> bool:
    """文字列に探索対象が含まれるかを返す。

    Parameters
    ----------
    text : str
        探索先。空文字も許す。
    needle : str
        探索対象。空文字も許す。

    Returns
    -------
    bool
        組込み部分文字列演算と一致する真偽値。
    """
    Ensures(Result() == (needle in text))
    return needle in text
