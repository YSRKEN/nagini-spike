"""str の添字: 文字列の先頭の文字を取り出す。"""

from nagini_contracts.contracts import Requires


def head(text: str) -> str:
    """`text` の先頭の1文字を返す。"""
    Requires(len(text) > 0)
    return text[0]
